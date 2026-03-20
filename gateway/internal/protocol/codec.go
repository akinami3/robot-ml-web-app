// =============================================================================
// Step 2: 構造化メッセージ — エンコード・デコード（コーデック）
// =============================================================================
//
// 【このファイルの概要】
// メッセージを「送信できる形式」に変換（エンコード）したり、
// 「受信した形式」からGoの構造体に戻す（デコード）するファイルです。
//
// 【シリアライゼーションとは？】
// プログラム内のデータ（構造体やオブジェクト）を、
// ネットワークで送信できるバイト列に変換すること。
//
//	Go の構造体 → JSON 文字列（エンコード / マーシャリング）
//	JSON 文字列 → Go の構造体（デコード / アンマーシャリング）
//
// 【JSON vs MessagePack】
// ┌──────────────┬───────────────────────────────────────┐
// │              │  JSON              │ MessagePack      │
// ├──────────────┼───────────────────────────────────────┤
// │ 形式         │ テキスト           │ バイナリ          │
// │ 可読性       │ ◎ 人間が読める    │ ✗ 読めない         │
// │ サイズ       │ △ 大きい          │ ◎ 小さい          │
// │ 速度         │ △ 普通            │ ◎ 高速            │
// │ デバッグ     │ ◎ DevToolsで確認  │ △ ツールが必要     │
// │ ブラウザ対応 │ ◎ 標準サポート    │ △ ライブラリ必要   │
// └──────────────┴───────────────────────────────────────┘
//
// Step 2 では JSON を使います（デバッグしやすいため）。
// Step 3 以降で MessagePack（バイナリ形式）に対応します。
//
// =============================================================================
package protocol

import (
	"encoding/json"
	"fmt"
	"time"
)

// =============================================================================
// Codec — メッセージのエンコード・デコードを行うインターフェース
// =============================================================================
//
// 【インターフェースとは？】
// 「この関数を持っていれば、この型として扱える」という約束事。
// Java の interface、TypeScript の interface に近い概念。
//
// なぜインターフェースにするのか？
// → 将来 MessagePack に切り替えても、このインターフェースを満たせばOK。
//
//	呼び出し側のコードを変更する必要がない（= 依存関係の逆転）。
//
// 【Go のインターフェースの特徴】
// Java と違い、「implements」キーワードは不要。
// 必要なメソッドを持っていれば、自動的にそのインターフェースを満たす。
// これを「暗黙的インターフェース実装（implicit implementation）」と呼ぶ。
type Codec interface {
	// Encode はメッセージをバイト列に変換する
	Encode(msg Message) ([]byte, error)
	// Decode はバイト列をメッセージに変換する
	Decode(data []byte) (Message, error)
}

// =============================================================================
// JSONCodec — JSON 形式のコーデック
// =============================================================================
//
// 【空の構造体 struct{} とは？】
// フィールドを持たない構造体。メモリを消費しない。
// メソッドを持たせるための「台座」として使う。
// JSONCodec 自体にはデータがないが、Encode/Decode メソッドの「所有者」になる。
type JSONCodec struct{}

// NewJSONCodec は JSONCodec を生成するファクトリ関数。
// 返り値の型が Codec インターフェースであることに注目。
// → JSONCodec は Codec インターフェースを満たしている（Encode, Decode を持つ）
func NewJSONCodec() Codec {
	return &JSONCodec{}
}

// =============================================================================
// Encode — Message → JSON バイト列
// =============================================================================
//
// 【メソッドとは？】
// func (jc *JSONCodec) Encode(...) の (jc *JSONCodec) 部分は「レシーバー」。
// これにより Encode は JSONCodec の「メソッド」になる。
// JavaScript では class のメソッド、Python では self を受け取るメソッドに相当。
//
// 【json.Marshal とは？】
// Go の構造体を JSON バイト列に変換する標準ライブラリ関数。
// JavaScript の JSON.stringify() に相当。
//
// 例:
//
//	msg := Message{Type: "velocity_cmd", Payload: VelocityPayload{LinearX: 0.5}}
//	bytes, _ := json.Marshal(msg)
//	// → {"type":"velocity_cmd","payload":{"linear_x":0.5}}
//
// 【多値戻り値 ([]byte, error)】
// Go では「結果」と「エラー」を同時に返すのが慣例。
// 成功時: (データ, nil)
// 失敗時: (nil, エラー)
func (jc *JSONCodec) Encode(msg Message) ([]byte, error) {
	data, err := json.Marshal(msg)
	if err != nil {
		return nil, fmt.Errorf("JSON エンコードエラー: %w", err)
	}
	return data, nil
}

