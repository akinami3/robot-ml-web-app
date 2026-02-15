// =============================================================================
// ファイル: mock_adapter.go
// 概要: ロボットのシミュレーション（模擬）アダプター
//
// このファイルは、実際のロボットハードウェアが無くても開発・テストができるように、
// 仮想的なロボットを作成するファイルです。「モックアダプター」と呼ばれます。
//
// 主な機能:
//   - 仮想ロボットへの接続・切断
//   - 速度コマンドの受信と仮想的な位置更新
//   - センサーデータ（オドメトリ、LiDAR、IMU、バッテリー）の模擬生成
//   - 緊急停止（E-Stop）機能
//
// デザインパターン:
//   - アダプターパターン: adapter.RobotAdapter インターフェースを実装し、
//     実際のロボットと同じインターフェースで操作可能
//   - ファクトリーパターン: Factory関数でインスタンスを生成
//   - Pub/Sub的パターン: チャネルを通じてセンサーデータを配信
//
// リアルタイム概念:
//   - オドメトリ: 20Hz（1秒間に20回）で位置・速度を更新
//   - LiDAR: 10Hz（1秒間に10回）で距離データを生成
//   - IMU: 50Hz（1秒間に50回）で姿勢データを生成
//   - バッテリー: 0.2Hz（5秒に1回）でバッテリー状態を更新
//
// =============================================================================
package mock

// =============================================================================
// インポート（import）セクション
// Go言語では、使用する外部パッケージをここで宣言します。
// 使わないインポートがあるとコンパイルエラーになります（Goの厳格なルール）。
// =============================================================================
import (
	// --- Go標準ライブラリ ---

	// "context": ゴルーチン（並行処理）のキャンセル・タイムアウトを管理するパッケージ。
	// 例えば「接続を切ったらセンサー生成も止める」という制御に使います。
	"context"

	// "math": 数学関数（Sin, Cos, Piなど）を提供するパッケージ。
	// ロボットの位置計算や角度計算に必要です。
	"math"

	// "math/rand": 乱数（ランダムな数値）を生成するパッケージ。
	// センサーデータにノイズ（雑音）を加えて、よりリアルなシミュレーションにします。
	"math/rand"

	// "sync": 同期処理のためのパッケージ。
	// sync.RWMutex（読み書きロック）を使って、複数のゴルーチンが同時に
	// データにアクセスしても安全にするために使います。
	"sync"

	// "time": 時間関連の機能を提供するパッケージ。
	// タイマー（Ticker）やタイムスタンプの取得に使います。
	"time"

	// --- プロジェクト内部パッケージ ---

	// adapter: ロボットアダプターのインターフェースと型定義が含まれるパッケージ。
	// RobotAdapter インターフェース、SensorData、Command、Capabilities などの
	// 型がここで定義されています。
	"github.com/robot-ai-webapp/gateway/internal/adapter"

	// --- 外部ライブラリ ---

	// zap: Uber社が開発した高性能なログ出力ライブラリ。
	// fmt.Println() よりも構造化されたログを高速に出力できます。
	// 本番環境でのデバッグや監視に重要です。
	"go.uber.org/zap"
)

// =============================================================================
// Factory関数 - ファクトリーパターン
// =============================================================================
//
// 【ファクトリーパターンとは？】
// オブジェクト（構造体のインスタンス）を生成するための専用関数です。
// 直接 &MockAdapter{...} と書く代わりに、Factory() を呼ぶことで
// 生成の詳細を隠蔽（いんぺい）できます。
//
// 【なぜ adapter.AdapterFactory 型を満たす？】
// adapter パッケージで「type AdapterFactory func(*zap.Logger) RobotAdapter」
// のような型が定義されており、この Factory 関数はそのシグネチャ（引数と戻り値の型）
// に一致します。これにより、レジストリに登録して動的にアダプターを選択できます。
//
// 【使い方の例】
//
//	registry.Register("mock", mock.Factory)  // 名前で登録
//	adapter := mock.Factory(logger)          // 直接呼び出しも可能
func Factory(logger *zap.Logger) adapter.RobotAdapter {
	return NewMockAdapter(logger)
}

