// =============================================================================
// Step 4: センサー可視化 — MockAdapter（LiDAR + IMU 追加）
// =============================================================================
//
// 【Step 3 からの変更点】
// 1. LiDAR データ生成を追加（10Hz、360度スキャン）
// 2. IMU データ生成を追加（50Hz、6軸）
// 3. 各センサーが異なる周波数で独立動作
//
// 【センサー周波数の違い】
// 実際のロボットでは、各センサーが異なる周波数で動作する。
//   - LiDAR:    10Hz（1秒に10回、360度スキャン）
//   - IMU:      50Hz（1秒に50回、加速度・角速度）
//   - Odometry: 20Hz（1秒に20回、位置・速度）
//   - Battery:  0.2Hz（5秒に1回）
//
// =============================================================================
package mock

import (
	"context"
	"fmt"
	"log"
	"math"
	"math/rand"
	"sync"
	"time"

	// 親パッケージの adapter をインポート
	// internal/adapter/mock → internal/adapter
	"github.com/robot-ai-webapp/gateway/internal/adapter"
)

// コンパイル時にインターフェースを満たすか確認する
// 【この行の意味】
// MockAdapter のポインタ(*MockAdapter) が adapter.RobotAdapter を
// 実装しているかをコンパイル時にチェックする。
// 実装漏れがあればコンパイルエラーになるので、安全。
// nil を使うのは実際にインスタンスを作る必要がないため。
var _ adapter.RobotAdapter = (*MockAdapter)(nil)

// =============================================================================
// MockAdapter 構造体
// =============================================================================
//
// 【フィールドの分類】
// 1. 同期・通信: mu, connected, dataCh, cancel
// 2. シミュレーション状態: posX, posY, theta, linearX, angularZ, battery
//
// 【sync.RWMutex の役割】
// 複数のgoroutineがフィールドに同時アクセスする:
// - writePump goroutine: posX, posY を更新（書き込み）
// - readPump goroutine:  linearX, angularZ を更新（書き込み）
// - SensorDataChannel:   dataCh を読み取り
// → mutex で排他制御して data race を防ぐ
type MockAdapter struct {
	mu        sync.RWMutex
	connected bool
	dataCh    chan adapter.SensorData
	cancel    context.CancelFunc

	// シミュレーション状態
	posX     float64 // X座標 (m)
	posY     float64 // Y座標 (m)
	theta    float64 // 向き (rad)
	linearX  float64 // 前後速度 (m/s)
	angularZ float64 // 回転速度 (rad/s)
	battery  float64 // バッテリー (%)
}

// =============================================================================
// NewMockAdapter — コンストラクタ
// =============================================================================
func NewMockAdapter() *MockAdapter {
	return &MockAdapter{
		dataCh:  make(chan adapter.SensorData, 100),
		battery: 100.0,
	}
}

// =============================================================================
// Factory — AdapterFactory 型を満たすファクトリ関数
// =============================================================================
//
// 【ファクトリ関数の型】
// adapter.AdapterFactory = func() adapter.RobotAdapter
// Factory はこのシグネチャに一致するので、レジストリに登録できる:
//   registry.RegisterFactory("mock", mock.Factory)
func Factory() adapter.RobotAdapter {
	return NewMockAdapter()
}

// =============================================================================
// Name — アダプター名を返す
// =============================================================================
func (m *MockAdapter) Name() string {
	return "mock"
}

// =============================================================================
// Connect — モックロボットに「接続」する
// =============================================================================
//
// 【処理の流れ】
// 1. 接続フラグを true に設定
// 2. context.WithCancel でキャンセル可能なコンテキストを作成
// 3. goroutine でセンサーデータの生成を開始
//
// 【context.WithCancel とは？】
// 親コンテキストから「キャンセル可能な子コンテキスト」を作るヘルパー。
// cancel() を呼ぶと、ctx.Done() チャネルが閉じられ、
// そのコンテキストを監視している全 goroutine が停止する。
//
// なぜ必要？
// Disconnect() 時にセンサーデータ生成の goroutine を確実に停止させるため。
func (m *MockAdapter) Connect(ctx context.Context, config map[string]any) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.connected {
		return nil // 既に接続済み
	}

	m.connected = true
	m.battery = 100.0
	m.posX = 0
	m.posY = 0
	m.theta = 0

	// キャンセル可能なコンテキストを作成
	sensorCtx, cancel := context.WithCancel(context.Background())
	m.cancel = cancel

	// センサーデータ生成を goroutine で開始
	go m.generateSensorLoop(sensorCtx)

	log.Println("🤖 MockAdapter: 接続しました")
	return nil
}

