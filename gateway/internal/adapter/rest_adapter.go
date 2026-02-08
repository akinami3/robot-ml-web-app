package adapter

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"github.com/amr-saas/gateway/internal/robot"
	"github.com/google/uuid"
)

// RESTAdapter implements RobotAdapter for REST API-based robots
type RESTAdapter struct {
	vendor    string
	baseURL   string
	client    *http.Client
	connected map[string]bool
	mu        sync.RWMutex
}

// NewRESTAdapter creates a new REST adapter
func NewRESTAdapter(vendor string, baseURL string) *RESTAdapter {
	return &RESTAdapter{
		vendor:  vendor,
		baseURL: baseURL,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
		connected: make(map[string]bool),
	}
}

// GetVendor returns the vendor name
func (a *RESTAdapter) GetVendor() string {
	return a.vendor
}

// Connect establishes connection to the robot
func (a *RESTAdapter) Connect(robotID string) error {
	// Check if robot API is reachable
	resp, err := a.client.Get(fmt.Sprintf("%s/robots/%s/ping", a.baseURL, robotID))
	if err != nil {
		return fmt.Errorf("failed to connect to robot %s: %w", robotID, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("robot %s not reachable: status %d", robotID, resp.StatusCode)
	}

	a.mu.Lock()
	defer a.mu.Unlock()
	a.connected[robotID] = true
	return nil
}

// Disconnect closes connection to the robot
func (a *RESTAdapter) Disconnect(robotID string) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	delete(a.connected, robotID)
	return nil
}

// SendCommand sends a command to the robot via REST API
func (a *RESTAdapter) SendCommand(cmd Command) (*CommandResult, error) {
	url := fmt.Sprintf("%s/robots/%s/command", a.baseURL, cmd.RobotID)
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

	resp, err := a.client.Post(url, "application/json", bytes.NewBuffer(jsonPayload))
	if err != nil {
		return &CommandResult{
			Success: false,
			Message: fmt.Sprintf("Failed to send command: %v", err),
		}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		body, _ := io.ReadAll(resp.Body)
		return &CommandResult{
			Success: false,
			Message: fmt.Sprintf("Command failed: %s", string(body)),
		}, fmt.Errorf("command failed with status %d", resp.StatusCode)
	}

	return &CommandResult{
		Success:   true,
		Message:   "Command sent successfully",
		CommandID: commandID,
	}, nil
}

// GetStatus gets current status from the robot
func (a *RESTAdapter) GetStatus(robotID string) (*robot.Status, error) {
	url := fmt.Sprintf("%s/robots/%s/status", a.baseURL, robotID)

	resp, err := a.client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get status: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("status request failed with status %d", resp.StatusCode)
	}

	var status robot.Status
	if err := json.NewDecoder(resp.Body).Decode(&status); err != nil {
		return nil, fmt.Errorf("failed to decode status: %w", err)
	}

	return &status, nil
}

// IsConnected checks if robot is connected
func (a *RESTAdapter) IsConnected(robotID string) bool {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.connected[robotID]
}
