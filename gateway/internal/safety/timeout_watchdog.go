package safety

import (
	"context"
	"sync"
	"time"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"go.uber.org/zap"
)

// TimeoutWatchdog monitors for command timeouts and auto-stops robots
type TimeoutWatchdog struct {
	mu            sync.RWMutex
	lastCommand   map[string]time.Time // robot_id -> last command time
	timeout       time.Duration
	registry      *adapter.Registry
	logger        *zap.Logger
	cancelFunc    context.CancelFunc
	onTimeout     func(robotID string) // callback when timeout triggers
}

// NewTimeoutWatchdog creates a new timeout watchdog
func NewTimeoutWatchdog(
	timeout time.Duration,
	registry *adapter.Registry,
	logger *zap.Logger,
) *TimeoutWatchdog {
	return &TimeoutWatchdog{
		lastCommand: make(map[string]time.Time),
		timeout:     timeout,
		registry:    registry,
		logger:      logger,
	}
}

// SetTimeoutCallback sets the callback function when a timeout occurs
func (t *TimeoutWatchdog) SetTimeoutCallback(fn func(robotID string)) {
	t.onTimeout = fn
}

// RecordCommand records that a command was received for a robot
func (t *TimeoutWatchdog) RecordCommand(robotID string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.lastCommand[robotID] = time.Now()
}

// RemoveRobot removes a robot from timeout monitoring
func (t *TimeoutWatchdog) RemoveRobot(robotID string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	delete(t.lastCommand, robotID)
}

// Start begins the watchdog goroutine
func (t *TimeoutWatchdog) Start(ctx context.Context) {
	watchCtx, cancel := context.WithCancel(ctx)
	t.cancelFunc = cancel

	go t.run(watchCtx)
	t.logger.Info("Timeout watchdog started", zap.Duration("timeout", t.timeout))
}

// Stop stops the watchdog
func (t *TimeoutWatchdog) Stop() {
	if t.cancelFunc != nil {
		t.cancelFunc()
	}
}

func (t *TimeoutWatchdog) run(ctx context.Context) {
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case now := <-ticker.C:
			t.checkTimeouts(ctx, now)
		}
	}
}

func (t *TimeoutWatchdog) checkTimeouts(ctx context.Context, now time.Time) {
	t.mu.RLock()
	var timedOut []string
	for robotID, lastCmd := range t.lastCommand {
		if now.Sub(lastCmd) > t.timeout {
			timedOut = append(timedOut, robotID)
		}
	}
	t.mu.RUnlock()

	for _, robotID := range timedOut {
		t.logger.Warn("Command timeout - auto-stopping robot",
			zap.String("robot_id", robotID),
			zap.Duration("timeout", t.timeout),
		)

		// Send zero velocity command
		if adp, ok := t.registry.GetAdapter(robotID); ok {
			_ = adp.SendCommand(ctx, adapter.Command{
				Type: "velocity",
				Payload: map[string]any{
					"linear_x":  0.0,
					"linear_y":  0.0,
					"angular_z": 0.0,
				},
			})
		}

		// Remove from monitoring until next command
		t.mu.Lock()
		delete(t.lastCommand, robotID)
		t.mu.Unlock()

		// Notify via callback
		if t.onTimeout != nil {
			t.onTimeout(robotID)
		}
	}
}