// =============================================================================
// Disconnect — モックロボットから「切断」する
// =============================================================================
//
// 【cancel() の呼び出し】
// Connect で作った cancel 関数を呼ぶと、
// generateSensorLoop 内の ctx.Done() チャネルが閉じられ、
// goroutine が停止する。
func (m *MockAdapter) Disconnect(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.connected {
		return nil
	}

	m.connected = false
	if m.cancel != nil {
		m.cancel() // goroutine を停止
	}

	// 速度をリセット
	m.linearX = 0
	m.angularZ = 0

	log.Println("🤖 MockAdapter: 切断しました")
	return nil
}

// =============================================================================
// IsConnected — 接続状態を返す
// =============================================================================
func (m *MockAdapter) IsConnected() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.connected
}

// =============================================================================
// SendCommand — コマンドを処理
// =============================================================================
//
// 【コマンドの処理】
// "velocity" コマンド: linearX と angularZ を更新
// "estop" コマンド:    EmergencyStop を呼び出し
//
// 【map からの値取得と型アサーション】
// cmd.Payload["linear_x"] は any 型。
// float64 として使うには型アサーションが必要:
//   value, ok := cmd.Payload["linear_x"].(float64)
func (m *MockAdapter) SendCommand(ctx context.Context, cmd adapter.Command) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.connected {
		return fmt.Errorf("MockAdapter: 未接続")
	}

	switch cmd.Type {
	case "velocity":
		if lx, ok := cmd.Payload["linear_x"].(float64); ok {
			m.linearX = lx
		}
		if az, ok := cmd.Payload["angular_z"].(float64); ok {
			m.angularZ = az
		}
		log.Printf("🤖 速度更新: linear_x=%.2f, angular_z=%.2f", m.linearX, m.angularZ)

	case "estop":
		m.linearX = 0
		m.angularZ = 0
		log.Println("🚨 緊急停止実行")
	}

	return nil
}

// =============================================================================
// SensorDataChannel — センサーデータのチャネルを返す
// =============================================================================
func (m *MockAdapter) SensorDataChannel() <-chan adapter.SensorData {
	return m.dataCh
}

// =============================================================================
// GetCapabilities — ロボットの能力を返す
// =============================================================================
func (m *MockAdapter) GetCapabilities() adapter.Capabilities {
	return adapter.Capabilities{
		SupportsVelocityControl: true,
		SupportsNavigation:      false,
		SupportsEStop:           true,
		SensorTopics:            []string{"/odom", "/battery", "/lidar", "/imu"},
		MaxLinearVelocity:       1.0,
		MaxAngularVelocity:      1.0,
	}
}

// =============================================================================
// EmergencyStop — 緊急停止
// =============================================================================
func (m *MockAdapter) EmergencyStop(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.linearX = 0
	m.angularZ = 0
	log.Println("🚨 MockAdapter: 緊急停止")
	return nil
}

// =============================================================================
// generateSensorLoop — センサーデータを定期的に生成（goroutine で実行）
// =============================================================================
//
// 【この関数の構造: for + select パターン】
// Step 2 の writePump と同じパターン:
//   for {
//       select {
//       case <-ctx.Done(): return   // キャンセルされたら終了
//       case <-ticker.C:            // 定期的にデータ生成
//       }
//   }
//
// 【オドメトリ（Odometry）の計算】
// ロボットの位置を「前回からの移動量」で更新する。
// dt 秒間の移動量:
//   dx = linearX × cos(theta) × dt
//   dy = linearX × sin(theta) × dt
//   dθ = angularZ × dt
//
// これは「デッドレコニング（dead reckoning）」と呼ばれる手法。
func (m *MockAdapter) generateSensorLoop(ctx context.Context) {
	// 各センサーの周波数に応じた ticker を作成
	// 【複数 ticker + select パターン】
	// 複数のタイマーを1つの select で監視する。
	// 各タイマーが独立して発火するので、センサーごとに異なる周波数を実現。
	odomTicker := time.NewTicker(50 * time.Millisecond)    // 20Hz
	defer odomTicker.Stop()

	lidarTicker := time.NewTicker(100 * time.Millisecond)  // 10Hz
	defer lidarTicker.Stop()

	imuTicker := time.NewTicker(20 * time.Millisecond)     // 50Hz
	defer imuTicker.Stop()

	batteryTicker := time.NewTicker(5 * time.Second)       // 0.2Hz
	defer batteryTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("🤖 センサーデータ生成停止")
			return

		case <-odomTicker.C:
			m.updatePosition()
			m.publishOdom()

		case <-lidarTicker.C:
			m.publishLidar()

		case <-imuTicker.C:
			m.publishIMU()

		case <-batteryTicker.C:
			m.updateBattery()
			m.publishBattery()
		}
	}
}

