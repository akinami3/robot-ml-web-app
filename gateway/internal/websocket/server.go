package websocket

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/amr-saas/gateway/internal/robot"
	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

const (
	writeWait      = 10 * time.Second
	pongWait       = 60 * time.Second
	pingPeriod     = (pongWait * 9) / 10
	maxMessageSize = 512 * 1024
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Configure appropriately for production
	},
}

// MessageType represents the type of WebSocket message
type MessageType string

const (
	// Client -> Gateway
	MsgSubscribe       MessageType = "subscribe"
	MsgUnsubscribe     MessageType = "unsubscribe"
	MsgCommand         MessageType = "command"
	MsgSetRecording    MessageType = "set_recording"

	// Gateway -> Client
	MsgRobotStatus     MessageType = "robot_status"
	MsgCommandResponse MessageType = "command_response"
	MsgError           MessageType = "error"
	MsgRecordingStatus MessageType = "recording_status"
)

// Message represents a WebSocket message
type Message struct {
	Type      MessageType            `json:"type"`
	RobotID   string                 `json:"robot_id,omitempty"`
	RobotIDs  []string               `json:"robot_ids,omitempty"`
	Command   string                 `json:"command,omitempty"`
	Params    map[string]interface{} `json:"params,omitempty"`
	Data      interface{}            `json:"data,omitempty"`
	Success   bool                   `json:"success,omitempty"`
	Error     string                 `json:"error,omitempty"`
	Timestamp int64                  `json:"timestamp"`
	Recording bool                   `json:"recording,omitempty"`
}

// RobotStatusData represents robot status sent to clients
type RobotStatusData struct {
	ID               string             `json:"id"`
	Name             string             `json:"name"`
	Vendor           string             `json:"vendor"`
	Model            string             `json:"model"`
	State            string             `json:"state"`
	Battery          float64            `json:"battery"`
	Position         robot.Position     `json:"position"`
	IsOnline         bool               `json:"is_online"`
	LastSeen         int64              `json:"last_seen"`
	CurrentMissionID string             `json:"current_mission_id,omitempty"`
	SensorData       map[string]float64 `json:"sensor_data,omitempty"`
	ControlData      map[string]float64 `json:"control_data,omitempty"`
}

// Client represents a connected WebSocket client
type Client struct {
	conn            *websocket.Conn
	server          *Server
	send            chan []byte
	userID          string
	subscribedBots  map[string]bool
	mu              sync.RWMutex
	recordingBots   map[string]bool // robots with recording enabled
}

// Server manages WebSocket connections
type Server struct {
	manager         *robot.Manager
	clients         map[*Client]bool
	register        chan *Client
	unregister      chan *Client
	broadcast       chan []byte
	logger          *zap.SugaredLogger
	mu              sync.RWMutex
	jwtSecret       []byte
	backendForwarder BackendForwarder
}

// BackendForwarder interface for forwarding data to backend
type BackendForwarder interface {
	ForwardSensorData(robotID string, sensorData, controlData map[string]float64) error
	ForwardCommandData(robotID, userID, command string, params map[string]float64, success bool, errorMsg string, robotStateBefore map[string]float64) error
}

// NewServer creates a new WebSocket server
func NewServer(manager *robot.Manager, logger *zap.SugaredLogger, jwtSecret string) *Server {
	return &Server{
		manager:    manager,
		clients:    make(map[*Client]bool),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan []byte, 256),
		logger:     logger,
		jwtSecret:  []byte(jwtSecret),
	}
}

// SetBackendForwarder sets the backend forwarder
func (s *Server) SetBackendForwarder(forwarder BackendForwarder) {
	s.backendForwarder = forwarder
}

// Run starts the WebSocket server hub
func (s *Server) Run() {
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case client := <-s.register:
			s.mu.Lock()
			s.clients[client] = true
			s.mu.Unlock()
			s.logger.Infow("WebSocket client connected", "user_id", client.userID)

		case client := <-s.unregister:
			s.mu.Lock()
			if _, ok := s.clients[client]; ok {
				delete(s.clients, client)
				close(client.send)
				s.logger.Infow("WebSocket client disconnected", "user_id", client.userID)
			}
			s.mu.Unlock()

		case message := <-s.broadcast:
			s.mu.RLock()
			for client := range s.clients {
				select {
				case client.send <- message:
				default:
					close(client.send)
					delete(s.clients, client)
				}
			}
			s.mu.RUnlock()

		case <-ticker.C:
			s.broadcastRobotStatus()
		}
	}
}

