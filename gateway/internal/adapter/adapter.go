package adapter

import (
	"github.com/amr-saas/gateway/internal/robot"
)

// Command represents a robot command
type Command struct {
	Type    string         `json:"type"`    // move, stop, pause, resume
	RobotID string         `json:"robot_id"`
	Goal    *robot.Position `json:"goal,omitempty"`
}

// CommandResult represents command execution result
type CommandResult struct {
	Success   bool   `json:"success"`
	Message   string `json:"message"`
	CommandID string `json:"command_id,omitempty"`
}

// RobotAdapter is the interface for robot vendor adapters
type RobotAdapter interface {
	// GetVendor returns the vendor name
	GetVendor() string

	// Connect establishes connection to the robot
	Connect(robotID string) error

	// Disconnect closes connection to the robot
	Disconnect(robotID string) error

	// SendCommand sends a command to the robot
	SendCommand(cmd Command) (*CommandResult, error)

	// GetStatus gets current status from the robot
	GetStatus(robotID string) (*robot.Status, error)

	// IsConnected checks if robot is connected
	IsConnected(robotID string) bool
}

// AdapterFactory creates adapters for different vendors
type AdapterFactory struct {
	adapters map[string]RobotAdapter
}

// NewAdapterFactory creates a new adapter factory
func NewAdapterFactory() *AdapterFactory {
	return &AdapterFactory{
		adapters: make(map[string]RobotAdapter),
	}
}

// RegisterAdapter registers an adapter for a vendor
func (f *AdapterFactory) RegisterAdapter(vendor string, adapter RobotAdapter) {
	f.adapters[vendor] = adapter
}

// GetAdapter returns adapter for a vendor
func (f *AdapterFactory) GetAdapter(vendor string) (RobotAdapter, bool) {
	adapter, exists := f.adapters[vendor]
	return adapter, exists
}