// =============================================================================
// MockAdapter 構造体
// =============================================================================
//
// 【構造体（struct）とは？】
// Go言語にはクラスがありません。代わりに「構造体」を使ってデータをまとめます。
// 構造体にメソッド（関数）を付けることで、オブジェクト指向に近い設計ができます。
//
// 【この構造体の役割】
// 仮想ロボットの全状態（位置、速度、バッテリーなど）を保持し、
// adapter.RobotAdapter インターフェースの全メソッドを実装します。
//
// 【インターフェースの実装について】
// Go言語では「implements」キーワードは不要です。
// インターフェースで定義された全メソッドを持っていれば、自動的にそのインターフェースを
// 満たします（暗黙的インターフェース実装 = duck typing）。
type MockAdapter struct {
	// --- 同期・通信関連フィールド ---

	// mu: sync.RWMutex（読み書きミューテックス）
	// 【RWMutexとは？】
	// 複数のゴルーチンが同じデータに同時アクセスすると「データ競合（race condition）」が
	// 起きます。RWMutexはこれを防ぐためのロック機構です。
	//
	// - RLock()/RUnlock(): 「読み取りロック」- 複数のゴルーチンが同時に読み取り可能
	// - Lock()/Unlock(): 「書き込みロック」- 1つのゴルーチンだけが書き込み可能
	//
	// 読み取りは頻繁に行うが書き込みは少ない場合、RWMutexが効率的です。
	// 通常のMutexだと読み取り同士もブロックしてしまいます。
	mu sync.RWMutex

	// connected: ロボットが接続されているかどうかを表すフラグ
	connected bool

	// dataCh: センサーデータを送信するためのチャネル
	// 【チャネル（channel）とは？】
	// ゴルーチン間でデータを安全にやり取りするためのGoの仕組みです。
	// パイプ（管）をイメージしてください。一方が入れて、もう一方が取り出します。
	//
	// 【バッファ付きチャネル】
	// make(chan adapter.SensorData, 100) で作成するチャネルは「バッファサイズ100」です。
	// つまり、受信側が取り出さなくても最大100個のデータを溜められます。
	// バッファが溢れると、送信側はブロックされる（待たされる）か、
	// default節で送信をスキップします。
	//
	// 【方向付きチャネル】
	// SensorDataChannel() メソッドでは <-chan （受信専用）として返します。
	// これにより、外部からはデータの読み取りのみ可能になります。
	dataCh chan adapter.SensorData

	// cancel: context.CancelFunc - ゴルーチンを停止するための関数
	// 【CancelFuncとは？】
	// context.WithCancel() で生成されるキャンセル関数です。
	// この関数を呼ぶと、対応するcontextの Done() チャネルが閉じられ、
	// そのcontextを監視しているすべてのゴルーチンに「停止してください」と合図できます。
	cancel context.CancelFunc

	// logger: 構造化ログを出力するためのロガー
	logger *zap.Logger

	// --- ロボットシミュレーション状態 ---

	// posX, posY: ロボットの2D位置（メートル単位）
	// 原点(0,0)からの座標で表されます。
	posX float64
	posY float64

	// theta: ロボットの向き（ラジアン単位）
	// 0 = 東向き、π/2 = 北向き、π = 西向き、3π/2 = 南向き
	// ラジアン = 度 × (π / 180)
	theta float64

	// linearX: 前進方向の速度（m/s）
	// 正の値 = 前進、負の値 = 後退
	linearX float64

	// linearY: 横方向の速度（m/s）
	// 通常の差動駆動ロボットでは0ですが、メカナムホイール等では使用します。
	linearY float64

	// angularZ: 回転速度（rad/s）
	// 正の値 = 反時計回り、負の値 = 時計回り
	angularZ float64

	// battery: バッテリー残量（0.0〜100.0のパーセンテージ）
	battery float64
}

// =============================================================================
// NewMockAdapter - コンストラクタ関数
// =============================================================================
//
// 【コンストラクタとは？】
// Go言語にはコンストラクタ構文がないため、慣例として New〇〇() という関数を作ります。
// 構造体を適切に初期化して返すのが役割です。
//
// 【ポインタ返却 *MockAdapter】
// &MockAdapter{...} とすることで、構造体のポインタ（メモリアドレス）を返します。
// これにより、呼び出し元とこの関数内で同じデータを共有できます。
// 値渡し（コピー）ではなく参照渡しのような動作になります。
func NewMockAdapter(logger *zap.Logger) *MockAdapter {
	return &MockAdapter{
		// バッファ付きチャネルを100の容量で作成
		// 100個分のセンサーデータを一時的に蓄えられます
		dataCh: make(chan adapter.SensorData, 100),

		// ロガーを保存
		logger: logger,

		// バッテリーは満充電（100%）で開始
		battery: 100.0,
	}
}