// =============================================================================
// Decode — JSON バイト列 → Message
// =============================================================================
//
// 【json.Unmarshal とは？】
// JSON バイト列を Go の構造体に変換する標準ライブラリ関数。
// JavaScript の JSON.parse() に相当。
//
// 【&msg の & とは？（ポインタ）】
// & はアドレス演算子。変数のメモリアドレスを取得する。
// json.Unmarshal は「渡されたポインタの先にデータを書き込む」仕組み。
// ポインタを渡さないと、コピーに書き込まれて元の変数が更新されない。
//
// 【デコードの2段階処理】
// Message.Payload は interface{} 型なので、json.Unmarshal は
// デフォルトで map[string]interface{} にデコードする。
// 1回目: JSON → Message（Payload は map[string]interface{} のまま）
// 2回目: Message.Type を見て、Payload を適切な型にデコードする
//
// この2段階処理が必要な理由:
// velocity_cmd なら VelocityPayload に、sensor_data なら SensorPayload に、
// と Type によって Payload の型が異なるため。
func (jc *JSONCodec) Decode(data []byte) (Message, error) {
	// --- 第1段階: 外側の Message 構造を解析 ---
	// rawPayload で Payload 部分を生の JSON のまま保持する
	var raw struct {
		Type      MessageType     `json:"type"`
		RobotID   string          `json:"robot_id,omitempty"`
		Timestamp string          `json:"timestamp"`
		Payload   json.RawMessage `json:"payload"`
	}

	if err := json.Unmarshal(data, &raw); err != nil {
		return Message{}, fmt.Errorf("JSON デコードエラー（外側）: %w", err)
	}

	// --- 第2段階: Type に応じて Payload を適切な型にデコード ---
	//
	// 【switch 文 + 型に応じた分岐】
	// Type の値を見て、Payload をどの構造体にデコードするか決める。
	// これは「メッセージディスパッチ」のパターンとも呼ばれる。
	msg := Message{
		Type:    raw.Type,
		RobotID: raw.RobotID,
	}

	// タイムスタンプの解析（クライアントから来ない場合もあるので、エラーは無視）
	// 【time.Parse とは？】
	// 文字列を time.Time 型に変換する関数。
	// time.RFC3339 は "2006-01-02T15:04:05Z07:00" 形式（ISO 8601）。
	// Go の時刻フォーマットは独特で、基準時刻（2006年1月2日...）の配置で指定する。
	if t, err := parseTimestamp(raw.Timestamp); err == nil {
		msg.Timestamp = t
	}

	switch raw.Type {
	case TypeVelocityCmd:
		var payload VelocityPayload
		if err := json.Unmarshal(raw.Payload, &payload); err != nil {
			return Message{}, fmt.Errorf("velocity_cmd ペイロードのデコードエラー: %w", err)
		}
		msg.Payload = payload

	case TypeSensorData:
		var payload SensorPayload
		if err := json.Unmarshal(raw.Payload, &payload); err != nil {
			return Message{}, fmt.Errorf("sensor_data ペイロードのデコードエラー: %w", err)
		}
		msg.Payload = payload

	case TypeCommandAck:
		var payload CommandAckPayload
		if err := json.Unmarshal(raw.Payload, &payload); err != nil {
			return Message{}, fmt.Errorf("command_ack ペイロードのデコードエラー: %w", err)
		}
		msg.Payload = payload

	case TypeError:
		var payload ErrorPayload
		if err := json.Unmarshal(raw.Payload, &payload); err != nil {
			return Message{}, fmt.Errorf("error ペイロードのデコードエラー: %w", err)
		}
		msg.Payload = payload

	default:
		return Message{}, fmt.Errorf("不明なメッセージタイプ: %s", raw.Type)
	}

	return msg, nil
}

// =============================================================================
// parseTimestamp — タイムスタンプ文字列をパースするヘルパー
// =============================================================================
//
// 【複数のフォーマットに対応する理由】
// クライアント（JavaScript）の toISOString() は "2024-01-01T00:00:00.000Z" 形式、
// Go の time.Now() は "2024-01-01T00:00:00+09:00" 形式、
// と環境によってフォーマットが異なる場合がある。
// 複数のフォーマットを順に試すことで、柔軟に対応する。
// parseTimestamp は複数の時刻フォーマットを試みてパースする
func parseTimestamp(s string) (time.Time, error) {
	// 試すフォーマットのリスト
	formats := []string{
		time.RFC3339Nano, // "2006-01-02T15:04:05.999999999Z07:00"
		time.RFC3339,     // "2006-01-02T15:04:05Z07:00"
	}

	for _, format := range formats {
		if t, err := time.Parse(format, s); err == nil {
			return t, nil
		}
	}

	return time.Time{}, fmt.Errorf("タイムスタンプのパースに失敗: %s", s)
}
