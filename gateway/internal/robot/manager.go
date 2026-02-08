package robot

import (
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
	ID           string       `json:"id"`
	Vendor       string       `json:"vendor"`
	State        State        `json:"state"`
	Battery      float64      `json:"battery"`
	Pose         Position     `json:"pose"`
	Capabilities Capabilities `json:"capabilities"`
	IsOnline     bool         `json:"is_online"`
	LastSeen     time.Time    `json:"last_seen"`
}

// Status returns robot status for API response
type Status struct {
	RobotID  string   `json:"robot_id"`
	State    State    `json:"state"`
	Battery  float64  `json:"battery"`
	Pose     Position `json:"pose"`
	IsOnline bool     `json:"is_online"`
}

// Manager manages all robots
type Manager struct {
	robots map[string]*Robot
	mu     sync.RWMutex
	logger *zap.SugaredLogger
}

// NewManager creates a new robot manager
func NewManager(logger *zap.SugaredLogger) *Manager {
	return &Manager{
		robots: make(map[string]*Robot),
		logger: logger,
	}
}

// RegisterRobot registers a new robot or updates existing one
func (m *Manager) RegisterRobot(id, vendor string, capabilities Capabilities) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.robots[id]; !exists {
		m.robots[id] = &Robot{
			ID:           id,
			Vendor:       vendor,
			State:        StateIdle,
			Battery:      100.0,
			Pose:         Position{X: 0, Y: 0, Theta: 0},
			Capabilities: capabilities,
			IsOnline:     true,
			LastSeen:     time.Now(),
		}
		m.logger.Infof("Registered new robot: %s (vendor: %s)", id, vendor)
	}
}

// UpdateStatus updates robot status
func (m *Manager) UpdateStatus(id string, state State, battery float64, pose Position) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if robot, exists := m.robots[id]; exists {
		robot.State = state
		robot.Battery = battery
		robot.Pose = pose
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
func (m *Manager) GetRobot(id string) (*Robot, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	robot, exists := m.robots[id]
	if !exists {
		return nil, false
	}

	// Return a copy to prevent race conditions
	robotCopy := *robot
	return &robotCopy, true
}

// GetStatus returns robot status
func (m *Manager) GetStatus(id string) (*Status, bool) {
	robot, exists := m.GetRobot(id)
	if !exists {
		return nil, false
	}

	return &Status{
		RobotID:  robot.ID,
		State:    robot.State,
		Battery:  robot.Battery,
		Pose:     robot.Pose,
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
			m.logger.Warnf("Robot %s marked as offline (no heartbeat)", id)
		}
	}
}
