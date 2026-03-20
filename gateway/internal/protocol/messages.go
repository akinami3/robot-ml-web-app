// =============================================================================
// Step 2: 構造化メッセージ — メッセージ型定義
// =============================================================================
//
// 【このファイルの概要】
// WebSocket で送受信するメッセージの「型」を定義するファイルです。
// Step 1 では単なるテキスト文字列を送受信していましたが、
// Step 2 では「種類」「送信元」「データ本体」を持つ**構造化メッセージ**に進化させます。
//
// 【なぜ構造化するの？】
// テキスト文字列だけでは、メッセージの意味をプログラムが判断しにくい。
// 例: "forward" が移動コマンドなのか、チャットメッセージなのか区別できない。
// 構造化すると:
//
//	{ "type": "velocity_cmd", "payload": { "linear_x": 0.5 } }
//
// → 「移動コマンドで、前に 0.5 m/s」と明確になる。
//
// 【パッケージとは？】
// Go では、関連するコードを「パッケージ」にまとめます。
// protocol パッケージ = メッセージの定義とシリアライゼーションを担当。
// 他のパッケージからは protocol.Message のように使えます。
//
// =============================================================================
package protocol

import "time"

// =============================================================================
// MessageType — メッセージの種類を表す型
// =============================================================================
//
// 【型エイリアスとは？】
// type MessageType string は、string 型に「MessageType」という別名を付けるもの。
// ただの string と同じだが、意味を明確にし、間違った値を使いにくくする。
// TypeScript の type MessageType = "velocity_cmd" | "sensor_data" に近い概念。
//
// 【なぜ定数にするの？】
// 文字列を直接使うと、タイプミスに気付けない（"velociy_cmd" → バグ）。
// 定数にすれば、コンパイル時に間違いを検出できる。
type MessageType string

const (
	// クライアント → サーバー: ロボットの速度を指示するコマンド
	// linear_x (前後), linear_y (左右), angular_z (回転) を含む
	TypeVelocityCmd MessageType = "velocity_cmd"

	// サーバー → クライアント: ロボットのセンサーデータ
	// 温度、バッテリー、速度などを含む
	TypeSensorData MessageType = "sensor_data"

	// サーバー → クライアント: コマンドに対する応答確認
	// "received" / "executing" / "completed" などのステータスを含む
	TypeCommandAck MessageType = "command_ack"

	// サーバー → クライアント: エラー通知
	TypeError MessageType = "error"
)

// =============================================================================
// Message — すべてのメッセージが共通して持つ「封筒」
// =============================================================================
//
// 【Go の構造体（struct）とは？】
// 複数の値をひとまとめにしたデータ型。
// JavaScript のオブジェクト { type: "...", robotId: "..." } に相当。
// ただし Go の struct は「どんなフィールドがあるか」が事前に決まっている（型安全）。
//
// 【json タグとは？】
// `json:"type"` は、JSON に変換する時のフィールド名を指定するタグ。
// Go の慣例ではフィールド名は PascalCase（Type）だが、
// JSON の慣例では snake_case（type）や camelCase を使う。
// タグがないと JSON のキー名が "Type" になってしまう（JavaScript 側で使いにくい）。
//
// 【omitempty とは？】
// `json:"robot_id,omitempty"` — 値がゼロ値（空文字列など）の場合、
// JSON出力時にそのフィールドを省略する。
// 省略したい理由: エラーメッセージには robot_id が不要な場合がある。
//
// 【json.RawMessage とは？】
// Payload の型に使っている。「中身は後で解釈する、まずはそのまま保持する」JSON データ。
// メッセージの Type によって Payload の構造が異なるため、
// 最初は生のJSONバイト列として受け取り、Type を見てから適切な型にデコードする。
// これを「遅延デコード（lazy decoding）」と呼ぶ。
type Message struct {
	Type      MessageType `json:"type"`               // メッセージの種類
	RobotID   string      `json:"robot_id,omitempty"` // ロボットの識別子
	Timestamp time.Time   `json:"timestamp"`          // メッセージの送信時刻
	Payload   interface{} `json:"payload"`            // メッセージ本体（型はTypeによって異なる）
}

