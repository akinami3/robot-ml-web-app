package server

import (
	"context"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
	"github.com/robot-ai-webapp/gateway/internal/safety"
	"go.uber.org/zap"
)

// Handler processes incoming WebSocket messages
type Handler struct {
	hub             *Hub
	registry        *adapter.Registry
	estop           *safety.EStopManager
	velocityLimiter *safety.VelocityLimiter
	watchdog        *safety.TimeoutWatchdog
	opLock          *safety.OperationLock
	codec           *protocol.Codec
	logger          *zap.Logger
	redisPublisher  RedisPublisher
}

// RedisPublisher interface for publishing sensor data to Redis
type RedisPublisher interface {
	PublishSensorData(ctx context.Context, robotID string, data adapter.SensorData) error
	PublishCommand(ctx context.Context, robotID string, cmd adapter.Command) error
}

// NewHandler creates a new message handler
func NewHandler(
	hub *Hub,
	registry *adapter.Registry,
	estop *safety.EStopManager,
	limiter *safety.VelocityLimiter,
	watchdog *safety.TimeoutWatchdog,
	opLock *safety.OperationLock,
	publisher RedisPublisher,
	logger *zap.Logger,
) *Handler {
	return &Handler{
		hub:             hub,
		registry:        registry,
		estop:           estop,
		velocityLimiter: limiter,
		watchdog:        watchdog,
		opLock:          opLock,
		codec:           protocol.NewCodec(),
		logger:          logger,
		redisPublisher:  publisher,
	}
}

// HandleMessage routes a decoded message to the appropriate handler
func (h *Handler) HandleMessage(ctx context.Context, client *Client, msg *protocol.Message) {
	switch msg.Type {
	case protocol.MsgTypeAuth:
		h.handleAuth(ctx, client, msg)
	case protocol.MsgTypePing:
		h.handlePing(client, msg)
	case protocol.MsgTypeVelocityCommand:
		h.handleVelocityCommand(ctx, client, msg)
	case protocol.MsgTypeEmergencyStop:
		h.handleEStop(ctx, client, msg)
	case protocol.MsgTypeNavigationGoal:
		h.handleNavigationGoal(ctx, client, msg)
	case protocol.MsgTypeNavigationCancel:
		h.handleNavigationCancel(ctx, client, msg)
	case protocol.MsgTypeOperationLock:
		h.handleOperationLock(ctx, client, msg)
	case protocol.MsgTypeOperationUnlock:
		h.handleOperationUnlock(ctx, client, msg)
	default:
		h.sendError(client, "unknown message type: "+string(msg.Type))
	}
}

func (h *Handler) handleAuth(ctx context.Context, client *Client, msg *protocol.Message) {
	// For now, accept any token and mark as authenticated
	// In production, verify JWT token
	token, _ := msg.Payload["token"].(string)
	if token == "" {
		h.sendError(client, "token required")
		return
	}

	// TODO: Verify JWT token and extract user ID
	client.Authenticated = true
	client.UserID = "user-from-token" // Extract from JWT

	// Auto-subscribe to mock robot for development
	client.mu.Lock()
	client.Subscriptions["mock-robot-1"] = true
	client.mu.Unlock()

	ack := protocol.NewMessage(protocol.MsgTypeConnectionStatus, "")
	ack.Payload = map[string]any{
		"authenticated": true,
		"client_id":     client.ID,
		"user_id":       client.UserID,
	}
	h.sendMessage(client, ack)
}

func (h *Handler) handlePing(client *Client, msg *protocol.Message) {
	pong := protocol.NewMessage(protocol.MsgTypePong, "")
	h.sendMessage(client, pong)
}

func (h *Handler) handleVelocityCommand(ctx context.Context, client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, "not authenticated")
		return
	}

	robotID := msg.RobotID
	if robotID == "" {
		h.sendError(client, "robot_id required")
		return
	}

	// Check E-Stop
	if h.estop.IsActive(robotID) {
		h.sendError(client, "E-Stop is active for robot "+robotID)
		return
	}

	// Check operation lock
	if !h.opLock.CheckLock(robotID, client.UserID) {
		h.sendError(client, "operation lock not held")
		return
	}

	// Extract velocity
	lx, _ := toFloat(msg.Payload["linear_x"])
	ly, _ := toFloat(msg.Payload["linear_y"])
	az, _ := toFloat(msg.Payload["angular_z"])

	// Apply velocity limits
	result := h.velocityLimiter.Limit(safety.VelocityInput{
		LinearX:  lx,
		LinearY:  ly,
		AngularZ: az,
	})

	// Send clamping alert if velocity was limited
	if result.Clamped {
		alert := protocol.NewMessage(protocol.MsgTypeSafetyAlert, robotID)
		alert.Payload = map[string]any{
			"type":    "velocity_clamped",
			"message": "Velocity was clamped to safety limits",
		}
		h.sendMessage(client, alert)
	}

	// Build command
	cmd := adapter.Command{
		RobotID: robotID,
		Type:    "velocity",
		Payload: map[string]any{
			"linear_x":  result.LinearX,
			"linear_y":  result.LinearY,
			"angular_z": result.AngularZ,
		},
		Timestamp: msg.Timestamp,
	}

	// Send to robot adapter
	if adp, ok := h.registry.GetAdapter(robotID); ok {
		if err := adp.SendCommand(ctx, cmd); err != nil {
			h.sendError(client, "failed to send command: "+err.Error())
			return
		}
	}

	// Record command for timeout watchdog
	h.watchdog.RecordCommand(robotID)

	// Publish to Redis for backend recording
	if h.redisPublisher != nil {
		_ = h.redisPublisher.PublishCommand(ctx, robotID, cmd)
	}

	// Send ack
	ack := protocol.NewMessage(protocol.MsgTypeCommandAck, robotID)
	ack.Payload = map[string]any{"success": true}
	h.sendMessage(client, ack)
}