// broadcastRobotStatus sends robot status to subscribed clients
func (s *Server) broadcastRobotStatus() {
	robots := s.manager.GetAllRobots()
	
	s.mu.RLock()
	defer s.mu.RUnlock()

	for client := range s.clients {
		client.mu.RLock()
		for _, r := range robots {
			if len(client.subscribedBots) == 0 || client.subscribedBots[r.ID] {
				status := RobotStatusData{
					ID:               r.ID,
					Name:             r.Name,
					Vendor:           r.Vendor,
					Model:            r.Model,
					State:            r.State,
					Battery:          r.Battery,
					Position:         robot.Position{X: r.X, Y: r.Y, Theta: r.Theta},
					IsOnline:         r.IsOnline,
					LastSeen:         r.LastSeen.UnixMilli(),
					CurrentMissionID: r.CurrentMissionID,
					SensorData:       s.manager.GetSensorData(r.ID),
					ControlData:      s.manager.GetControlData(r.ID),
				}

				msg := Message{
					Type:      MsgRobotStatus,
					RobotID:   r.ID,
					Data:      status,
					Timestamp: time.Now().UnixMilli(),
				}

				data, err := json.Marshal(msg)
				if err != nil {
					s.logger.Errorw("Failed to marshal robot status", "error", err)
					continue
				}

				select {
				case client.send <- data:
				default:
				}

				// Forward to backend if recording is enabled
				if client.recordingBots[r.ID] && s.backendForwarder != nil {
					go s.backendForwarder.ForwardSensorData(r.ID, status.SensorData, status.ControlData)
				}
			}
		}
		client.mu.RUnlock()
	}
}

// HandleWebSocket handles WebSocket upgrade requests
func (s *Server) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	// Extract and validate JWT token
	token := r.URL.Query().Get("token")
	if token == "" {
		token = r.Header.Get("Authorization")
		if len(token) > 7 && token[:7] == "Bearer " {
			token = token[7:]
		}
	}

	userID, err := s.validateToken(token)
	if err != nil {
		s.logger.Warnw("Invalid token", "error", err)
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		s.logger.Errorw("WebSocket upgrade failed", "error", err)
		return
	}

	client := &Client{
		conn:           conn,
		server:         s,
		send:           make(chan []byte, 256),
		userID:         userID,
		subscribedBots: make(map[string]bool),
		recordingBots:  make(map[string]bool),
	}

	s.register <- client

	go client.writePump()
	go client.readPump()
}

// validateToken validates JWT token and returns user ID
func (s *Server) validateToken(tokenString string) (string, error) {
	if tokenString == "" {
		return "", fmt.Errorf("empty token")
	}

	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return s.jwtSecret, nil
	})

	if err != nil {
		return "", err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		if sub, ok := claims["sub"].(string); ok {
			return sub, nil
		}
	}

	return "", fmt.Errorf("invalid token claims")
}

// readPump reads messages from the WebSocket connection
func (c *Client) readPump() {
	defer func() {
		c.server.unregister <- c
		c.conn.Close()
	}()

	c.conn.SetReadLimit(maxMessageSize)
	c.conn.SetReadDeadline(time.Now().Add(pongWait))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				c.server.logger.Errorw("WebSocket read error", "error", err)
			}
			break
		}

		c.handleMessage(message)
	}
}

// writePump writes messages to the WebSocket connection
func (c *Client) writePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// handleMessage processes incoming WebSocket messages
func (c *Client) handleMessage(data []byte) {
	var msg Message
	if err := json.Unmarshal(data, &msg); err != nil {
		c.sendError("Invalid message format")
		return
	}

	switch msg.Type {
	case MsgSubscribe:
		c.handleSubscribe(msg)
	case MsgUnsubscribe:
		c.handleUnsubscribe(msg)
	case MsgCommand:
		c.handleCommand(msg)
	case MsgSetRecording:
		c.handleSetRecording(msg)
	default:
		c.sendError("Unknown message type")
	}
}