// =============================================================================
// updatePosition — ロボット位置のシミュレーション更新
// =============================================================================
func (m *MockAdapter) updatePosition() {
	m.mu.Lock()
	defer m.mu.Unlock()

	dt := 0.05 // 50ms = 0.05秒

	// 角度の更新
	m.theta += m.angularZ * dt

	// 位置の更新（三角関数で方向に応じた移動量を計算）
	m.posX += m.linearX * math.Cos(m.theta) * dt
	m.posY += m.linearX * math.Sin(m.theta) * dt
}

// =============================================================================
// publishOdom — オドメトリデータをチャネルに送信
// =============================================================================
//
// 【select + default パターン】
// チャネルが満杯（バッファがいっぱい）の場合、通常の送信はブロックする。
// select { case ch <- data: default: } で、ブロックせずにスキップできる。
// これにより、受信側が遅くてもセンサーデータ生成が止まらない。
func (m *MockAdapter) publishOdom() {
	m.mu.RLock()
	data := adapter.SensorData{
		RobotID:   "robot-01",
		Topic:     "/odom",
		DataType:  "odometry",
		Timestamp: time.Now().UnixNano(),
		Data: map[string]any{
			"pos_x":     m.posX,
			"pos_y":     m.posY,
			"theta":     m.theta,
			"linear_x":  m.linearX,
			"angular_z": m.angularZ,
			// ノイズを加えてリアルなセンサーデータを再現
			"speed": math.Abs(m.linearX) + rand.Float64()*0.01,
		},
	}
	m.mu.RUnlock()

	select {
	case m.dataCh <- data:
		// 送信成功
	default:
		// バッファが満杯 → 古いデータを捨てる
	}
}

// =============================================================================
// updateBattery — バッテリー残量のシミュレーション更新
// =============================================================================
func (m *MockAdapter) updateBattery() {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 動いているとバッテリーが減る（停止中は緩やかに減少）
	if m.linearX != 0 || m.angularZ != 0 {
		m.battery -= 0.5 + rand.Float64()*0.3
	} else {
		m.battery -= 0.1
	}

	if m.battery < 0 {
		m.battery = 0
	}
}

// publishBattery — バッテリーデータをチャネルに送信
func (m *MockAdapter) publishBattery() {
	m.mu.RLock()
	data := adapter.SensorData{
		RobotID:   "robot-01",
		Topic:     "/battery",
		DataType:  "battery",
		Timestamp: time.Now().UnixNano(),
		Data: map[string]any{
			"percentage":  m.battery,
			"voltage":     11.5 + (m.battery/100.0)*1.1 + rand.Float64()*0.1,
			"temperature": 25.0 + rand.Float64()*5.0,
		},
	}
	m.mu.RUnlock()

	select {
	case m.dataCh <- data:
	default:
	}
}

// =============================================================================
// publishLidar — LiDAR（レーザー距離計）データを生成
// =============================================================================
//
// 【LiDAR（Light Detection and Ranging）とは？】
// レーザーを360度回転させながら照射し、反射までの時間から距離を測る。
// ロボットの周囲の障害物を検知するための主要センサー。
//
// 【データ形式: 極座標（Polar Coordinates）】
// 各データポイントは (角度, 距離) のペア。
//   - angle: レーザーの照射角度（ラジアン）
//   - range: 障害物までの距離（メートル）
//
// フロントエンドでは極座標 → 直交座標変換して Canvas に描画する:
//   x = range × cos(angle)
//   y = range × sin(angle)
//
// 【モックデータの生成】
// 360度を均等に分割し、各方向の距離を「基本距離 ± ノイズ」で生成。
// "壁" をシミュレーションするために、一部の角度範囲で距離を短くする。
func (m *MockAdapter) publishLidar() {
	m.mu.RLock()
	posX := m.posX
	posY := m.posY
	theta := m.theta
	m.mu.RUnlock()

	// 360度を等間隔で分割（1度刻み = 360点）
	numPoints := 360
	ranges := make([]float64, numPoints)
	angles := make([]float64, numPoints)

	for i := 0; i < numPoints; i++ {
		angle := float64(i) * math.Pi * 2.0 / float64(numPoints)
		angles[i] = angle

		// 基本距離: 5m（部屋サイズ）
		baseRange := 5.0

		// 壁のシミュレーション: 長方形の部屋（10m x 8m）の中にいる想定
		// ロボットの位置と向きに基づいて壁までの距離を計算
		worldAngle := angle + theta
		// 簡易的な壁の距離計算
		wallDist := m.calcWallDistance(posX, posY, worldAngle)
		if wallDist < baseRange {
			baseRange = wallDist
		}

		// ノイズを追加（実際のLiDARもノイズがある）
		noise := rand.Float64()*0.05 - 0.025 // ±2.5cm
		ranges[i] = math.Max(0.1, baseRange+noise)
	}

	data := adapter.SensorData{
		RobotID:   "robot-01",
		Topic:     "/lidar",
		DataType:  "lidar_scan",
		Timestamp: time.Now().UnixNano(),
		Data: map[string]any{
			"ranges":     ranges,
			"angles":     angles,
			"num_points": numPoints,
			"min_range":  0.1,
			"max_range":  10.0,
		},
	}

	select {
	case m.dataCh <- data:
	default:
	}
}

