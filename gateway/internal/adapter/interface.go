// =============================================================================
// ファイル: interface.go
// パッケージ: adapter（アダプターパッケージ）
//
// 【このファイルの概要】
// ロボットアダプターの「インターフェース（interface）」と
// 共通のデータ型（struct）を定義するファイルです。
//
// 【アダプターパターン（Adapter Pattern）とは？】
// 異なる種類のロボット（ROS2、MQTT、gRPC、模擬ロボットなど）を
// 同じインターフェースで操作できるようにする設計パターンです。
//
// 例えば：
// - ROS2ロボット: ROS2プロトコルで通信する
// - MQTTロボット: MQTTプロトコルで通信する
// - Mockロボット: 実際のロボットなしでテストする
//
// これらはすべて RobotAdapter インターフェースを実装するので、
// 呼び出し側は「どの種類のロボットか」を気にせず同じ方法で操作できます。
//
// 【プラグインパターン（Plugin Pattern）との関連】
// このインターフェースは「プラグインパターン」も実現しています。
// 新しい種類のロボットを追加する時：
// 1. 新しいパッケージを作る（例: internal/adapter/mqtt/）
// 2. RobotAdapter インターフェースを実装する
// 3. Registry に登録する
// → 既存のコードを変更せずに新しいロボットに対応できます！
//
// これは「オープン・クローズドの原則（Open-Closed Principle）」と呼ばれ、
// 「拡張に対して開いていて、修正に対して閉じている」設計を実現します。
// =============================================================================
package adapter

import (
	// context: コンテキスト管理パッケージ
	// ロボットとの接続・切断・コマンド送信などの操作に
	// タイムアウトやキャンセルの制御を提供します。
	//
	// 【なぜコンテキストが必要？】
	// ロボットとの通信はネットワーク経由なので、応答が来ない可能性があります。
	// コンテキストを使うことで「5秒以内に応答がなければキャンセル」などの
	// 制御を各メソッドに統一的に提供できます。
	"context"
)

// =============================================================================
// SensorData - センサーデータを表す構造体
// =============================================================================
//
// 【この構造体の役割】
// 様々な種類のセンサー（カメラ、LiDAR、IMU、エンコーダなど）からの
// データを統一的な形式で表現します。
//
// 【なぜ統一的な形式が必要？】
// 各ロボットのセンサーデータの形式はバラバラです。
// 統一形式にすることで、受信側は「どのロボットのどのセンサーか」を
// 気にせずデータを処理できます。
type SensorData struct {
	// RobotID: データを送信したロボットのID
	// どのロボットからのデータかを識別するために使います。
	RobotID string

	// Topic: センサーデータのトピック名
	// ROS2の「トピック」に由来する概念です。
	// 例: "/camera/image", "/lidar/scan", "/odom"
	// データの種類を識別するために使います。
	Topic string

	// DataType: データの型
	// 例: "sensor_msgs/Image", "sensor_msgs/LaserScan", "nav_msgs/Odometry"
	// データをどう解釈するかを示します。
	DataType string

	// FrameID: 座標フレームのID
	// ロボットのどの部分のセンサーかを示します。
	// 例: "base_link"（本体）、"camera_link"（カメラ）、"lidar_link"（LiDAR）
	FrameID string

	// Timestamp: データのタイムスタンプ（Unix時間、ナノ秒）
	// int64型: 64ビット整数（非常に大きな数を扱える）
	// Unix時間: 1970年1月1日からの経過時間
	Timestamp int64

	// Data: センサーデータの本体
	// map[string]any: キーが文字列、値が任意の型のmap
	//
	// 【any（interface{}）を使う理由】
	// センサーの種類によってデータの形式が全く異なります：
	// - カメラ: {"width": 640, "height": 480, "data": [...バイト配列...]}
	// - LiDAR: {"ranges": [1.5, 2.3, 0.8, ...], "angle_min": -3.14}
	// - IMU: {"linear_acceleration": {"x": 0.0, "y": 0.0, "z": 9.8}}
	//
	// any を使うことで、あらゆる種類のデータを1つの型で扱えます。
	// ただし、使う時に型アサーション（type assertion）が必要です：
	//
	//	width := data["width"].(int)  // any → int に変換
	Data map[string]any
}

