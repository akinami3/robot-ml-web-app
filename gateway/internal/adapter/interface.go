package adapter

import (
	"context"
)

// SensorData represents unified sensor data from a robot
type SensorData struct {
	RobotID   string
	Topic     string
	DataType  string
	FrameID   string
	Timestamp int64
	Data      map[string]any
}

// Command represents a command to send to a robot
type Command struct {
	RobotID   string
	Type      string
	Payload   map[string]any
	Timestamp int64
}

// Capabilities describes what a robot adapter supports
type Capabilities struct {
	SupportsVelocityControl bool     `json:"supports_velocity_control"`
	SupportsNavigation      bool     `json:"supports_navigation"`
	SupportsEStop           bool     `json:"supports_estop"`
	SensorTopics            []string `json:"sensor_topics"`
	MaxLinearVelocity       float64  `json:"max_linear_velocity"`
	MaxAngularVelocity      float64  `json:"max_angular_velocity"`
}

// RobotAdapter is the interface that all robot adapters must implement.
// This enables the Plugin/Adapter pattern for supporting diverse robot protocols.
//
// To add a new robot type:
// 1. Create a new package under internal/adapter/<your_robot>/
// 2. Implement the RobotAdapter interface
// 3. Register it in the AdapterRegistry
type RobotAdapter interface {
	// Name returns the adapter name (e.g., "ros2", "mqtt", "grpc", "mock")
	Name() string

	// Connect establishes a connection to the robot
	Connect(ctx context.Context, config map[string]any) error

	// Disconnect closes the connection to the robot
	Disconnect(ctx context.Context) error

	// IsConnected returns whether the adapter is currently connected
	IsConnected() bool

	// SendCommand sends a command to the robot
	SendCommand(ctx context.Context, cmd Command) error

	// SensorDataChannel returns a channel that receives sensor data
	SensorDataChannel() <-chan SensorData

	// GetCapabilities returns what this robot supports
	GetCapabilities() Capabilities

	// EmergencyStop immediately stops the robot
	EmergencyStop(ctx context.Context) error
}
