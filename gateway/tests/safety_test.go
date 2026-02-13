package tests

import (
	"testing"

	"github.com/robot-ai-webapp/gateway/internal/safety"
	"go.uber.org/zap"
)

func TestVelocityLimiter_NoClamp(t *testing.T) {
	logger := zap.NewNop()
	limiter := safety.NewVelocityLimiter(1.0, 2.0, logger)

	result := limiter.Limit(safety.VelocityInput{
		LinearX:  0.5,
		LinearY:  0.0,
		AngularZ: 1.0,
	})

	if result.Clamped {
		t.Error("Expected no clamping")
	}
	if result.LinearX != 0.5 {
		t.Errorf("Expected linear_x=0.5, got %f", result.LinearX)
	}
	if result.AngularZ != 1.0 {
		t.Errorf("Expected angular_z=1.0, got %f", result.AngularZ)
	}
}

func TestVelocityLimiter_ClampLinear(t *testing.T) {
	logger := zap.NewNop()
	limiter := safety.NewVelocityLimiter(1.0, 2.0, logger)

	result := limiter.Limit(safety.VelocityInput{
		LinearX:  2.0,
		LinearY:  0.0,
		AngularZ: 0.0,
	})

	if !result.Clamped {
		t.Error("Expected clamping")
	}
	if result.LinearX != 1.0 {
		t.Errorf("Expected linear_x=1.0, got %f", result.LinearX)
	}
}

func TestVelocityLimiter_ClampAngular(t *testing.T) {
	logger := zap.NewNop()
	limiter := safety.NewVelocityLimiter(1.0, 2.0, logger)

	result := limiter.Limit(safety.VelocityInput{
		LinearX:  0.5,
		AngularZ: 5.0,
	})

	if !result.Clamped {
		t.Error("Expected clamping")
	}
	if result.AngularZ != 2.0 {
		t.Errorf("Expected angular_z=2.0, got %f", result.AngularZ)
	}
}

func TestOperationLock_AcquireRelease(t *testing.T) {
	logger := zap.NewNop()
	lock := safety.NewOperationLock(300*1000*1000*1000, logger) // 300 sec

	// Acquire lock
	info, err := lock.Acquire("robot-1", "user-1")
	if err != nil {
		t.Fatalf("Failed to acquire lock: %v", err)
	}
	if info.UserID != "user-1" {
		t.Errorf("Expected user_id=user-1, got %s", info.UserID)
	}

	// Check lock
	if !lock.CheckLock("robot-1", "user-1") {
		t.Error("Expected lock to be held by user-1")
	}
	if lock.CheckLock("robot-1", "user-2") {
		t.Error("Expected lock NOT to be held by user-2")
	}

	// Another user tries to acquire
	_, err = lock.Acquire("robot-1", "user-2")
	if err == nil {
		t.Error("Expected error when another user tries to acquire")
	}

	// Release lock
	err = lock.Release("robot-1", "user-1")
	if err != nil {
		t.Fatalf("Failed to release lock: %v", err)
	}

	// Now user-2 can acquire
	_, err = lock.Acquire("robot-1", "user-2")
	if err != nil {
		t.Fatalf("user-2 should be able to acquire after release: %v", err)
	}
}

func TestEStopManager(t *testing.T) {
	logger := zap.NewNop()

	// We need a registry with a mock adapter
	// For unit test, we just test the state management
	registry := setupMockRegistry(logger)
	estop := safety.NewEStopManager(registry, logger)

	if estop.IsActive("robot-1") {
		t.Error("E-Stop should not be active initially")
	}

	// We can't fully test without a connected adapter, but test state
	_ = estop.Activate(nil, "robot-1", "user-1", "test")
	if !estop.IsActive("robot-1") {
		t.Error("E-Stop should be active after activation")
	}

	estop.Release("robot-1", "user-1")
	if estop.IsActive("robot-1") {
		t.Error("E-Stop should not be active after release")
	}
}