// =============================================================================
// Command - ロボットへのコマンドを表す構造体
// =============================================================================
//
// 【この構造体の役割】
// ユーザーからロボットへのコマンド（命令）を統一的な形式で表現します。
//
// 【コマンドの例】
//
//  1. 速度コマンド:
//     Type: "velocity", Payload: {"linear_x": 1.0, "angular_z": 0.5}
//
//  2. ナビゲーションコマンド:
//     Type: "navigate", Payload: {"goal_x": 5.0, "goal_y": 3.0}
//
//  3. 緊急停止コマンド:
//     Type: "estop", Payload: {}
type Command struct {
	// RobotID: コマンド送信先のロボットID
	RobotID string

	// Type: コマンドの種類
	// 例: "velocity"（速度指令）, "navigate"（目標地点へ移動）, "estop"（緊急停止）
	Type string

	// Payload: コマンドの具体的なデータ
	// コマンドの種類によって中身が変わるため、map[string]any を使います。
	Payload map[string]any

	// Timestamp: コマンドの送信時刻（Unix時間）
	Timestamp int64
}

// =============================================================================
// Capabilities - ロボットの能力を記述する構造体
// =============================================================================
//
// 【この構造体の役割】
// ロボットが「何ができるか」を記述します。
// UIは、この情報を使って利用可能な機能だけを表示できます。
//
// 例えば：
// - SupportsNavigation が false なら、ナビゲーションボタンを非表示にする
// - MaxLinearVelocity が 0.5 なら、速度スライダーの最大値を0.5にする
//
// 【構造体タグ（struct tag）とは？】
// `json:"supports_velocity_control"` の部分は「構造体タグ」です。
// JSONに変換する時のフィールド名を指定します。
//
// Goの慣例: フィールド名はCamelCase（例: SupportsVelocityControl）
// JSONの慣例: フィールド名はsnake_case（例: supports_velocity_control）
//
// 構造体タグにより、この変換を自動的に行えます。
type Capabilities struct {
	// SupportsVelocityControl: 速度制御に対応しているか
	// 例: 車輪型ロボットは対応、固定型カメラは非対応
	SupportsVelocityControl bool `json:"supports_velocity_control"`

	// SupportsNavigation: 自律ナビゲーションに対応しているか
	// 例: SLAM搭載ロボットは対応、簡易リモコンロボットは非対応
	SupportsNavigation bool `json:"supports_navigation"`

	// SupportsEStop: 緊急停止に対応しているか
	// ほとんどのロボットは対応すべきですが、
	// 一部のセンサー専用デバイスは非対応かもしれません。
	SupportsEStop bool `json:"supports_estop"`

	// SensorTopics: このロボットが提供するセンサートピックのリスト
	// 例: ["/camera/image", "/lidar/scan", "/odom"]
	//
	// []string: string型のスライス（可変長配列）
	SensorTopics []string `json:"sensor_topics"`

	// MaxLinearVelocity: 最大直進速度（m/s）
	MaxLinearVelocity float64 `json:"max_linear_velocity"`

	// MaxAngularVelocity: 最大回転速度（rad/s）
	MaxAngularVelocity float64 `json:"max_angular_velocity"`
}