// =============================================================================
// Name - アダプター名を返すメソッド
// =============================================================================
//
// 【メソッドの書き方】
// func (m *MockAdapter) Name() string
// ↑ (m *MockAdapter) はレシーバーと呼ばれます。
// これにより、MockAdapterの「メソッド」としてドット記法で呼べます。
// 例: adapter.Name() → "mock"
//
// 【1行メソッド】
// Goでは短いメソッドを1行で書くことも一般的です。
func (m *MockAdapter) Name() string { return "mock" }

// =============================================================================
// Connect - ロボットへの接続を開始するメソッド
// =============================================================================
//
// 【contextパラメータ】
// ctx context.Context は、Goの並行処理で「キャンセル」や「タイムアウト」を
// 伝搬するための仕組みです。関数の最初の引数として渡すのがGoの慣例です。
//
// 【configパラメータ】
// map[string]any 型は「文字列キーで何でも格納できる辞書」です。
// 【any型とは？】
// Go 1.18で導入された型で、interface{} の別名（エイリアス）です。
// 任意の型の値を受け取れますが、使う時に型アサーション（後述）が必要です。
//
// 【このメソッドの処理フロー】
// 1. ミューテックスでロック（排他制御）
// 2. 既に接続済みなら何もしない（冪等性）
// 3. 新しいcontextを作成（キャンセル可能な子context）
// 4. 4つのセンサーデータ生成ゴルーチンを起動
// 5. ログ出力
func (m *MockAdapter) Connect(ctx context.Context, config map[string]any) error {
	// 【Lock/Unlock のペア】
	// Lock() で書き込みロックを取得します。
	// defer m.mu.Unlock() とすることで、この関数が終了する時（return時）に
	// 自動的にロックが解放されます。
	//
	// 【deferとは？】
	// defer は「この関数が終了する直前に実行する」という予約です。
	// ロックの解放忘れ、ファイルの閉じ忘れなどを防ぐためにGoではよく使います。
	// 複数のdeferがある場合、LIFO（後入先出）の順番で実行されます。
	m.mu.Lock()
	defer m.mu.Unlock()

	// 既に接続されている場合は何もしない（冪等性: 何度呼んでも同じ結果）
	if m.connected {
		return nil
	}

	// 【context.WithCancel の仕組み】
	// 親context（ctx）から新しい子context（sensorCtx）を作成します。
	// cancel 関数を呼ぶと、sensorCtx.Done() チャネルが閉じられます。
	// これにより、sensorCtx を使っている全てのゴルーチンに停止を通知できます。
	//
	//   親context (ctx) → 子context (sensorCtx)
	//   cancel() 呼び出し → sensorCtx.Done() が閉じる → ゴルーチンが停止
	sensorCtx, cancel := context.WithCancel(ctx)
	m.cancel = cancel
	m.connected = true

	// 【ゴルーチン（goroutine）とは？】
	// go キーワードを付けて関数を呼ぶと、その関数が「別のスレッド（軽量スレッド）」で
	// 並行に実行されます。OSのスレッドよりもはるかに軽量で、数千個同時に動かせます。
	//
	// ここでは4つのセンサーデータ生成器を並行に起動しています:
	// - オドメトリ（位置・速度）: 20Hz
	// - LiDAR（距離センサー）: 10Hz
	// - IMU（慣性計測装置）: 50Hz
	// - バッテリー: 0.2Hz

	// Start sensor data generators
	go m.generateOdometry(sensorCtx)
	go m.generateLiDAR(sensorCtx)
	go m.generateIMU(sensorCtx)
	go m.generateBattery(sensorCtx)

	// 接続成功のログを出力
	m.logger.Info("Mock adapter connected")
	return nil
}

