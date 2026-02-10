package robot

import (
	"errors"
	"sync"
	"time"

	"go.uber.org/zap"
)

// State represents robot state
type State string

const (
	StateIdle     State = "IDLE"
	StateMoving   State = "MOVING"
	StatePaused   State = "PAUSED"
	StateError    State = "ERROR"
	StateCharging State = "CHARGING"
	StateOffline  State = "OFFLINE"
)

// Position represents robot position
type Position struct {
	X     float64 `json:"x"`
	Y     float64 `json:"y"`
	Theta float64 `json:"theta"`
}

// Capabilities represents robot capabilities
type Capabilities struct {
	SupportsPause   bool `json:"supports_pause"`
	SupportsDocking bool `json:"supports_docking"`
}

// Robot represents a robot instance
type Robot struct {
	ID               string            `json:"id"`
	Name             string            `json:"name"`
	Vendor           string            `json:"vendor"`
	Model            string            `json:"model"`
	State            string            `json:"state"`
	Battery          float64           `json:"battery"`
	X                float64           `json:"x"`
	Y                float64           `json:"y"`
	Theta            float64           `json:"theta"`
	Capabilities     Capabilities      `json:"capabilities"`
	IsOnline         bool              `json:"is_online"`
	LastSeen         time.Time         `json:"last_seen"`
	CurrentMissionID string            `json:"current_mission_id"`
	Metadata         map[string]string `json:"metadata"`
}

// Status returns robot status for API response
type Status struct {
	RobotID  string  `json:"robot_id"`
	State    string  `json:"state"`
	Battery  float64 `json:"battery"`
	X        float64 `json:"x"`
	Y        float64 `json:"y"`
	Theta    float64 `json:"theta"`
	IsOnline bool    `json:"is_online"`
}

// Manager manages all robots
type Manager struct {
	robots          map[string]*Robot
	sensorDataStore map[string]map[string]float64
	controlDataStore map[string]map[string]float64
	mu              sync.RWMutex
	logger          *zap.SugaredLogger
}

// NewManager creates a new robot manager
func NewManager(logger *zap.SugaredLogger) *Manager {
	return &Manager{
		robots:           make(map[string]*Robot),
		sensorDataStore:  make(map[string]map[string]float64),
		controlDataStore: make(map[string]map[string]float64),
		logger:           logger,
	}
}

// RegisterRobot registers a new robot or updates existing one
func (m *Manager) RegisterRobot(id, name, vendor, model string, capabilities Capabilities) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.robots[id]; !exists {
		m.robots[id] = &Robot{
			ID:           id,
			Name:         name,
			Vendor:       vendor,
			Model:        model,
			State:        string(StateIdle),
			Battery:      100.0,
			X:            0,
			Y:            0,
			Theta:        0,
			Capabilities: capabilities,
			IsOnline:     true,
			LastSeen:     time.Now(),
			Metadata:     make(map[string]string),
		}
		m.logger.Infof("Registered new robot: %s (vendor: %s)", id, vendor)
	}
}

// UpdateStatus updates robot status
func (m *Manager) UpdateStatus(id string, state string, battery float64, x, y, theta float64) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if robot, exists := m.robots[id]; exists {
		robot.State = state
		robot.Battery = battery
		robot.X = x
		robot.Y = y
		robot.Theta = theta
		robot.IsOnline = true
		robot.LastSeen = time.Now()
		m.logger.Debugf("Updated status for robot %s: state=%s, battery=%.1f", id, state, battery)
	}
}

// SetOnline sets robot online status
func (m *Manager) SetOnline(id string, online bool) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if robot, exists := m.robots[id]; exists {
		robot.IsOnline = online
		robot.LastSeen = time.Now()
	}
}

// GetRobot returns a robot by ID
func (m *Manager) GetRobot(id string) (*Robot, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	robot, exists := m.robots[id]
	if !exists {
		return nil, errors.New("robot not found")
	}

	// Return a copy to prevent race conditions
	robotCopy := *robot
	return &robotCopy, nil
}

