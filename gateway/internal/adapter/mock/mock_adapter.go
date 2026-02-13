package mock

import (
	"context"
	"math"
	"math/rand"
	"sync"
	"time"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"go.uber.org/zap"
)

// MockAdapter generates simulated sensor data for development and testing
type MockAdapter struct {
	logger     *zap.Logger
	sensorCh   chan adapter.SensorData
	connected  bool
	mu         sync.RWMutex
	cancelFunc context.CancelFunc

	// Simulated robot state
	posX, posY, posTheta float64
	linearVel, angularVel float64
}

// Factory creates a new MockAdapter
func Factory(logger *zap.Logger) adapter.RobotAdapter {
	return &MockAdapter{
		logger:   logger,
		sensorCh: make(chan adapter.SensorData, 100),
	}
}

func (m *MockAdapter) Name() string {
	return "mock"
}

func (m *MockAdapter) Connect(ctx context.Context, config map[string]any) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.connected {
		return nil
	}

	m.connected = true
	m.posX = 0
	m.posY = 0
	m.posTheta = 0

	sensorCtx, cancel := context.WithCancel(ctx)
	m.cancelFunc = cancel

	// Start sensor data generators
	go m.generateOdometry(sensorCtx)
	go m.generateLidar(sensorCtx)
	go m.generateIMU(sensorCtx)
	go m.generateBattery(sensorCtx)

	m.logger.Info("Mock adapter connected")
	return nil
}

func (m *MockAdapter) Disconnect(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.connected {
		return nil
	}

	if m.cancelFunc != nil {
		m.cancelFunc()
	}
	m.connected = false
	m.logger.Info("Mock adapter disconnected")
	return nil
}

func (m *MockAdapter) IsConnected() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.connected
}

func (m *MockAdapter) SendCommand(ctx context.Context, cmd adapter.Command) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	switch cmd.Type {
	case "velocity":
		if lx, ok := cmd.Payload["linear_x"]; ok {
			m.linearVel = toFloat64(lx)
		}
		if az, ok := cmd.Payload["angular_z"]; ok {
			m.angularVel = toFloat64(az)
		}
		m.logger.Debug("Velocity command received",
			zap.Float64("linear_x", m.linearVel),
			zap.Float64("angular_z", m.angularVel),
		)
	case "estop":
		m.linearVel = 0
		m.angularVel = 0
		m.logger.Warn("Emergency stop activated")
	}

	return nil
}

func (m *MockAdapter) SensorDataChannel() <-chan adapter.SensorData {
	return m.sensorCh
}

func (m *MockAdapter) GetCapabilities() adapter.Capabilities {
	return adapter.Capabilities{
		SupportsVelocityControl: true,
		SupportsNavigation:      true,
		SupportsEStop:           true,
		SensorTopics:            []string{"odom", "scan", "imu", "battery"},
		MaxLinearVelocity:       1.0,
		MaxAngularVelocity:      2.0,
	}
}

func (m *MockAdapter) EmergencyStop(ctx context.Context) error {
	return m.SendCommand(ctx, adapter.Command{Type: "estop"})
}

// --- Sensor data generators ---

func (m *MockAdapter) generateOdometry(ctx context.Context) {
	ticker := time.NewTicker(50 * time.Millisecond) // 20Hz
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			m.mu.Lock()
			dt := 0.05
			m.posTheta += m.angularVel * dt
			m.posX += m.linearVel * math.Cos(m.posTheta) * dt
			m.posY += m.linearVel * math.Sin(m.posTheta) * dt
			data := adapter.SensorData{
				Topic:     "odom",
				DataType:  "odometry",
				FrameID:   "odom",
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					"pos_x":      m.posX,
					"pos_y":      m.posY,
					"pos_theta":  m.posTheta,
					"linear_vel": m.linearVel,
					"angular_vel": m.angularVel,
				},
			}
			m.mu.Unlock()

			select {
			case m.sensorCh <- data:
			default:
				// Drop if buffer full
			}
		}
	}
}

func (m *MockAdapter) generateLidar(ctx context.Context) {
	ticker := time.NewTicker(100 * time.Millisecond) // 10Hz
	defer ticker.Stop()

	numRays := 360

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			ranges := make([]float64, numRays)
			for i := 0; i < numRays; i++ {
				angle := float64(i) * math.Pi * 2 / float64(numRays)
				// Simulate a room with walls
				dist := 5.0 + rand.Float64()*0.1
				if math.Abs(math.Cos(angle)) > 0.7 {
					dist = 3.0 + rand.Float64()*0.1
				}
				if math.Abs(math.Sin(angle)) > 0.7 {
					dist = 4.0 + rand.Float64()*0.1
				}
				ranges[i] = dist
			}

			data := adapter.SensorData{
				Topic:     "scan",
				DataType:  "laser_scan",
				FrameID:   "laser",
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					"angle_min":       0.0,
					"angle_max":       2 * math.Pi,
					"angle_increment": 2 * math.Pi / float64(numRays),
					"range_min":       0.1,
					"range_max":       30.0,
					"ranges":          ranges,
				},
			}

			select {
			case m.sensorCh <- data:
			default:
			}
		}
	}
}

func (m *MockAdapter) generateIMU(ctx context.Context) {
	ticker := time.NewTicker(20 * time.Millisecond) // 50Hz
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			m.mu.RLock()
			theta := m.posTheta
			angVel := m.angularVel
			linVel := m.linearVel
			m.mu.RUnlock()

			data := adapter.SensorData{
				Topic:     "imu",
				DataType:  "imu",
				FrameID:   "imu_link",
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					"orientation_x": 0.0,
					"orientation_y": 0.0,
					"orientation_z": math.Sin(theta / 2),
					"orientation_w": math.Cos(theta / 2),
					"angular_vel_x": rand.Float64() * 0.01,
					"angular_vel_y": rand.Float64() * 0.01,
					"angular_vel_z": angVel + rand.Float64()*0.01,
					"linear_acc_x":  linVel*0.1 + rand.Float64()*0.05,
					"linear_acc_y":  rand.Float64() * 0.05,
					"linear_acc_z":  9.81 + rand.Float64()*0.05,
				},
			}

			select {
			case m.sensorCh <- data:
			default:
			}
		}
	}
}

func (m *MockAdapter) generateBattery(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	percentage := 85.0

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			percentage -= rand.Float64() * 0.1
			if percentage < 10 {
				percentage = 85.0
			}

			data := adapter.SensorData{
				Topic:     "battery",
				DataType:  "battery_state",
				FrameID:   "base_link",
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					"voltage":    12.6 * (percentage / 100),
					"current":    -0.5 - rand.Float64()*0.3,
					"percentage": percentage,
				},
			}

			select {
			case m.sensorCh <- data:
			default:
			}
		}
	}
}

func toFloat64(v any) float64 {
	switch val := v.(type) {
	case float64:
		return val
	case float32:
		return float64(val)
	case int:
		return float64(val)
	case int64:
		return float64(val)
	default:
		return 0
	}
}