// =============================================================================
// Disconnect - ロボットとの接続を切断するメソッド
// =============================================================================
//
// cancel() を呼ぶことで、Connect() で起動した全てのゴルーチンに停止を通知します。
// これが context を使った「優雅な停止（graceful shutdown）」パターンです。
func (m *MockAdapter) Disconnect(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// cancelがnilでなければ（=接続されていれば）キャンセルを実行
	if m.cancel != nil {
		m.cancel()
	}
	m.connected = false
	m.logger.Info("Mock adapter disconnected")
	return nil
}

// =============================================================================
// IsConnected - 接続状態を確認するメソッド
// =============================================================================
//
// 【RLock/RUnlock - 読み取りロック】
// この関数は connected の値を「読み取る」だけなので、RLock()（読み取りロック）を使います。
// 読み取りロックは同時に複数のゴルーチンが取得可能なので、パフォーマンスが良くなります。
// 書き込みロック（Lock()）を使うと、読み取りだけの場合でも他をブロックしてしまいます。
func (m *MockAdapter) IsConnected() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.connected
}

// =============================================================================
// SendCommand - ロボットにコマンドを送信するメソッド
// =============================================================================
//
// 【adapter.Command構造体】
// コマンドには Type（種類）と Payload（データ本体）が含まれています。
// Payload は map[string]any 型なので、様々な種類のデータを柔軟に格納できます。
//
// 【このメソッドの処理】
// "velocity"（速度）コマンドを受け取ったら、仮想ロボットの速度を更新します。
// 更新された速度は generateOdometry() で位置計算に使われます。
func (m *MockAdapter) SendCommand(ctx context.Context, cmd adapter.Command) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// コマンドタイプが "velocity"（速度指令）の場合
	if cmd.Type == "velocity" {
		// Payload からそれぞれの速度成分を取得
		// toFloat64() はany型をfloat64に安全に変換するヘルパー関数（後述）
		m.linearX = toFloat64(cmd.Payload["linear_x"])
		m.linearY = toFloat64(cmd.Payload["linear_y"])
		m.angularZ = toFloat64(cmd.Payload["angular_z"])
	}

	return nil
}

// =============================================================================
// SensorDataChannel - センサーデータの受信チャネルを返すメソッド
// =============================================================================
//
// 【方向付きチャネル: <-chan】
// 戻り値の型が <-chan adapter.SensorData です。
// これは「受信専用チャネル」を意味します。
//
// - chan T:     送受信両方可能なチャネル
// - <-chan T:   受信のみ可能なチャネル（読み取り専用）
// - chan<- T:   送信のみ可能なチャネル（書き込み専用）
//
// 内部的には dataCh は双方向チャネルですが、外部には受信専用として公開します。
// これにより、外部のコードがデータを送信してしまうミスを防げます。
func (m *MockAdapter) SensorDataChannel() <-chan adapter.SensorData {
	return m.dataCh
}

// =============================================================================
// GetCapabilities - ロボットの能力を返すメソッド
// =============================================================================
//
// 【Capabilities構造体】
// ロボットが何ができるかを表現します。フロントエンドはこの情報を使って、
// 表示するUIコンポーネント（速度制御スライダー、ナビゲーションボタンなど）を
// 動的に切り替えます。
//
// 【構造体リテラル】
// adapter.Capabilities{...} のように、フィールド名: 値 の形式で初期化します。
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

// =============================================================================
// EmergencyStop - 緊急停止メソッド
// =============================================================================
//
// 【緊急停止（E-Stop）とは？】
// ロボットの動作を即座に停止する安全機能です。
// 実際のロボットでは、モーターへの電力供給を遮断するなどの処理を行います。
// このモックでは、全ての速度を0に設定します。
//
// 【logger.Warn】
// 通常のInfo（情報）ではなくWarn（警告）レベルでログを出力します。
// ログレベル: Debug < Info < Warn < Error < Fatal
func (m *MockAdapter) EmergencyStop(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.linearX = 0
	m.linearY = 0
	m.angularZ = 0
	m.logger.Warn("EMERGENCY STOP triggered on mock adapter")
	return nil
}

// =============================================================================
//
//	センサーデータ生成器（ゴルーチンで実行される関数群）
//
// =============================================================================