// GetStatus returns robot status
func (m *Manager) GetStatus(id string) (*Status, bool) {
	robot, err := m.GetRobot(id)
	if err != nil {
		return nil, false
	}

	return &Status{
		RobotID:  robot.ID,
		State:    robot.State,
		Battery:  robot.Battery,
		X:        robot.X,
		Y:        robot.Y,
		Theta:    robot.Theta,
		IsOnline: robot.IsOnline,
	}, true
}

// GetAllRobots returns all robots
func (m *Manager) GetAllRobots() []*Robot {
	m.mu.RLock()
	defer m.mu.RUnlock()

	robots := make([]*Robot, 0, len(m.robots))
	for _, robot := range m.robots {
		robotCopy := *robot
		robots = append(robots, &robotCopy)
	}
	return robots
}

// GetOnlineRobots returns count of online robots
func (m *Manager) GetOnlineRobots() int {
	m.mu.RLock()
	defer m.mu.RUnlock()

	count := 0
	for _, robot := range m.robots {
		if robot.IsOnline {
			count++
		}
	}
	return count
}

// CheckTimeouts marks robots as offline if no heartbeat received
func (m *Manager) CheckTimeouts(timeout time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	for id, robot := range m.robots {
		if robot.IsOnline && now.Sub(robot.LastSeen) > timeout {
			robot.IsOnline = false
			robot.State = string(StateOffline)
			m.logger.Warnf("Robot %s marked as offline (no heartbeat)", id)
		}
	}
}

// MoveRobot sends move command to robot
func (m *Manager) MoveRobot(id string, x, y float64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	robot, exists := m.robots[id]
	if !exists {
		return errors.New("robot not found")
	}

	if !robot.IsOnline {
		return errors.New("robot is offline")
	}

	robot.State = string(StateMoving)
	m.logger.Infow("Move command sent", "robot_id", id, "target_x", x, "target_y", y)
	return nil
}

// StopRobot sends stop command to robot
func (m *Manager) StopRobot(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	robot, exists := m.robots[id]
	if !exists {
		return errors.New("robot not found")
	}

	if !robot.IsOnline {
		return errors.New("robot is offline")
	}

	robot.State = string(StateIdle)
	m.logger.Infow("Stop command sent", "robot_id", id)
	return nil
}

// PauseRobot sends pause command to robot
func (m *Manager) PauseRobot(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	robot, exists := m.robots[id]
	if !exists {
		return errors.New("robot not found")
	}

	if !robot.IsOnline {
		return errors.New("robot is offline")
	}

	if !robot.Capabilities.SupportsPause {
		return errors.New("robot does not support pause")
	}

	robot.State = string(StatePaused)
	m.logger.Infow("Pause command sent", "robot_id", id)
	return nil
}

// ResumeRobot sends resume command to robot
func (m *Manager) ResumeRobot(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	robot, exists := m.robots[id]
	if !exists {
		return errors.New("robot not found")
	}

	if !robot.IsOnline {
		return errors.New("robot is offline")
	}

	robot.State = string(StateMoving)
	m.logger.Infow("Resume command sent", "robot_id", id)
	return nil
}

// SetCurrentMission sets the current mission for a robot
func (m *Manager) SetCurrentMission(id, missionID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	robot, exists := m.robots[id]
	if !exists {
		return errors.New("robot not found")
	}

	robot.CurrentMissionID = missionID
	return nil
}

// UpdateSensorData updates sensor data for a robot
func (m *Manager) UpdateSensorData(robotID string, data map[string]float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.sensorDataStore[robotID] = data
}

// UpdateControlData updates control data for a robot
func (m *Manager) UpdateControlData(robotID string, data map[string]float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.controlDataStore[robotID] = data
}

// GetSensorData returns sensor data for a robot
func (m *Manager) GetSensorData(robotID string) map[string]float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if data, exists := m.sensorDataStore[robotID]; exists {
		// Return a copy
		result := make(map[string]float64)
		for k, v := range data {
			result[k] = v
		}
		return result
	}
	return nil
}

// GetControlData returns control data for a robot
func (m *Manager) GetControlData(robotID string) map[string]float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if data, exists := m.controlDataStore[robotID]; exists {
		// Return a copy
		result := make(map[string]float64)
		for k, v := range data {
			result[k] = v
		}
		return result
	}
	return nil
}
