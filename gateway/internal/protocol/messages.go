// =============================================================================
// ファイル: messages.go（メッセージ定義）
// 概要: WebSocket通信で使用するメッセージの型とペイロード（データ本体）を定義
//
// このファイルは、ゲートウェイとクライアント（ブラウザ）間で
// やり取りされるメッセージの「形」を定義しています。
//
// 【通信の流れ】
//   クライアント（ブラウザ）  ←→  ゲートウェイ（このサーバー）  ←→  ロボット
//
// 【メッセージの構造: エンベロープ（封筒）パターン】
//   全てのメッセージは共通の「封筒」（Message構造体）に入れて送受信する。
//   封筒には以下の情報が含まれる：
//   - Type: メッセージの種類（速度コマンド、センサーデータなど）
//   - RobotID: どのロボットに関するメッセージか
//   - Timestamp: いつ作成されたか
//   - Payload: 実際のデータ（メッセージの種類ごとに異なる）
//
// 【Go言語の知識: 構造体タグ（Struct Tags）とシリアライズ】
//   Go の構造体フィールドには「タグ」を付けることができる。
//   `msgpack:"type" json:"type"` のように複数のタグを並べて書く。
//   - msgpack タグ: MessagePack 形式でのフィールド名を指定
//   - json タグ: JSON 形式でのフィールド名を指定
//   - omitempty: 値がゼロ値の場合、そのフィールドを省略する
// =============================================================================
package protocol

import (
// time: 時間に関する操作を提供する標準ライブラリ。
// time.Now().UnixMilli() でミリ秒精度のタイムスタンプを取得。
"time"
)

// =============================================================================
// MessageType: メッセージの種類を表す型
//
// 【Go言語の知識: 型エイリアス / カスタム型】
//   type MessageType string は、string をベースにした新しい型を作成する。
//   これにより：
//   - 型安全性が向上する（普通の string と混同しない）
//   - この型にメソッドを追加できる
//   - コードの意図が明確になる（ただの string ではなく「メッセージの種類」）
//
// 【Go言語の知識: 定数（const）】
//   const ブロック内で定数を定義。
//   定数はコンパイル時に決まる値で、実行中に変更できない。
//   Go には enum（列挙型）がないため、const でメッセージタイプを定義するのが一般的。
// =============================================================================
type MessageType string

const (
// --- クライアント → ゲートウェイ 方向のメッセージ ---
// これらはブラウザからサーバーに送信されるメッセージの種類。

// MsgTypeAuth: 認証メッセージ。JWT トークンを送って自分の身元を証明する。
MsgTypeAuth              MessageType = "auth"

// MsgTypeVelocityCommand: 速度コマンド。ロボットの移動速度を指定する。
// 直線速度（linear_x, linear_y）と回転速度（angular_z）を含む。
MsgTypeVelocityCommand   MessageType = "velocity_cmd"

// MsgTypeNavigationGoal: ナビゲーション目標。ロボットに目的地を指定する。
// 座標（x, y, z）と向き（orientation）を含む。
MsgTypeNavigationGoal    MessageType = "nav_goal"

// MsgTypeNavigationCancel: ナビゲーションキャンセル。移動中のロボットを停止。
MsgTypeNavigationCancel  MessageType = "nav_cancel"

// MsgTypeEmergencyStop: 緊急停止（E-Stop）。ロボットの全動作を即座に停止。
// 安全上最も重要なコマンド。
MsgTypeEmergencyStop     MessageType = "estop"

// MsgTypeOperationLock: 操作ロック。自分だけがロボットを操作できるようにする。
MsgTypeOperationLock     MessageType = "op_lock"

// MsgTypeOperationUnlock: 操作ロック解除。他のユーザーも操作可能にする。
MsgTypeOperationUnlock   MessageType = "op_unlock"

// MsgTypePing: 生存確認（Ping）。接続が生きているかの確認メッセージ。
// サーバーは Pong で応答する（WebSocket のキープアライブ機構）。
MsgTypePing              MessageType = "ping"

// --- ゲートウェイ → クライアント 方向のメッセージ ---
// これらはサーバーからブラウザに送信されるメッセージの種類。

// MsgTypeSensorData: センサーデータ。ロボットのセンサー情報をリアルタイムで配信。
// LiDAR、カメラ、IMU（慣性計測装置）などのデータを含む。
MsgTypeSensorData        MessageType = "sensor_data"

// MsgTypeRobotStatus: ロボットの状態。バッテリー残量、接続状態など。
MsgTypeRobotStatus       MessageType = "robot_status"

// MsgTypeCommandAck: コマンド応答確認（ACK = Acknowledgement）。
// クライアントからのコマンドを受け取ったことを確認する。
MsgTypeCommandAck        MessageType = "cmd_ack"

// MsgTypeLockStatus: ロック状態の通知。誰がロボットをロックしているかを通知。
MsgTypeLockStatus        MessageType = "lock_status"

// MsgTypeConnectionStatus: 接続状態の通知。ロボットの接続・切断を通知。
MsgTypeConnectionStatus  MessageType = "conn_status"

// MsgTypeError: エラー通知。処理中にエラーが発生したことをクライアントに通知。
MsgTypeError             MessageType = "error"

// MsgTypePong: Ping への応答。接続が生きていることを確認する。
MsgTypePong              MessageType = "pong"

// MsgTypeSafetyAlert: 安全警告。速度制限違反や緊急停止の通知。
MsgTypeSafetyAlert       MessageType = "safety_alert"
)

