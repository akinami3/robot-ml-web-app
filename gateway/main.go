// =============================================================================
// Step 2: 構造化メッセージ — WebSocket サーバー
// =============================================================================
//
// 【Step 1 からの変更点】
// Step 1 では単なるテキスト文字列を送受信していましたが、
// Step 2 では構造化されたJSONメッセージを使います。
//
// 変更のポイント:
//   1. protocol パッケージを利用（メッセージの型定義 + エンコード/デコード）
//   2. クライアントから velocity_cmd メッセージを受信して処理
//   3. サーバーから sensor_data メッセージを JSON で送信
//   4. コマンド受信時に command_ack メッセージを返信
//
// 【パッケージのインポートパス】
// "gateway/protocol" は、go.mod の module 名 + ディレクトリ名。
// go.mod に module gateway と書いてあるので、
// gateway/protocol で protocol ディレクトリのパッケージを参照できる。
//
// =============================================================================
package main

import (
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"

	// 自作パッケージ: protocol
	// 【Go のパッケージ参照ルール】
	// "モジュール名/パッケージ名" でインポートする。
	// go.mod の module が "github.com/robot-ai-webapp/gateway" なので
	// "github.com/robot-ai-webapp/gateway/protocol" となる。
	"github.com/robot-ai-webapp/gateway/protocol"

	"github.com/gorilla/websocket"
)

// =============================================================================
// 定数の定義
// =============================================================================
const (
	port           = ":8080"
	sensorInterval = 1 * time.Second

	// デフォルトのロボットID
	// 将来的には複数ロボットに対応するが、今は固定値を使う
	defaultRobotID = "robot-01"
)

// =============================================================================
// グローバル変数
// =============================================================================
//
// 【コーデックの初期化】
// protocol.Codec インターフェースを満たす JSONCodec を生成。
// 将来 MessagePack に変えたい場合は、ここを NewMsgPackCodec() に差し替えるだけ。
// → これが「インターフェースによる依存関係の逆転」の効果。
var codec = protocol.NewJSONCodec()

// =============================================================================
// upgrader — HTTP → WebSocket のアップグレード設定
// =============================================================================
//
// 【Step 1 からの変更点】
// ReadBufferSize, WriteBufferSize を明示的に設定。
// JSON メッセージはテキスト文字列より大きくなる場合があるため、
// バッファサイズを適切に確保する。
//
// 【バッファ（buffer）とは？】
// データを一時的に蓄えるメモリ領域。
// 小さすぎると大きなメッセージを処理できない。
// 大きすぎるとメモリを無駄遣いする。
// 1024バイト = 1KB は、JSON メッセージには十分な大きさ。
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // 開発用: 全オリジン許可
	},
}

// =============================================================================
// main — エントリーポイント
// =============================================================================
func main() {
	http.HandleFunc("/ws", handleWebSocket)

	fmt.Println("🚀 WebSocket サーバー起動 (Step 2: 構造化メッセージ)")
	fmt.Println("   エンドポイント: ws://localhost" + port + "/ws")
	fmt.Println("   プロトコル: JSON")
	fmt.Println("   Ctrl+C で停止")

	log.Fatal(http.ListenAndServe(port, nil))
}

// =============================================================================
// handleWebSocket — WebSocket 接続のハンドラー
// =============================================================================
func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket アップグレード失敗:", err)
		return
	}
	defer conn.Close()

	log.Println("✅ 新しいクライアントが接続しました")

	done := make(chan struct{})
	go writePump(conn, done)
	readPump(conn, done)

	log.Println("❌ クライアントが切断しました")
}

// =============================================================================
// readPump — クライアントからの構造化メッセージを受信・処理
// =============================================================================
//
// 【Step 1 からの変更点】
// - テキスト文字列の代わりに JSON メッセージを受信
// - codec.Decode() で構造体にデシリアライズ
// - メッセージの Type に応じて異なる処理を実行
// - 応答も構造化メッセージ（command_ack）として返信
func readPump(conn *websocket.Conn, done chan struct{}) {
	defer close(done)

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Println("読み取りエラー:", err)
			return
		}

		// --- 受信したJSONをデコード ---
		// 【codec.Decode の流れ】
		// 1. JSON バイト列を受け取る
		//    例: {"type":"velocity_cmd","robot_id":"robot-01","payload":{"linear_x":0.5}}
		// 2. Message.Type を読み取る（"velocity_cmd"）
		// 3. Type に応じて Payload を正しい型にデコード
		//    → VelocityPayload{LinearX: 0.5}
		msg, err := codec.Decode(message)
		if err != nil {
			log.Println("⚠️ デコードエラー:", err)

			// エラーメッセージをクライアントに返す
			errMsg := protocol.NewError(400, fmt.Sprintf("メッセージの解析に失敗: %v", err))
			sendMessage(conn, errMsg)
			continue // 次のメッセージを待つ（return ではなく continue で切断しない）
		}

		log.Printf("📨 受信: type=%s, robot_id=%s", msg.Type, msg.RobotID)

		// --- メッセージの Type に応じた処理 ---
		//
		// 【Type-based dispatching（型ベースの振り分け）】
		// メッセージの Type フィールドを見て、適切なハンドラーに振り分ける設計パターン。
		// REST API のルーティング（/api/users → UserHandler）に似た概念。
		switch msg.Type {
		case protocol.TypeVelocityCmd:
			handleVelocityCmd(conn, msg)

		default:
			log.Printf("⚠️ 未対応のメッセージタイプ: %s", msg.Type)
			errMsg := protocol.NewError(404, fmt.Sprintf("未対応のメッセージタイプ: %s", msg.Type))
			sendMessage(conn, errMsg)
		}
	}
}

