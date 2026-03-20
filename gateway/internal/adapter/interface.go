// =============================================================================
// Step 3: Adapter パターン — RobotAdapter インターフェース定義
// =============================================================================
//
// 【このファイルの概要】
// ロボットアダプターのインターフェースと、共通のデータ型を定義するファイル。
// 「どんなロボットでも同じ方法で操作できる」ための契約書です。
//
// 【Adapter パターン（アダプターパターン）とは？】
// 異なるインターフェースを統一的に扱えるようにする設計パターン。
//
// 現実世界の例: 電源アダプター
//   日本のコンセント(Aタイプ) → アダプター → ヨーロッパの機器(Cタイプ)
//   異なるプラグの形を統一するのがアダプターの役割。
//
// このプロジェクトでの例:
//   ROS2ロボット  → ROS2Adapter  ─┐
//   MQTTロボット  → MQTTAdapter  ─┼→ RobotAdapter インターフェース
//   テスト用      → MockAdapter  ─┘
//
// どのロボットでも Connect(), SendCommand(), SensorDataChannel() で操作できる！
//
// 【internal ディレクトリとは？】
// Go の特殊なディレクトリ名。internal/ 配下のパッケージは、
// 親モジュール内からしかインポートできない。
// 外部プロジェクトが勝手に internal パッケージを使うのを防ぐ。
// → カプセル化（外に見せたくないコードを隠す）の仕組み。
//
// =============================================================================
package adapter

import "context"

// =============================================================================
// SensorData — センサーデータの統一型
// =============================================================================
//
// 【なぜ統一型が必要？】
// ロボットによってセンサーの形式はバラバラ:
//   ROS2: sensor_msgs/LaserScan 型
//   MQTT: JSON 文字列
//   Mock: Go の map
//
// SensorData に統一することで、受信側（WebSocket サーバー）は
// データの出所（ロボットの種類）を気にせず処理できる。
type SensorData struct {
	RobotID   string         `json:"robot_id"`   // どのロボットのデータか
	Topic     string         `json:"topic"`      // どのセンサーか（例: "/odom", "/battery"）
	DataType  string         `json:"data_type"`  // データの型（例: "odometry", "battery"）
	Timestamp int64          `json:"timestamp"`  // Unix タイムスタンプ（ナノ秒）
	Data      map[string]any `json:"data"`       // センサーデータ本体
}

// =============================================================================
// Command — ロボットへのコマンドの統一型
// =============================================================================
//
// 【map[string]any とは？】
// キーが string、値が any（= interface{} = なんでもOK）の map。
// JSON の自由な構造を Go で表現するのに使う。
//
// 例:
//   {"linear_x": 0.5, "angular_z": 0.3}       ← 速度コマンド
//   {"goal_x": 5.0, "goal_y": 3.0}            ← ナビゲーション
type Command struct {
	RobotID   string         `json:"robot_id"`
	Type      string         `json:"type"`       // "velocity", "navigate", "estop"
	Payload   map[string]any `json:"payload"`
	Timestamp int64          `json:"timestamp"`
}

// =============================================================================
// Capabilities — ロボットの能力記述
// =============================================================================
//
// 【Capabilities の用途】
// UI がロボットの能力を問い合わせて、表示を適応させるために使う。
// 例: SupportsNavigation = false → ナビゲーション画面を非表示にする。
type Capabilities struct {
	SupportsVelocityControl bool     `json:"supports_velocity_control"`
	SupportsNavigation      bool     `json:"supports_navigation"`
	SupportsEStop           bool     `json:"supports_estop"`
	SensorTopics            []string `json:"sensor_topics"`
	MaxLinearVelocity       float64  `json:"max_linear_velocity"`
	MaxAngularVelocity      float64  `json:"max_angular_velocity"`
}

// =============================================================================
// RobotAdapter — ロボットアダプターインターフェース
// =============================================================================
//
// 【Go のインターフェースとは？】
// 「これらのメソッドを全て持っていれば、この型として扱える」という約束事。
//
// Java/TypeScript: class MockAdapter implements RobotAdapter { ... }
// Go:             type MockAdapter struct { ... } + メソッド定義だけ
//                 → implements キーワード不要！（暗黙的実装）
//
// 【暗黙的実装の利点】
// 1. 後からインターフェースを定義しても、既存の型を変更不要
// 2. インターフェースと実装の依存関係が弱い（疎結合）
// 3. テスト用モックの作成が簡単
//
// 【context.Context とは？】
// Go の標準的なキャンセル・タイムアウト機構。
// 「5秒以内に終わらせて」「ユーザーがキャンセルした」などの制御を統一的に扱う。
// ネットワーク通信メソッドの第1引数に渡すのが Go の慣例。
type RobotAdapter interface {
	// Name — アダプターの名前（"mock", "ros2" など）
	Name() string

	// Connect — ロボットへの接続
	Connect(ctx context.Context, config map[string]any) error

	// Disconnect — ロボットからの切断
	Disconnect(ctx context.Context) error

	// IsConnected — 接続状態の確認
	IsConnected() bool

	// SendCommand — コマンド送信
	SendCommand(ctx context.Context, cmd Command) error

	// SensorDataChannel — センサーデータの受信チャネルを返す
	//
	// 【<-chan SensorData（受信専用チャネル）】
	// chan SensorData      — 送受信可能
	// <-chan SensorData    — 受信のみ可能（読み取り専用）
	// chan<- SensorData    — 送信のみ可能（書き込み専用）
	//
	// 受信専用にする理由:
	// 呼び出し側がうっかりチャネルにデータを送信するのを防ぐ。
	SensorDataChannel() <-chan SensorData

	// GetCapabilities — ロボットの能力情報を返す
	GetCapabilities() Capabilities

	// EmergencyStop — 緊急停止（安全上、最重要メソッド）
	EmergencyStop(ctx context.Context) error
}