// =============================================================================
// Message: WebSocketメッセージの統一エンベロープ（封筒）構造体
//
// 全てのメッセージはこの構造体に格納されて送受信される。
// Type フィールドでメッセージの種類を判別し、Payload に実際のデータが入る。
//
// 【Go言語の知識: 構造体タグ（Struct Tags）の書き方】
//   `msgpack:"type" json:"type"` のように書く。
//   - msgpack:"type" : MessagePack でのフィールド名は "type"
//   - json:"type"    : JSON でのフィールド名は "type"
//   - omitempty      : 値がゼロ値（空文字列、0、nil等）の場合、出力しない
//     例: Topic が空文字列なら、JSON/MessagePack 出力から省略される
//     これによりデータサイズを削減できる。
//
// 【Go言語の知識: map[string]any 型】
//   any は Go 1.18 で追加された interface{} のエイリアス。
//   map[string]any は「文字列キー → 任意の値」のマップ（辞書）。
//   Payload にはメッセージの種類に応じて異なるデータが入るため、
//   柔軟な any 型を使用している。
// =============================================================================
type Message struct {
Type      MessageType    `msgpack:"type" json:"type"`                             // メッセージの種類（必須）
Topic     string         `msgpack:"topic,omitempty" json:"topic,omitempty"`        // トピック名（センサーデータの分類に使用）
RobotID   string         `msgpack:"robot_id,omitempty" json:"robot_id,omitempty"` // ロボットの識別子
UserID    string         `msgpack:"user_id,omitempty" json:"user_id,omitempty"`   // ユーザーの識別子
Timestamp int64          `msgpack:"ts" json:"ts"`                                  // タイムスタンプ（ミリ秒）
Payload   map[string]any `msgpack:"payload,omitempty" json:"payload,omitempty"`   // メッセージ本体データ
Error     string         `msgpack:"error,omitempty" json:"error,omitempty"`        // エラーメッセージ（エラー時のみ使用）
}

// =============================================================================
// NewMessage: 新しいメッセージを作成するコンストラクタ関数
//
// 現在のタイムスタンプ（ミリ秒）を自動設定し、空の Payload マップを初期化する。
//
// 【Go言語の知識: time.Now().UnixMilli()】
//   UnixMilli() は「1970年1月1日からの経過ミリ秒」を返す。
//   この形式はJavaScript側でも扱いやすい（new Date(timestamp) で変換可能）。
//   UnixNano() はナノ秒精度だが、WebSocket通信にはミリ秒で十分。
//
// 【Go言語の知識: make(map[string]any)】
//   make() でマップを初期化する。初期化しないとnilマップとなり、
//   値の代入時に panic（実行時エラー）が発生するため、必ず初期化する。
// =============================================================================
func NewMessage(msgType MessageType, robotID string) *Message {
return &Message{
Type:      msgType,
RobotID:   robotID,
Timestamp: time.Now().UnixMilli(), // 現在時刻のミリ秒タイムスタンプ
Payload:   make(map[string]any),   // 空のペイロードマップを初期化
}
}

