package safety

import (
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// LockInfo holds information about an operation lock
type LockInfo struct {
	RobotID   string
	UserID    string
	AcquiredAt time.Time
	ExpiresAt  time.Time
}

// OperationLock manages exclusive access to robots
type OperationLock struct {
	mu      sync.RWMutex
	locks   map[string]*LockInfo // robot_id -> lock info
	timeout time.Duration
	logger  *zap.Logger
}

// NewOperationLock creates a new operation lock manager
func NewOperationLock(timeout time.Duration, logger *zap.Logger) *OperationLock {
	ol := &OperationLock{
		locks:   make(map[string]*LockInfo),
		timeout: timeout,
		logger:  logger,
	}
	return ol
}

// StartCleanup starts a goroutine that periodically cleans up expired locks
func (o *OperationLock) StartCleanup(done <-chan struct{}) {
	go func() {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				o.cleanupExpired()
			}
		}
	}()
}

// Acquire tries to acquire the operation lock for a robot
func (o *OperationLock) Acquire(robotID, userID string) (*LockInfo, error) {
	o.mu.Lock()
	defer o.mu.Unlock()

	now := time.Now()

	// Check if lock exists and is still valid
	if existing, ok := o.locks[robotID]; ok {
		if existing.ExpiresAt.After(now) {
			if existing.UserID == userID {
				// Same user, extend lock
				existing.ExpiresAt = now.Add(o.timeout)
				o.logger.Debug("Operation lock extended",
					zap.String("robot_id", robotID),
					zap.String("user_id", userID),
				)
				return existing, nil
			}
			return existing, fmt.Errorf("robot %s is locked by user %s until %s",
				robotID, existing.UserID, existing.ExpiresAt.Format(time.RFC3339))
		}
		// Lock expired, remove it
		delete(o.locks, robotID)
	}

	// Acquire new lock
	lock := &LockInfo{
		RobotID:    robotID,
		UserID:     userID,
		AcquiredAt: now,
		ExpiresAt:  now.Add(o.timeout),
	}
	o.locks[robotID] = lock

	o.logger.Info("Operation lock acquired",
		zap.String("robot_id", robotID),
		zap.String("user_id", userID),
		zap.Time("expires_at", lock.ExpiresAt),
	)

	return lock, nil
}

// Release releases the operation lock for a robot
func (o *OperationLock) Release(robotID, userID string) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	lock, ok := o.locks[robotID]
	if !ok {
		return nil // No lock to release
	}

	if lock.UserID != userID {
		return fmt.Errorf("cannot release lock: owned by %s, requested by %s", lock.UserID, userID)
	}

	delete(o.locks, robotID)
	o.logger.Info("Operation lock released",
		zap.String("robot_id", robotID),
		zap.String("user_id", userID),
	)
	return nil
}

// CheckLock checks if a user holds the lock for a robot
func (o *OperationLock) CheckLock(robotID, userID string) bool {
	o.mu.RLock()
	defer o.mu.RUnlock()

	lock, ok := o.locks[robotID]
	if !ok {
		return false
	}

	return lock.UserID == userID && lock.ExpiresAt.After(time.Now())
}

// GetLockInfo returns the current lock info for a robot
func (o *OperationLock) GetLockInfo(robotID string) *LockInfo {
	o.mu.RLock()
	defer o.mu.RUnlock()

	lock, ok := o.locks[robotID]
	if !ok || lock.ExpiresAt.Before(time.Now()) {
		return nil
	}
	return lock
}

func (o *OperationLock) cleanupExpired() {
	o.mu.Lock()
	defer o.mu.Unlock()

	now := time.Now()
	for robotID, lock := range o.locks {
		if lock.ExpiresAt.Before(now) {
			delete(o.locks, robotID)
			o.logger.Info("Expired operation lock cleaned up",
				zap.String("robot_id", robotID),
				zap.String("user_id", lock.UserID),
			)
		}
	}
}