// calcWallDistance — 指定方向の壁までの距離を計算（簡易レイキャスト）
//
// 【レイキャスト（Ray Casting）とは？】
// ある点から特定の方向に「光線（ray）」を飛ばし、
// 最初にぶつかる物体までの距離を求める手法。
// ゲームの描画エンジンやロボットのセンサーシミュレーションで使われる。
func (m *MockAdapter) calcWallDistance(posX, posY, angle float64) float64 {
	// 部屋の境界（-5m ~ 5m × -4m ~ 4m）
	const (
		wallMinX = -5.0
		wallMaxX = 5.0
		wallMinY = -4.0
		wallMaxY = 4.0
	)

	dirX := math.Cos(angle)
	dirY := math.Sin(angle)

	minDist := 10.0 // 最大探索距離

	// 各壁との交差距離を計算
	// t = (wall - pos) / dir の正の最小値
	if dirX != 0 {
		t1 := (wallMaxX - posX) / dirX
		t2 := (wallMinX - posX) / dirX
		if t1 > 0 && t1 < minDist {
			y := posY + dirY*t1
			if y >= wallMinY && y <= wallMaxY {
				minDist = t1
			}
		}
		if t2 > 0 && t2 < minDist {
			y := posY + dirY*t2
			if y >= wallMinY && y <= wallMaxY {
				minDist = t2
			}
		}
	}
	if dirY != 0 {
		t3 := (wallMaxY - posY) / dirY
		t4 := (wallMinY - posY) / dirY
		if t3 > 0 && t3 < minDist {
			x := posX + dirX*t3
			if x >= wallMinX && x <= wallMaxX {
				minDist = t3
			}
		}
		if t4 > 0 && t4 < minDist {
			x := posX + dirX*t4
			if x >= wallMinX && x <= wallMaxX {
				minDist = t4
			}
		}
	}

	return minDist
}

// =============================================================================
// publishIMU — IMU（慣性計測装置）データを生成
// =============================================================================
//
// 【IMU（Inertial Measurement Unit）とは？】
// ロボットの運動状態を計測するセンサー。
// 通常6軸: 加速度3軸（X,Y,Z）+ 角速度3軸（X,Y,Z）
//
// 加速度（acceleration）:
//   - 静止時: Z軸に重力加速度 9.81 m/s² がかかる
//   - 前進時: X軸に正の加速度
//
// 角速度（gyroscope）:
//   - 回転時: Z軸に角速度（AngularZ と同じ値）
//
// 【ノイズのシミュレーション】
// 実際のIMUは常にノイズ（ランダムな誤差）を含む。
// ガウシアンノイズを追加してリアルさを出す。
func (m *MockAdapter) publishIMU() {
	m.mu.RLock()
	linearX := m.linearX
	angularZ := m.angularZ
	m.mu.RUnlock()

	// 加速度: 速度の変化率（簡易的に現在の速度 × 係数で近似）
	accelX := linearX*0.5 + (rand.Float64()-0.5)*0.1
	accelY := (rand.Float64() - 0.5) * 0.05 // 横方向は小さなノイズのみ
	accelZ := 9.81 + (rand.Float64()-0.5)*0.02 // 重力 + ノイズ

	// 角速度
	gyroX := (rand.Float64() - 0.5) * 0.02
	gyroY := (rand.Float64() - 0.5) * 0.02
	gyroZ := angularZ + (rand.Float64()-0.5)*0.05

	data := adapter.SensorData{
		RobotID:   "robot-01",
		Topic:     "/imu",
		DataType:  "imu",
		Timestamp: time.Now().UnixNano(),
		Data: map[string]any{
			"accel_x": accelX,
			"accel_y": accelY,
			"accel_z": accelZ,
			"gyro_x":  gyroX,
			"gyro_y":  gyroY,
			"gyro_z":  gyroZ,
		},
	}

	select {
	case m.dataCh <- data:
	default:
	}
}
