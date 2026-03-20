// =============================================================================
// Step 3: Adapter パターン — MockAdapter（モックロボット）
// =============================================================================
//
// 【このファイルの概要】
// 実際のロボットの代わりとなる「モック（模擬）」アダプター。
// RobotAdapter インターフェースを完全に実装する。
//
// 【モック（Mock）とは？】
// 本物の代わりに使うテスト用の偽物。
// - 本物のロボット: 高価、セットアップが大変、物理的に必要
// - モック: ソフトウェアだけで動く、いつでもテスト可能
//
// 【暗黙的インターフェース実装の実例】
// このファイルの MockAdapter は、adapter.RobotAdapter インターフェースの
// メソッドを全て実装している。
// "implements" と書く必要はない — メソッドが揃っていれば自動的に満たす。
//
// コンパイラに確認させる方法（オプション）:
//   var _ adapter.RobotAdapter = (*MockAdapter)(nil)
// → コンパイルが通れば、MockAdapter は RobotAdapter を満たしている。
//
// 【Step 2 との違い】
// Step 2: main.go 内の generateMockSensorMessage() でモックデータを生成
// Step 3: MockAdapter が独立してセンサーデータを生成 → チャネル経由で配信
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
		SupportsNavigation:      false, // Step 3 では未実装
		SupportsEStop:           true,
		SensorTopics:            []string{"/odom", "/battery"},
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
	// 50ms ごと = 20Hz でセンサーデータを生成
	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop()

	batteryTicker := time.NewTicker(5 * time.Second)
	defer batteryTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("🤖 センサーデータ生成停止")
			return

		case <-ticker.C:
			m.updatePosition()
			m.publishOdom()

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