// =============================================================================
// RobotAdapter - ロボットアダプターインターフェース
// =============================================================================
//
// 【インターフェース（interface）とは？】
// インターフェースは「メソッドの契約書」です。
// 「このインターフェースを満たすには、これらのメソッドを実装してください」
// という仕様を定義します。
//
// 【Goのインターフェースの特徴（暗黙的実装）】
// Goのインターフェースは「暗黙的（implicit）」に実装されます。
// Java の implements や Python の ABC と違い、
// 「このインターフェースを実装します」と宣言する必要がありません。
// 必要なメソッドがすべて揃っていれば、自動的にインターフェースを満たします。
//
// 例えば：
//
//	type MockAdapter struct { ... }
//	func (m *MockAdapter) Name() string { return "mock" }
//	func (m *MockAdapter) Connect(ctx context.Context, config map[string]any) error { ... }
//	... 他のメソッドも実装 ...
//	// → MockAdapter は自動的に RobotAdapter インターフェースを満たす！
//
// 【このインターフェースを使う利点】
// 1. テスト可能性: MockAdapter を作れば、実ロボットなしでテストできる
// 2. 拡張性: 新しいロボットタイプを追加しても、既存コードは変更不要
// 3. 疎結合: 呼び出し側はインターフェースだけ知っていればよい
//
// 【新しいロボットタイプの追加手順】
// 1. 新しいパッケージを作る（例: internal/adapter/mqtt/）
// 2. RobotAdapter インターフェースのすべてのメソッドを実装する
// 3. AdapterRegistry にファクトリ関数を登録する
type RobotAdapter interface {
	// Name: アダプターの名前を返す
	// 例: "ros2", "mqtt", "grpc", "mock"
	// ロギングやデバッグで使います。
	//
	// 【インターフェースのメソッドシグネチャ】
	// インターフェース内では、メソッドの「シグネチャ（署名）」だけを定義します。
	// 実装（中身のコード）は書きません。
	// 実装は、このインターフェースを満たす各構造体が行います。
	Name() string

	// Connect: ロボットとの接続を確立する
	// 引数:
	//   - ctx: コンテキスト（タイムアウト・キャンセル制御用）
	//   - config: 接続設定（map形式で柔軟に設定を渡す）
	//     例: {"host": "192.168.1.100", "port": 9090, "protocol": "ws"}
	//
	// 戻り値:
	// - error: 接続失敗時のエラー、成功時は nil
	Connect(ctx context.Context, config map[string]any) error

	// Disconnect: ロボットとの接続を切断する
	// リソースの解放（ソケットのクローズなど）を行います。
	// 引数:
	// - ctx: コンテキスト
	// 戻り値:
	// - error: 切断時のエラー
	Disconnect(ctx context.Context) error

	// IsConnected: 現在接続されているかどうかを返す
	// UIでの接続状態表示や、コマンド送信前の確認に使います。
	// 戻り値:
	// - bool: true = 接続中, false = 未接続
	IsConnected() bool

	// SendCommand: ロボットにコマンドを送信する
	// 速度指令、ナビゲーション目標などのコマンドを送ります。
	// 引数:
	// - ctx: コンテキスト
	// - cmd: 送信するコマンド（Command構造体）
	// 戻り値:
	// - error: 送信失敗時のエラー
	SendCommand(ctx context.Context, cmd Command) error

	// SensorDataChannel: センサーデータを受信するチャネルを返す
	//
	// 【チャネル（channel）とは？】
	// チャネルはゴルーチン間でデータを安全にやり取りするための「パイプ」です。
	//
	// <-chan SensorData は「受信専用チャネル」を意味します：
	// - <-chan: このチャネルからはデータを受け取ることしかできない
	// - chan<-: このチャネルにはデータを送ることしかできない
	// - chan: 送受信どちらもできる
	//
	// 受信専用にすることで、呼び出し側がうっかりデータを送信するのを防ぎます。
	//
	// 使い方の例：
	//
	//	ch := adapter.SensorDataChannel()
	//	for data := range ch {
	//	    // 新しいセンサーデータが来るたびにこのループが実行される
	//	    fmt.Println(data.Topic, data.Data)
	//	}
	SensorDataChannel() <-chan SensorData

	// GetCapabilities: ロボットがサポートする機能を返す
	// UIは、この情報に基づいて表示する機能を切り替えます。
	// 戻り値:
	// - Capabilities: ロボットの能力情報
	GetCapabilities() Capabilities

	// EmergencyStop: 緊急停止を実行する
	// すべてのモーターを即座に停止させます。
	// 安全上、最も重要なメソッドです。
	// 引数:
	// - ctx: コンテキスト
	// 戻り値:
	// - error: 緊急停止の実行に失敗した場合のエラー
	EmergencyStop(ctx context.Context) error
}