// handleSubscribe handles robot subscription
func (c *Client) handleSubscribe(msg Message) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if len(msg.RobotIDs) > 0 {
		for _, id := range msg.RobotIDs {
			c.subscribedBots[id] = true
		}
	} else if msg.RobotID != "" {
		c.subscribedBots[msg.RobotID] = true
	}

	c.server.logger.Infow("Client subscribed to robots",
		"user_id", c.userID,
		"robot_ids", msg.RobotIDs,
	)
}

// handleUnsubscribe handles robot unsubscription
func (c *Client) handleUnsubscribe(msg Message) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if len(msg.RobotIDs) > 0 {
		for _, id := range msg.RobotIDs {
			delete(c.subscribedBots, id)
			delete(c.recordingBots, id)
		}
	} else if msg.RobotID != "" {
		delete(c.subscribedBots, msg.RobotID)
		delete(c.recordingBots, msg.RobotID)
	}
}

// handleCommand handles robot commands
func (c *Client) handleCommand(msg Message) {
	if msg.RobotID == "" {
		c.sendError("robot_id is required")
		return
	}

	// Capture robot state before command execution (for ML training data)
	robtStateBefore := make(map[string]float64)
	if r, err := c.server.manager.GetRobot(msg.RobotID); err == nil && r != nil {
		robtStateBefore["x"] = r.X
		robtStateBefore["y"] = r.Y
		robtStateBefore["theta"] = r.Theta
		robtStateBefore["battery"] = r.Battery
	}

	var err error
	switch msg.Command {
	case "move":
		x, _ := msg.Params["x"].(float64)
		y, _ := msg.Params["y"].(float64)
		err = c.server.manager.MoveRobot(msg.RobotID, x, y)
	case "stop":
		err = c.server.manager.StopRobot(msg.RobotID)
	case "pause":
		err = c.server.manager.PauseRobot(msg.RobotID)
	case "resume":
		err = c.server.manager.ResumeRobot(msg.RobotID)
	default:
		c.sendError("Unknown command: " + msg.Command)
		return
	}

	success := err == nil
	errorMsg := ""
	if err != nil {
		errorMsg = err.Error()
	}

	response := Message{
		Type:      MsgCommandResponse,
		RobotID:   msg.RobotID,
		Command:   msg.Command,
		Success:   success,
		Timestamp: time.Now().UnixMilli(),
	}

	if err != nil {
		response.Error = errorMsg
	}

	data, _ := json.Marshal(response)
	c.send <- data

	// Forward command data to backend if recording is enabled for this robot
	c.mu.RLock()
	isRecording := c.recordingBots[msg.RobotID]
	c.mu.RUnlock()

	if isRecording && c.server.backendForwarder != nil {
		cmdParams := make(map[string]float64)
		for k, v := range msg.Params {
			if fv, ok := v.(float64); ok {
				cmdParams[k] = fv
			}
		}
		go c.server.backendForwarder.ForwardCommandData(
			msg.RobotID, c.userID, msg.Command,
			cmdParams, success, errorMsg, robtStateBefore,
		)
	}
}

// handleSetRecording handles recording enable/disable
func (c *Client) handleSetRecording(msg Message) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if msg.RobotID == "" {
		c.sendError("robot_id is required")
		return
	}

	if msg.Recording {
		c.recordingBots[msg.RobotID] = true
	} else {
		delete(c.recordingBots, msg.RobotID)
	}

	response := Message{
		Type:      MsgRecordingStatus,
		RobotID:   msg.RobotID,
		Recording: msg.Recording,
		Success:   true,
		Timestamp: time.Now().UnixMilli(),
	}

	data, _ := json.Marshal(response)
	c.send <- data

	c.server.logger.Infow("Recording status changed",
		"user_id", c.userID,
		"robot_id", msg.RobotID,
		"recording", msg.Recording,
	)
}

// sendError sends an error message to the client
func (c *Client) sendError(errMsg string) {
	msg := Message{
		Type:      MsgError,
		Error:     errMsg,
		Timestamp: time.Now().UnixMilli(),
	}
	data, _ := json.Marshal(msg)
	c.send <- data
}

// Start starts the HTTP server for WebSocket
func (s *Server) Start(addr string) error {
	http.HandleFunc("/ws", s.HandleWebSocket)
	
	s.logger.Infow("WebSocket server starting", "address", addr)
	return http.ListenAndServe(addr, nil)
}