// =============================================================================
// generateOdometry - オドメトリ（位置・速度）データの生成
// =============================================================================
//
// 【オドメトリとは？】
// ロボットの位置と速度を推定する手法です。車輪の回転数やエンコーダーの値から
// 「どれだけ移動したか」を積算して現在位置を計算します。
//
// 【更新頻度: 20Hz】
// 50ミリ秒ごと（1秒に20回）にデータを更新します。
// ロボット工学では、制御ループの周波数が高いほど精密な制御が可能です。
//
// 【位置計算の数学】
// dt = 0.05秒（50ミリ秒）
// θ（theta）+= ω（angularZ）× dt      → 向きの更新
// x += v（linearX）× cos(θ) × dt       → X座標の更新
// y += v（linearX）× sin(θ) × dt       → Y座標の更新
//
// これは「デッドレコニング（推測航法）」と呼ばれる手法で、
// 速度から位置を積分（近似的に積算）しています。
func (m *MockAdapter) generateOdometry(ctx context.Context) {
	// 【time.NewTicker】
	// 指定した間隔で定期的にチャネルに値を送信するタイマーです。
	// 50ミリ秒 = 0.05秒ごと → 20Hz
	ticker := time.NewTicker(50 * time.Millisecond) // 20Hz
	// deferでTickerを停止（メモリリーク防止）
	defer ticker.Stop()

	// 【無限ループ + select文】
	// この組み合わせは、Goの並行処理で非常によく使うパターンです。
	// 「何かイベントが起きるまで待機し、イベントが来たら処理する」というループです。
	for {
		// 【select文とは？】
		// 複数のチャネル操作のうち、準備ができたものを実行します。
		// switch文に似ていますが、チャネル専用です。
		// 複数のcaseが同時に準備できた場合、ランダムに1つが選ばれます。
		select {
		case <-ctx.Done():
			// 【ctx.Done()】
			// contextがキャンセルされた（cancel()が呼ばれた）場合、このチャネルが閉じます。
			// チャネルが閉じると、<-ctx.Done() は即座にゼロ値を返します。
			// これにより、ゴルーチンを安全に終了できます。
			return
		case <-ticker.C:
			// Tickerから50ミリ秒ごとに通知が来る

			// 書き込みロックを取得（位置と速度の更新のため）
			m.mu.Lock()

			dt := 0.05 // 50ms = 0.05秒

			// 【位置の更新計算】
			// 1. 向き（theta）を更新: 回転速度 × 時間
			m.theta += m.angularZ * dt

			// 2. X座標を更新: 前進速度 × cos(向き) × 時間
			//    cos(theta) は、向きのX成分（東西方向）を計算します
			m.posX += m.linearX * math.Cos(m.theta) * dt

			// 3. Y座標を更新: 前進速度 × sin(向き) × 時間
			//    sin(theta) は、向きのY成分（南北方向）を計算します
			m.posY += m.linearX * math.Sin(m.theta) * dt

			// 送信するセンサーデータを構造体リテラルで作成
			data := adapter.SensorData{
				Topic:     "odom",                 // トピック名（購読者がフィルタに使う）
				DataType:  "odometry",             // データの種類
				FrameID:   "odom",                 // 座標系の基準フレーム
				Timestamp: time.Now().UnixMilli(), // 現在時刻のミリ秒タイムスタンプ
				Data: map[string]any{
					"position_x":    m.posX,     // X座標（m）
					"position_y":    m.posY,     // Y座標（m）
					"orientation_z": m.theta,    // 向き（rad）
					"velocity_x":    m.linearX,  // 前進速度（m/s）
					"velocity_y":    m.linearY,  // 横方向速度（m/s）
					"angular_z":     m.angularZ, // 回転速度（rad/s）
				},
			}

			// ロックを解放（データ作成が完了したので）
			m.mu.Unlock()

			// 【チャネルへの安全な送信パターン】
			// 2段階のselect文を使って、チャネルが満杯の場合はデータを捨てます。
			// これにより、受信側が遅くても送信側がブロックされることを防ぎます。
			select {
			case m.dataCh <- data:
				// チャネルに正常に送信できた
			default: // drop if channel is full
				// 【default節】
				// チャネルのバッファが満杯の場合、ブロックせずにここに来ます。
				// センサーデータは連続的に生成されるので、古いデータを捨てても問題ありません。
				// これは「非ブロッキング送信」のパターンです。
			}
		}
	}
}