// =============================================================================
// VelocityPayload: 速度コマンドのペイロード（データ本体）
//
// ロボットに送る移動指令の速度値を格納する。
// ロボット工学では一般的な座標系を使用：
//   - LinearX:  前後方向の速度（正: 前進、負: 後退）[m/s]
//   - LinearY:  左右方向の速度（正: 左、負: 右）[m/s] ※一部のロボットのみ対応
//   - AngularZ: 回転速度（正: 反時計回り、負: 時計回り）[rad/s]
//
// 【Go言語の知識: float64】
//   float64 は64ビット浮動小数点数で、小数を扱える。
//   物理量（速度、位置など）の表現に使用。
// =============================================================================
type VelocityPayload struct {
LinearX  float64 `msgpack:"linear_x" json:"linear_x"`   // X軸方向の直線速度 [m/s]
LinearY  float64 `msgpack:"linear_y" json:"linear_y"`   // Y軸方向の直線速度 [m/s]
AngularZ float64 `msgpack:"angular_z" json:"angular_z"` // Z軸周りの回転速度 [rad/s]
}

// =============================================================================
// NavigationGoalPayload: ナビゲーション目標のペイロード
//
// ロボットの自律移動の目的地を指定する。
// 位置（X, Y, Z）と向き（OrientationW）を含む。
//
// 【ロボット工学の知識: 座標系とクォータニオン】
//   X, Y, Z: 3D空間での位置座標（メートル単位）
//   OrientationW: クォータニオン（四元数）のW成分。ロボットの向きを表す。
//     簡単に言えば、目的地でどの方向を向いているかを指定する値。
//   FrameID: 座標系の基準フレーム（例: "map" = 地図座標系）
//   Tolerance: 許容誤差（この範囲内なら到着とみなす）
// =============================================================================
type NavigationGoalPayload struct {
X                    float64 `msgpack:"x" json:"x"`             // 目標X座標 [m]
Y                    float64 `msgpack:"y" json:"y"`             // 目標Y座標 [m]
Z                    float64 `msgpack:"z" json:"z"`             // 目標Z座標 [m]
OrientationW         float64 `msgpack:"ow" json:"ow"`           // 向き（クォータニオンW成分）
FrameID              string  `msgpack:"frame_id" json:"frame_id"` // 座標系フレームID
TolerancePosition    float64 `msgpack:"tol_pos" json:"tol_pos"` // 位置の許容誤差 [m]
ToleranceOrientation float64 `msgpack:"tol_ori" json:"tol_ori"` // 向きの許容誤差 [rad]
}

// =============================================================================
// EStopPayload: 緊急停止（E-Stop）のペイロード
//
// ロボットの緊急停止を起動/解除するためのデータ。
//   Activate: true で緊急停止を起動、false で解除
//   Reason: 緊急停止の理由（ログや通知に使用）
// =============================================================================
type EStopPayload struct {
Activate bool   `msgpack:"activate" json:"activate"` // true: 緊急停止起動、false: 解除
Reason   string `msgpack:"reason" json:"reason"`     // 緊急停止の理由
}

// =============================================================================
// SensorDataPayload: センサーデータのペイロード
//
// ロボットのセンサーから取得したデータを格納する。
//   DataType: データの種類（例: "lidar_scan", "imu", "camera"）
//   FrameID: センサーの座標フレーム（例: "laser_frame", "camera_frame"）
//   Data: 実際のセンサーデータ（種類に応じて異なる構造）
// =============================================================================
type SensorDataPayload struct {
DataType string         `msgpack:"data_type" json:"data_type"` // センサーデータの種類
FrameID  string         `msgpack:"frame_id" json:"frame_id"`   // 座標フレームID
Data     map[string]any `msgpack:"data" json:"data"`           // 実際のセンサーデータ
}

// =============================================================================
// AuthPayload: 認証のペイロード
//
// JWT（JSON Web Token）を送信してユーザー認証を行う。
// トークンには、ユーザーID、権限、有効期限などの情報が含まれる。
// =============================================================================
type AuthPayload struct {
Token string `msgpack:"token" json:"token"` // JWT認証トークン
}

// =============================================================================
// ConnectionStatusPayload: 接続状態のペイロード
//
// ロボットの接続状態の変化をクライアントに通知する。
//   RobotID: どのロボットの接続状態が変わったか
//   Connected: true = 接続中、false = 切断
//   Adapter: 使用しているアダプターの種類（例: "mock", "ros2"）
// =============================================================================
type ConnectionStatusPayload struct {
RobotID   string `msgpack:"robot_id" json:"robot_id"`     // ロボットの識別子
Connected bool   `msgpack:"connected" json:"connected"`   // 接続状態（true=接続中）
Adapter   string `msgpack:"adapter" json:"adapter"`       // アダプターの種類
}
