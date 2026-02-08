package adapter

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/amr-saas/gateway/internal/robot"
	"github.com/google/uuid"
)

// MQTTAdapter implements RobotAdapter for MQTT-based robots
type MQTTAdapter struct {
	vendor      string
	client      mqtt.Client
	topicPrefix string
	connected   map[string]bool
	mu          sync.RWMutex
}

// NewMQTTAdapter creates a new MQTT adapter
func NewMQTTAdapter(vendor string, client mqtt.Client, topicPrefix string) *MQTTAdapter {
	return &MQTTAdapter{
		vendor:      vendor,
		client:      client,
		topicPrefix: topicPrefix,
		connected:   make(map[string]bool),
	}
}

// GetVendor returns the vendor name
func (a *MQTTAdapter) GetVendor() string {
	return a.vendor
}

// Connect establishes connection to the robot
func (a *MQTTAdapter) Connect(robotID string) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.connected[robotID] = true
	return nil
}

// Disconnect closes connection to the robot
func (a *MQTTAdapter) Disconnect(robotID string) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	delete(a.connected, robotID)
	return nil
}

// SendCommand sends a command to the robot via MQTT
func (a *MQTTAdapter) SendCommand(cmd Command) (*CommandResult, error) {
	topic := fmt.Sprintf("%s%s/command", a.topicPrefix, cmd.RobotID)
	commandID := uuid.New().String()

	payload := map[string]interface{}{
		"command_id": commandID,
		"type":       cmd.Type,
		"timestamp":  time.Now().Unix(),
	}

	if cmd.Goal != nil {
		payload["goal"] = cmd.Goal
	}

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal command: %w", err)
	}

	token := a.client.Publish(topic, 1, false, jsonPayload)
	token.Wait()

	if token.Error() != nil {
		return &CommandResult{
			Success: false,
			Message: fmt.Sprintf("Failed to publish command: %v", token.Error()),
		}, token.Error()
	}

	return &CommandResult{
		Success:   true,
		Message:   "Command sent successfully",
		CommandID: commandID,
	}, nil
}

// GetStatus gets current status from the robot
func (a *MQTTAdapter) GetStatus(robotID string) (*robot.Status, error) {
	// Status is typically received via subscription, not request
	// This is a placeholder for direct status request if needed
	return nil, fmt.Errorf("status retrieval via MQTT subscription")
}

// IsConnected checks if robot is connected
func (a *MQTTAdapter) IsConnected(robotID string) bool {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.connected[robotID]
}