// =============================================================================
// generateLiDAR - LiDARセンサーデータの生成
// =============================================================================
//
// 【LiDAR（ライダー）とは？】
// Light Detection And Ranging の略で、レーザー光を使って周囲の距離を測定するセンサーです。
// 360度の方向にレーザーを照射し、反射光が戻ってくるまでの時間から距離を計算します。
//
// 【シミュレーションの仕組み】
// - 360個の距離データ（1度刻み）を生成
// - 基本距離3.0m + sin関数で壁の凹凸を模擬
// - ±0.1mのランダムノイズを追加してリアルさを演出
//
// 【更新頻度: 10Hz】
// 100ミリ秒ごと（1秒に10回）にデータを生成します。
// 実際のLiDARも5~40Hzで動作することが多いです。
func (m *MockAdapter) generateLiDAR(ctx context.Context) {
	ticker := time.NewTicker(100 * time.Millisecond) // 10Hz
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// 360個の距離データを格納するスライスを作成
			// 【スライスとは？】
			// Goの可変長配列です。make([]float64, 360) で360個のfloat64を確保します。
			// 初期値は全て0.0です。
			ranges := make([]float64, 360)

			// 0度〜359度の各方向について距離を計算
			for i := range ranges {
				// 【度からラジアンへの変換】
				// Go の math パッケージはラジアンを使います。
				// 度 → ラジアン: angle = 度 × π / 180
				angle := float64(i) * math.Pi / 180.0

				// 【部屋のシミュレーション】
				// sin関数で壁の距離を変化させ、楕円形の部屋を模擬します。
				// baseRange = 3.0 + sin(angle×2) × 1.0
				// → 距離が2.0m〜4.0mの間で変化する
				// Simulate a room
				baseRange := 3.0 + math.Sin(angle*2.0)*1.0

				// ランダムノイズ（0〜0.1m）を追加
				// 実際のセンサーにもノイズ（測定誤差）があります
				ranges[i] = baseRange + rand.Float64()*0.1 // add noise
			}

			// LiDARデータの構造体を作成
			data := adapter.SensorData{
				Topic:     "scan", // "scan" はLiDARの一般的なトピック名
				DataType:  "lidar",
				FrameID:   "lidar_link", // LiDARセンサーの座標フレーム
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					"angle_min":       0.0,             // スキャン開始角度（0ラジアン）
					"angle_max":       2 * math.Pi,     // スキャン終了角度（2π = 360度）
					"angle_increment": math.Pi / 180.0, // 角度の増分（1度 = π/180ラジアン）
					"range_min":       0.1,             // 測定可能な最小距離（0.1m）
					"range_max":       12.0,            // 測定可能な最大距離（12.0m）
					"ranges":          ranges,          // 360個の距離データ
				},
			}

			// チャネルへの非ブロッキング送信
			select {
			case m.dataCh <- data:
			default:
			}
		}
	}
}

// =============================================================================
// generateIMU - IMUセンサーデータの生成
// =============================================================================
//
// 【IMU（慣性計測装置）とは？】
// Inertial Measurement Unit の略で、加速度センサーとジャイロスコープを
// 組み合わせたセンサーです。ロボットの姿勢（傾き、向き）や回転速度を高速に測定します。
//
// 【クォータニオン（四元数）による姿勢表現】
// ロボットの向きは「クォータニオン」で表現します。
// 2D回転の場合: orientation_z = sin(θ/2), orientation_w = cos(θ/2)
// これは「オイラー角（roll, pitch, yaw）」よりも数学的に安定した表現方法です。
// 特に「ジンバルロック」と呼ばれる問題が起きません。
//
// 【更新頻度: 50Hz】
// 20ミリ秒ごと（1秒に50回）にデータを生成します。
// IMUは高速なセンサーで、実際には100Hz〜1000Hzで動作することもあります。
func (m *MockAdapter) generateIMU(ctx context.Context) {
	ticker := time.NewTicker(20 * time.Millisecond) // 50Hz
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// 読み取りロックで theta を取得
			// ここでは読み取りだけなので RLock を使用（他の読み取りをブロックしない）
			m.mu.RLock()
			theta := m.theta
			m.mu.RUnlock()

			data := adapter.SensorData{
				Topic:     "imu",
				DataType:  "imu",
				FrameID:   "imu_link",
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					// 【クォータニオン（四元数）の値】
					// 2Dの場合、z軸周りの回転のみなので:
					// x = 0, y = 0（回転軸がz軸なので）
					// z = sin(θ/2)  ← 回転の虚数部分
					// w = cos(θ/2)  ← 回転の実数部分
					// |q| = √(x²+y²+z²+w²) = 1 （単位クォータニオン）
					"orientation_x": 0.0,
					"orientation_y": 0.0,
					"orientation_z": math.Sin(theta / 2.0),
					"orientation_w": math.Cos(theta / 2.0),

					// ジャイロスコープ: z軸周りの回転速度（rad/s）
					"angular_vel_z": m.angularZ,

					// 加速度センサー: 各軸の加速度（m/s²）
					// x, y: ランダムノイズ（-0.05〜+0.05）で微小な振動を模擬
					// z: 重力加速度（9.81 m/s²）+ ノイズ（-0.01〜+0.01）
					"linear_acc_x": rand.Float64()*0.1 - 0.05,
					"linear_acc_y": rand.Float64()*0.1 - 0.05,
					"linear_acc_z": 9.81 + rand.Float64()*0.02 - 0.01,
				},
			}

			select {
			case m.dataCh <- data:
			default:
			}
		}
	}
}