// =============================================================================
// VelocityPayload — velocity_cmd のペイロード（データ本体）
// =============================================================================
//
// 【ロボットの速度コマンドについて】
// ロボットの動きは以下の3軸で表現します。
// これは ROS (Robot Operating System) の geometry_msgs/Twist に対応しています。
//
//	LinearX  (前後)    : 正 = 前進、負 = 後退     単位: m/s
//	LinearY  (左右)    : 正 = 左、負 = 右          単位: m/s
//	AngularZ (回転)    : 正 = 左旋回、負 = 右旋回  単位: rad/s
//
//	     前進 (+X)
//	       ▲
//	       |
//	左(+Y) ← → 右(-Y)
//	       |
//	       ▼
//	     後退 (-X)
//
//	左旋回(+Z) ↺    ↻ 右旋回(-Z)
type VelocityPayload struct {
	LinearX  float64 `json:"linear_x"`  // 前後方向の速度 (m/s)
	LinearY  float64 `json:"linear_y"`  // 左右方向の速度 (m/s)
	AngularZ float64 `json:"angular_z"` // 回転速度 (rad/s)
}

// =============================================================================
// SensorPayload — sensor_data のペイロード
// =============================================================================
//
// 【センサーデータの構造】
// ロボットが持つ各種センサーの値をまとめたもの。
// Step 1 では文字列で送っていたが、構造体にすることで:
// - フロントエンドで個別の値にアクセスしやすい（data.payload.temperature）
// - バリデーション（値の検証）がしやすい
// - 将来的な拡張がしやすい（新しいフィールドを追加するだけ）
type SensorPayload struct {
	Temperature float64 `json:"temperature"` // 温度 (°C)
	Battery     float64 `json:"battery"`     // バッテリー残量 (%)
	Speed       float64 `json:"speed"`       // 現在の速度 (m/s)
	Distance    float64 `json:"distance"`    // 障害物までの距離 (m) — 新規追加
}

// =============================================================================
// CommandAckPayload — command_ack のペイロード
// =============================================================================
//
// 【コマンド応答の意味】
// ロボットにコマンドを送った後、そのコマンドがどうなったか知る必要がある。
// Status のパターン:
//
//	"received"   — サーバーがコマンドを受け取った
//	"executing"  — コマンド実行中
//	"completed"  — コマンド完了
//	"rejected"   — コマンドを拒否した（安全制限など）
type CommandAckPayload struct {
	Status      string `json:"status"`                // 処理状態
	Description string `json:"description,omitempty"` // 状態の説明
}

// =============================================================================
// ErrorPayload — error のペイロード
// =============================================================================
type ErrorPayload struct {
	Code    int    `json:"code"`    // エラーコード
	Message string `json:"message"` // エラーメッセージ
}

// =============================================================================
// NewVelocityCmd — velocity_cmd メッセージを簡単に作成するヘルパー関数
// =============================================================================
//
// 【ファクトリ関数とは？】
// オブジェクトの生成を簡略化する関数。New〇〇 という命名が Go の慣例。
// Python の __init__、JavaScript の constructor に相当するが、
// Go にはクラスがないため、通常の関数として定義する。
//
// 【引数の型: float64】
// Go の浮動小数点数型。JavaScript の number、Python の float に相当。
// 64ビットの精度を持つ。
func NewVelocityCmd(robotID string, linearX, linearY, angularZ float64) Message {
	return Message{
		Type:      TypeVelocityCmd,
		RobotID:   robotID,
		Timestamp: time.Now(),
		Payload: VelocityPayload{
			LinearX:  linearX,
			LinearY:  linearY,
			AngularZ: angularZ,
		},
	}
}

// =============================================================================
// NewSensorData — sensor_data メッセージを作成するヘルパー関数
// =============================================================================
func NewSensorData(robotID string, temp, battery, speed, distance float64) Message {
	return Message{
		Type:      TypeSensorData,
		RobotID:   robotID,
		Timestamp: time.Now(),
		Payload: SensorPayload{
			Temperature: temp,
			Battery:     battery,
			Speed:       speed,
			Distance:    distance,
		},
	}
}

// =============================================================================
// NewCommandAck — command_ack メッセージを作成するヘルパー関数
// =============================================================================
func NewCommandAck(robotID, status, description string) Message {
	return Message{
		Type:      TypeCommandAck,
		RobotID:   robotID,
		Timestamp: time.Now(),
		Payload: CommandAckPayload{
			Status:      status,
			Description: description,
		},
	}
}

// =============================================================================
// NewError — error メッセージを作成するヘルパー関数
// =============================================================================
func NewError(code int, message string) Message {
	return Message{
		Type:      TypeError,
		Timestamp: time.Now(),
		Payload: ErrorPayload{
			Code:    code,
			Message: message,
		},
	}
}
