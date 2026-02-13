package adapter

import (
	"fmt"
	"sync"

	"go.uber.org/zap"
)

// AdapterFactory is a function that creates a new RobotAdapter instance
type AdapterFactory func(logger *zap.Logger) RobotAdapter

// Registry manages adapter factories and active adapter instances
type Registry struct {
	mu        sync.RWMutex
	factories map[string]AdapterFactory
	active    map[string]RobotAdapter // robot_id -> adapter
	logger    *zap.Logger
}

// NewRegistry creates a new adapter registry
func NewRegistry(logger *zap.Logger) *Registry {
	return &Registry{
		factories: make(map[string]AdapterFactory),
		active:    make(map[string]RobotAdapter),
		logger:    logger,
	}
}

// RegisterFactory registers an adapter factory for a given adapter type
func (r *Registry) RegisterFactory(adapterType string, factory AdapterFactory) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.factories[adapterType] = factory
	r.logger.Info("Registered adapter factory", zap.String("type", adapterType))
}

// CreateAdapter creates and stores a new adapter for a robot
func (r *Registry) CreateAdapter(robotID, adapterType string) (RobotAdapter, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	factory, ok := r.factories[adapterType]
	if !ok {
		return nil, fmt.Errorf("unknown adapter type: %s", adapterType)
	}

	adapter := factory(r.logger.With(zap.String("robot_id", robotID), zap.String("adapter", adapterType)))
	r.active[robotID] = adapter

	r.logger.Info("Created adapter",
		zap.String("robot_id", robotID),
		zap.String("type", adapterType),
	)

	return adapter, nil
}

// GetAdapter returns the active adapter for a robot
func (r *Registry) GetAdapter(robotID string) (RobotAdapter, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	adapter, ok := r.active[robotID]
	return adapter, ok
}

// RemoveAdapter disconnects and removes an adapter
func (r *Registry) RemoveAdapter(robotID string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.active, robotID)
	r.logger.Info("Removed adapter", zap.String("robot_id", robotID))
}

// GetAllActive returns all active adapters
func (r *Registry) GetAllActive() map[string]RobotAdapter {
	r.mu.RLock()
	defer r.mu.RUnlock()
	result := make(map[string]RobotAdapter, len(r.active))
	for k, v := range r.active {
		result[k] = v
	}
	return result
}

// ListFactories returns registered adapter type names
func (r *Registry) ListFactories() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	types := make([]string, 0, len(r.factories))
	for k := range r.factories {
		types = append(types, k)
	}
	return types
}
