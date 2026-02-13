package safety

import (
	"context"
	"sync"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"go.uber.org/zap"
)

// EStopManager handles emergency stop functionality
type EStopManager struct {
	mu       sync.RWMutex
	active   map[string]bool // robot_id -> estop active
	registry *adapter.Registry
	logger   *zap.Logger
}

// NewEStopManager creates a new E-Stop manager
func NewEStopManager(registry *adapter.Registry, logger *zap.Logger) *EStopManager {
	return &EStopManager{
		active:   make(map[string]bool),
		registry: registry,
		logger:   logger,
	}
}

// Activate activates E-Stop for a specific robot
func (e *EStopManager) Activate(ctx context.Context, robotID, userID, reason string) error {
	e.mu.Lock()
	e.active[robotID] = true
	e.mu.Unlock()

	e.logger.Warn("E-STOP ACTIVATED",
		zap.String("robot_id", robotID),
		zap.String("user_id", userID),
		zap.String("reason", reason),
	)

	if adp, ok := e.registry.GetAdapter(robotID); ok {
		return adp.EmergencyStop(ctx)
	}
	return nil
}

// ActivateAll activates E-Stop for all connected robots
func (e *EStopManager) ActivateAll(ctx context.Context, userID, reason string) (int, []string) {
	adapters := e.registry.GetAllActive()
	stopped := 0
	var failed []string

	e.mu.Lock()
	for robotID := range adapters {
		e.active[robotID] = true
	}
	e.mu.Unlock()

	for robotID, adp := range adapters {
		if err := adp.EmergencyStop(ctx); err != nil {
			e.logger.Error("Failed to E-Stop robot",
				zap.String("robot_id", robotID),
				zap.Error(err),
			)
			failed = append(failed, robotID)
		} else {
			stopped++
		}
	}

	e.logger.Warn("E-STOP ALL ACTIVATED",
		zap.String("user_id", userID),
		zap.String("reason", reason),
		zap.Int("stopped", stopped),
		zap.Int("failed", len(failed)),
	)

	return stopped, failed
}

// Release releases E-Stop for a specific robot
func (e *EStopManager) Release(robotID, userID string) {
	e.mu.Lock()
	delete(e.active, robotID)
	e.mu.Unlock()

	e.logger.Info("E-Stop released",
		zap.String("robot_id", robotID),
		zap.String("user_id", userID),
	)
}

// IsActive checks if E-Stop is active for a robot
func (e *EStopManager) IsActive(robotID string) bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.active[robotID]
}
