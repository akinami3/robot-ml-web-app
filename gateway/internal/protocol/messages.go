package protocol

import (
	"time"
)

// MessageType defines the type of WebSocket message
type MessageType string

const (
	// Client -> Gateway
	MsgTypeAuth              MessageType = "auth"
	MsgTypeVelocityCommand   MessageType = "velocity_cmd"
	MsgTypeNavigationGoal    MessageType = "nav_goal"
	MsgTypeNavigationCancel  MessageType = "nav_cancel"
	MsgTypeEmergencyStop     MessageType = "estop"
	MsgTypeOperationLock     MessageType = "op_lock"
	MsgTypeOperationUnlock   MessageType = "op_unlock"
	MsgTypePing              MessageType = "ping"

	// Gateway -> Client
	MsgTypeSensorData        MessageType = "sensor_data"
	MsgTypeRobotStatus       MessageType = "robot_status"
	MsgTypeCommandAck        MessageType = "cmd_ack"
	MsgTypeLockStatus        MessageType = "lock_status"
	MsgTypeConnectionStatus  MessageType = "conn_status"
	MsgTypeError             MessageType = "error"
	MsgTypePong              MessageType = "pong"
	MsgTypeSafetyAlert       MessageType = "safety_alert"
)

// Message is the unified WebSocket message envelope
type Message struct {
	Type      MessageType    `msgpack:"type" json:"type"`
	Topic     string         `msgpack:"topic,omitempty" json:"topic,omitempty"`
	RobotID   string         `msgpack:"robot_id,omitempty" json:"robot_id,omitempty"`
	UserID    string         `msgpack:"user_id,omitempty" json:"user_id,omitempty"`
	Timestamp int64          `msgpack:"ts" json:"ts"`
	Payload   map[string]any `msgpack:"payload,omitempty" json:"payload,omitempty"`
	Error     string         `msgpack:"error,omitempty" json:"error,omitempty"`
}

// NewMessage creates a new message with the current timestamp
func NewMessage(msgType MessageType, robotID string) *Message {
	return &Message{
		Type:      msgType,
		RobotID:   robotID,
		Timestamp: time.Now().UnixMilli(),
		Payload:   make(map[string]any),
	}
}

// VelocityPayload from velocity command messages
type VelocityPayload struct {
	LinearX  float64 `msgpack:"linear_x" json:"linear_x"`
	LinearY  float64 `msgpack:"linear_y" json:"linear_y"`
	AngularZ float64 `msgpack:"angular_z" json:"angular_z"`
}

// NavigationGoalPayload from navigation goal messages
type NavigationGoalPayload struct {
	X                    float64 `msgpack:"x" json:"x"`
	Y                    float64 `msgpack:"y" json:"y"`
	Z                    float64 `msgpack:"z" json:"z"`
	OrientationW         float64 `msgpack:"ow" json:"ow"`
	FrameID              string  `msgpack:"frame_id" json:"frame_id"`
	TolerancePosition    float64 `msgpack:"tol_pos" json:"tol_pos"`
	ToleranceOrientation float64 `msgpack:"tol_ori" json:"tol_ori"`
}

// EStopPayload from emergency stop messages
type EStopPayload struct {
	Activate bool   `msgpack:"activate" json:"activate"`
	Reason   string `msgpack:"reason" json:"reason"`
}

// SensorDataPayload for sensor data messages
type SensorDataPayload struct {
	DataType string         `msgpack:"data_type" json:"data_type"`
	FrameID  string         `msgpack:"frame_id" json:"frame_id"`
	Data     map[string]any `msgpack:"data" json:"data"`
}

// AuthPayload for authentication messages
type AuthPayload struct {
	Token string `msgpack:"token" json:"token"`
}

// ConnectionStatusPayload for connection status messages
type ConnectionStatusPayload struct {
	RobotID   string `msgpack:"robot_id" json:"robot_id"`
	Connected bool   `msgpack:"connected" json:"connected"`
	Adapter   string `msgpack:"adapter" json:"adapter"`
}