// =============================================================================
// generateBattery - バッテリーデータの生成
// =============================================================================
//
// 【バッテリーモニタリング】
// ロボットのバッテリー残量を定期的に報告します。
// 5秒ごとに0.01%ずつ減少させ、バッテリーが徐々に消耗するのを模擬します。
//
// 【更新頻度: 0.2Hz】
// 5秒ごと（1秒に0.2回）にデータを更新します。
// バッテリー状態は頻繁に変化しないので、低い周波数で十分です。
//
// 【バッテリー電圧の計算】
// voltage = 12.0V × (残量 / 100)
// 実際のリチウムイオンバッテリーは、放電曲線がもっと複雑ですが、
// ここでは簡略化して線形に減少させています。
func (m *MockAdapter) generateBattery(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Second) // 0.2Hz
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// 書き込みロックでバッテリー値を更新
			m.mu.Lock()
			m.battery -= 0.01 // 0.01%ずつ減少
			if m.battery < 0 {
				m.battery = 0 // 0%以下にはならない
			}
			bat := m.battery // ローカル変数にコピー（ロック外で使うため）
			m.mu.Unlock()

			data := adapter.SensorData{
				Topic:     "battery",
				DataType:  "battery",
				FrameID:   "base_link",
				Timestamp: time.Now().UnixMilli(),
				Data: map[string]any{
					"percentage": bat,                  // バッテリー残量（%）
					"voltage":    12.0 * (bat / 100.0), // 電圧（V）= 12V × 残量比率
					"current":    -0.5,                 // 電流（A）負の値は放電中を意味する
					"charging":   false,                // 充電中フラグ
				},
			}

			select {
			case m.dataCh <- data:
			default:
			}
		}
	}
}

// =============================================================================
// toFloat64 - any型からfloat64への安全な型変換ヘルパー関数
// =============================================================================
//
// 【型スイッチ（type switch）とは？】
// Go言語の any（interface{}）型の値が実際に何の型なのかを判定する構文です。
// 通常のswitch文に似ていますが、値ではなく「型」で分岐します。
//
// 【なぜこの関数が必要？】
// map[string]any のPayloadから値を取り出すと、型が any のままです。
// JSONデコードした場合、数値は通常 float64 になりますが、
// 他のソースからは int や float32 など、様々な型で来る可能性があります。
// この関数は、どの数値型が来ても安全にfloat64に変換します。
//
// 【構文の説明】
//
//	switch val := v.(type) {  ← v の実際の型で分岐し、val にキャスト済みの値が入る
//	case float64:             ← v が float64 型の場合
//	    return val            ← val は float64 型として使える
//	}
//
// 【型アサーション v.(type) との違い】
// - v.(float64): 単一の型へのアサーション。失敗するとpanicまたは第2戻り値がfalse
// - v.(type): switch文専用。複数の型を安全に判定可能
func toFloat64(v any) float64 {
	switch val := v.(type) {
	case float64:
		return val
	case float32:
		// float32 → float64 への変換
		return float64(val)
	case int:
		// int → float64 への変換
		return float64(val)
	case int64:
		// int64 → float64 への変換
		return float64(val)
	default:
		// 上記以外の型（nil、string等）の場合は0.0を返す
		return 0.0
	}
}