func (h *Handler) handleEStop(ctx context.Context, client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, "not authenticated")
		return
	}

	activate, _ := msg.Payload["activate"].(bool)
	reason, _ := msg.Payload["reason"].(string)
	robotID := msg.RobotID

	if activate {
		if robotID != "" {
			// E-Stop specific robot
			if err := h.estop.Activate(ctx, robotID, client.UserID, reason); err != nil {
				h.sendError(client, "E-Stop failed: "+err.Error())
				return
			}
		} else {
			// E-Stop ALL robots
			h.estop.ActivateAll(ctx, client.UserID, reason)
		}
	} else {
		if robotID != "" {
			h.estop.Release(robotID, client.UserID)
		}
	}

	// Broadcast E-Stop status to all clients
	alert := protocol.NewMessage(protocol.MsgTypeSafetyAlert, robotID)
	alert.Payload = map[string]any{
		"type":     "estop",
		"activate": activate,
		"reason":   reason,
		"user_id":  client.UserID,
	}
	data, _ := h.codec.Encode(alert)
	h.hub.BroadcastToAll(data)
}

func (h *Handler) handleNavigationGoal(ctx context.Context, client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, "not authenticated")
		return
	}

	robotID := msg.RobotID
	if !h.opLock.CheckLock(robotID, client.UserID) {
		h.sendError(client, "operation lock not held")
		return
	}

	if h.estop.IsActive(robotID) {
		h.sendError(client, "E-Stop is active")
		return
	}

	cmd := adapter.Command{
		RobotID:   robotID,
		Type:      "navigation_goal",
		Payload:   msg.Payload,
		Timestamp: msg.Timestamp,
	}

	if adp, ok := h.registry.GetAdapter(robotID); ok {
		if err := adp.SendCommand(ctx, cmd); err != nil {
			h.sendError(client, "failed to send navigation goal: "+err.Error())
			return
		}
	}

	if h.redisPublisher != nil {
		_ = h.redisPublisher.PublishCommand(ctx, robotID, cmd)
	}

	ack := protocol.NewMessage(protocol.MsgTypeCommandAck, robotID)
	ack.Payload = map[string]any{"success": true, "command": "navigation_goal"}
	h.sendMessage(client, ack)
}

func (h *Handler) handleNavigationCancel(ctx context.Context, client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, "not authenticated")
		return
	}

	robotID := msg.RobotID

	cmd := adapter.Command{
		RobotID: robotID,
		Type:    "navigation_cancel",
		Payload: msg.Payload,
	}

	if adp, ok := h.registry.GetAdapter(robotID); ok {
		_ = adp.SendCommand(ctx, cmd)
	}

	ack := protocol.NewMessage(protocol.MsgTypeCommandAck, robotID)
	ack.Payload = map[string]any{"success": true, "command": "navigation_cancel"}
	h.sendMessage(client, ack)
}

func (h *Handler) handleOperationLock(ctx context.Context, client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, "not authenticated")
		return
	}

	robotID := msg.RobotID
	lockInfo, err := h.opLock.Acquire(robotID, client.UserID)

	resp := protocol.NewMessage(protocol.MsgTypeLockStatus, robotID)
	if err != nil {
		resp.Payload = map[string]any{
			"granted":    false,
			"locked_by":  lockInfo.UserID,
			"expires_at": lockInfo.ExpiresAt.UnixMilli(),
			"message":    err.Error(),
		}
	} else {
		resp.Payload = map[string]any{
			"granted":    true,
			"locked_by":  client.UserID,
			"expires_at": lockInfo.ExpiresAt.UnixMilli(),
		}
	}
	h.sendMessage(client, resp)

	// Broadcast lock status change
	broadcast := protocol.NewMessage(protocol.MsgTypeLockStatus, robotID)
	broadcast.Payload = map[string]any{
		"locked_by":  lockInfo.UserID,
		"expires_at": lockInfo.ExpiresAt.UnixMilli(),
	}
	data, _ := h.codec.Encode(broadcast)
	h.hub.BroadcastToRobot(robotID, data)
}

func (h *Handler) handleOperationUnlock(ctx context.Context, client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, "not authenticated")
		return
	}

	robotID := msg.RobotID
	err := h.opLock.Release(robotID, client.UserID)

	resp := protocol.NewMessage(protocol.MsgTypeLockStatus, robotID)
	if err != nil {
		resp.Error = err.Error()
	} else {
		resp.Payload = map[string]any{
			"locked_by":  "",
			"released":   true,
		}
	}
	h.sendMessage(client, resp)

	// Broadcast lock released
	data, _ := h.codec.Encode(resp)
	h.hub.BroadcastToRobot(robotID, data)
}

func (h *Handler) sendMessage(client *Client, msg *protocol.Message) {
	data, err := h.codec.Encode(msg)
	if err != nil {
		h.logger.Error("Failed to encode message", zap.Error(err))
		return
	}
	select {
	case client.Send <- data:
	default:
		h.logger.Warn("Client send buffer full", zap.String("client_id", client.ID))
	}
}

func (h *Handler) sendError(client *Client, errMsg string) {
	msg := protocol.NewMessage(protocol.MsgTypeError, "")
	msg.Error = errMsg
	h.sendMessage(client, msg)
}

func toFloat(v any) (float64, bool) {
	switch val := v.(type) {
	case float64:
		return val, true
	case float32:
		return float64(val), true
	case int:
		return float64(val), true
	case int64:
		return float64(val), true
	case int8:
		return float64(val), true
	default:
		return 0, false
	}
}