// =============================================================================
// handleVelocityCmd — velocity_cmd メッセージを処理
// =============================================================================
//
// 【型アサーション（Type Assertion）とは？】
// msg.Payload は interface{} 型（なんでも入る箱）だが、
// ここでは VelocityPayload が入っていることを「断言」して取り出す。
//
// payload, ok := msg.Payload.(protocol.VelocityPayload)
//   payload: 取り出した値（VelocityPayload 型）
//   ok:      成功したかどうか（bool）
//
// ok が false の場合、型が違っていた（= バグか不正なメッセージ）。
func handleVelocityCmd(conn *websocket.Conn, msg protocol.Message) {
	payload, ok := msg.Payload.(protocol.VelocityPayload)
	if !ok {
		log.Println("⚠️ velocity_cmd のペイロードが不正")
		errMsg := protocol.NewError(400, "velocity_cmd のペイロード形式が不正です")
		sendMessage(conn, errMsg)
		return
	}

	// --- 速度コマンドの内容をログに表示 ---
	log.Printf("🤖 速度コマンド: linear_x=%.2f, linear_y=%.2f, angular_z=%.2f",
		payload.LinearX, payload.LinearY, payload.AngularZ)

	// --- コマンドの説明文を生成 ---
	description := describeVelocity(payload)

	// --- command_ack メッセージで応答 ---
	// 将来はここにセーフティチェック（速度制限、障害物検知）を入れる
	ack := protocol.NewCommandAck(defaultRobotID, "executing", description)
	sendMessage(conn, ack)
}

// =============================================================================
// describeVelocity — 速度コマンドを人間が読みやすい文字列に変換
// =============================================================================
func describeVelocity(v protocol.VelocityPayload) string {
	if v.LinearX == 0 && v.LinearY == 0 && v.AngularZ == 0 {
		return "停止"
	}

	desc := ""
	if v.LinearX > 0 {
		desc += fmt.Sprintf("前進 %.2f m/s ", v.LinearX)
	} else if v.LinearX < 0 {
		desc += fmt.Sprintf("後退 %.2f m/s ", -v.LinearX)
	}

	if v.LinearY > 0 {
		desc += fmt.Sprintf("左移動 %.2f m/s ", v.LinearY)
	} else if v.LinearY < 0 {
		desc += fmt.Sprintf("右移動 %.2f m/s ", -v.LinearY)
	}

	if v.AngularZ > 0 {
		desc += fmt.Sprintf("左旋回 %.2f rad/s ", v.AngularZ)
	} else if v.AngularZ < 0 {
		desc += fmt.Sprintf("右旋回 %.2f rad/s ", -v.AngularZ)
	}

	return desc
}

// =============================================================================
// writePump — 定期的にセンサーデータを構造化メッセージとして送信
// =============================================================================
//
// 【Step 1 からの変更点】
// - テキスト文字列の代わりに SensorPayload を含む構造化メッセージを送信
// - protocol.NewSensorData() でメッセージを生成
// - codec.Encode() で JSON にシリアライズ
func writePump(conn *websocket.Conn, done chan struct{}) {
	ticker := time.NewTicker(sensorInterval)
	defer ticker.Stop()

	for {
		select {
		case <-done:
			log.Println("writePump 停止（クライアント切断）")
			return

		case <-ticker.C:
			// --- モックセンサーデータを構造化メッセージとして送信 ---
			sensorMsg := generateMockSensorMessage()
			sendMessage(conn, sensorMsg)
		}
	}
}

// =============================================================================
// generateMockSensorMessage — モックセンサーデータメッセージを生成
// =============================================================================
//
// 【Step 1 からの変更点】
// 文字列ではなく protocol.Message 構造体を返す。
// NewSensorData ヘルパーで型安全にメッセージを作成。
func generateMockSensorMessage() protocol.Message {
	return protocol.NewSensorData(
		defaultRobotID,
		20.0+rand.Float64()*10.0, // 温度: 20〜30°C
		50.0+rand.Float64()*50.0, // バッテリー: 50〜100%
		rand.Float64(),           // 速度: 0〜1 m/s
		0.5+rand.Float64()*4.5,   // 障害物距離: 0.5〜5.0 m
	)
}

// =============================================================================
// sendMessage — 構造化メッセージをエンコードして送信
// =============================================================================
//
// 【ヘルパー関数に抽出する理由】
// エンコード → 送信 → エラーチェック の流れを毎回書くのは面倒で、
// バグの原因にもなる。共通処理を1つの関数にまとめる = DRY 原則
// （Don't Repeat Yourself: 同じことを繰り返すな）。
func sendMessage(conn *websocket.Conn, msg protocol.Message) {
	data, err := codec.Encode(msg)
	if err != nil {
		log.Println("エンコードエラー:", err)
		return
	}

	err = conn.WriteMessage(websocket.TextMessage, data)
	if err != nil {
		log.Println("送信エラー:", err)
	}
}
