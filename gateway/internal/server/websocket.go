// =============================================================================
// Step 3: WebSocket サーバー（Adapter 統合版）
// =============================================================================
//
// 【このファイルの概要】
// Step 2 では main.go にすべてのWebSocket処理が入っていた。
// Step 3 では以下の変更を行う:
//
//   1. WebSocket 処理を server パッケージに分離（責任の分離）
//   2. Adapter パターンを統合（モックデータ → Adapter のセンサーデータ）
//   3. コマンドを Adapter に委譲（直接ログ出力 → Adapter.SendCommand）
//
// 【パッケージ分離のメリット】
// - main.go はエントリーポイントに専念（配線のみ）
// - server パッケージは WebSocket 通信に専念
// - adapter パッケージはロボット制御に専念
// → 各パッケージが1つの責任だけを持つ = 単一責任の原則 (SRP)
//
// 【Step 2 からの進化】
// Step 2: generateMockSensorMessage() で固定的なランダムデータ
// Step 3: adapter.SensorDataChannel() からリアルなストリームデータ
//
// =============================================================================
package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
)

// =============================================================================
// Server 構造体
// =============================================================================
//
// 【構造体に依存性を注入する】
// Server は adapter.RobotAdapter を「受け取る」設計。
// どのアダプターを使うかは main.go が決める。
// これが「依存性注入（Dependency Injection）」の実践。
//
//   main.go:  mockAdapter を作って Server に渡す
//   Server:   渡されたアダプターを使う（中身は気にしない）
//
// 将来、本物のロボットアダプターを作っても、Server は変更不要。
type Server struct {
	adapter  adapter.RobotAdapter
	codec    protocol.Codec
	upgrader websocket.Upgrader
	port     string
}

// =============================================================================
// NewServer — サーバーのコンストラクタ
// =============================================================================
//
// 【引数の設計】
// adapter: どのロボットアダプターを使うか（外から注入）
// port:    リッスンポート（":8080" 形式）
//
// 【Upgrader の設定】
// ReadBufferSize / WriteBufferSize: WebSocket のバッファサイズ。
// CheckOrigin: 本番では厳密に設定すべきだが、開発中は全許可。
func NewServer(robotAdapter adapter.RobotAdapter, port string) *Server {
	return &Server{
		adapter: robotAdapter,
		codec:   protocol.NewJSONCodec(),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			CheckOrigin: func(r *http.Request) bool {
				return true // 開発用: 全オリジン許可
			},
		},
		port: port,
	}
}

// =============================================================================
// Start — サーバーを起動
// =============================================================================
//
// 【context.Context を受け取る理由】
// 将来的に graceful shutdown（優雅な停止）をしたいとき、
// ctx のキャンセルでサーバーを停止できる。
// Step 3 では使わないが、良い習慣として引数に含める。
func (s *Server) Start(ctx context.Context) error {
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", s.handleWebSocket)

	// --- ヘルスチェック ---
	// Docker Compose の healthcheck や監視で使うシンプルなエンドポイント
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		status := map[string]any{
			"status":    "ok",
			"adapter":   s.adapter.Name(),
			"connected": s.adapter.IsConnected(),
		}
		json.NewEncoder(w).Encode(status)
	})

	log.Printf("🚀 WebSocket サーバー起動 (Step 3: Adapter パターン)")
	log.Printf("   エンドポイント: ws://localhost%s/ws", s.port)
	log.Printf("   ヘルス: http://localhost%s/health", s.port)
	log.Printf("   アダプター: %s", s.adapter.Name())
	log.Printf("   Ctrl+C で停止")

	return http.ListenAndServe(s.port, mux)
}

// =============================================================================
// handleWebSocket — WebSocket 接続のハンドラー
// =============================================================================
//
// 【Step 2 からの変更点】
// s.upgrader を使う（メソッドレシーバ経由でアクセス）
func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket アップグレード失敗:", err)
		return
	}
	defer conn.Close()

	log.Println("✅ 新しいクライアントが接続しました")

	// 接続時にアダプターの情報を送信
	s.sendAdapterInfo(conn)

	done := make(chan struct{})
	go s.writePump(conn, done)
	s.readPump(conn, done)

	log.Println("❌ クライアントが切断しました")
}

// =============================================================================
// sendAdapterInfo — 接続時にアダプター情報を送信
// =============================================================================
//
// 【接続直後に情報を送る理由】
// クライアントがロボットの状態を知るために、接続直後に情報を送る。
// - どのロボットに接続しているか
// - ロボットの能力（速度制限など）
// - 接続状態
func (s *Server) sendAdapterInfo(conn *websocket.Conn) {
	caps := s.adapter.GetCapabilities()
	info := protocol.Message{
		Type:      "adapter_info",
		RobotID:   "robot-01",
		Timestamp: time.Now(),
		Payload: map[string]any{
			"adapter_name": s.adapter.Name(),
			"connected":    s.adapter.IsConnected(),
			"capabilities": map[string]any{
				"velocity_control": caps.SupportsVelocityControl,
				"navigation":      caps.SupportsNavigation,
				"estop":           caps.SupportsEStop,
				"max_linear":      caps.MaxLinearVelocity,
				"max_angular":     caps.MaxAngularVelocity,
				"sensor_topics":   caps.SensorTopics,
			},
		},
	}
	s.sendMessage(conn, info)
}

// =============================================================================
// readPump — クライアントからのメッセージを受信・処理
// =============================================================================
//
// 【Step 2 からの変更点】
// - velocity_cmd → adapter.SendCommand に委譲
// - estop メッセージ → adapter.EmergencyStop に委譲
// - "connect" / "disconnect" コマンドを追加
func (s *Server) readPump(conn *websocket.Conn, done chan struct{}) {
	defer close(done)

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Println("読み取りエラー:", err)
			return
		}

		msg, err := s.codec.Decode(message)
		if err != nil {
			log.Println("⚠️ デコードエラー:", err)
			errMsg := protocol.NewError(400, fmt.Sprintf("メッセージの解析に失敗: %v", err))
			s.sendMessage(conn, errMsg)
			continue
		}

		log.Printf("📨 受信: type=%s, robot_id=%s", msg.Type, msg.RobotID)

		// --- メッセージの Type に応じた処理 ---
		switch msg.Type {
		case protocol.TypeVelocityCmd:
			s.handleVelocityCmd(conn, msg)

		case "estop":
			s.handleEStop(conn)

		case "connect":
			s.handleConnect(conn)

		case "disconnect":
			s.handleDisconnect(conn)

		default:
			log.Printf("⚠️ 未対応のメッセージタイプ: %s", msg.Type)
			errMsg := protocol.NewError(404, fmt.Sprintf("未対応のメッセージタイプ: %s", msg.Type))
			s.sendMessage(conn, errMsg)
		}
	}
}

// =============================================================================
// handleVelocityCmd — velocity_cmd メッセージを Adapter 経由で処理
// =============================================================================
//
// 【Step 2 からの変更点】
// Step 2: ログ出力して ack を返すだけ
// Step 3: adapter.SendCommand() でアダプターに委譲
//         → MockAdapter が内部速度を更新 → センサーデータに反映
func (s *Server) handleVelocityCmd(conn *websocket.Conn, msg protocol.Message) {
	payload, ok := msg.Payload.(protocol.VelocityPayload)
	if !ok {
		log.Println("⚠️ velocity_cmd のペイロードが不正")
		errMsg := protocol.NewError(400, "velocity_cmd のペイロード形式が不正です")
		s.sendMessage(conn, errMsg)
		return
	}

	// Adapter に速度コマンドを送信
	cmd := adapter.Command{
		Type: "velocity",
		Payload: map[string]any{
			"linear_x":  payload.LinearX,
			"linear_y":  payload.LinearY,
			"angular_z": payload.AngularZ,
		},
	}

	if err := s.adapter.SendCommand(context.Background(), cmd); err != nil {
		log.Printf("⚠️ コマンド送信エラー: %v", err)
		errMsg := protocol.NewError(500, fmt.Sprintf("コマンド送信失敗: %v", err))
		s.sendMessage(conn, errMsg)
		return
	}

	// --- コマンド成功の応答 ---
	description := describeVelocity(payload)
	ack := protocol.NewCommandAck("robot-01", "executing", description)
	s.sendMessage(conn, ack)
}

// =============================================================================
// handleEStop — 緊急停止
// =============================================================================
func (s *Server) handleEStop(conn *websocket.Conn) {
	if err := s.adapter.EmergencyStop(context.Background()); err != nil {
		log.Printf("⚠️ 緊急停止エラー: %v", err)
		errMsg := protocol.NewError(500, fmt.Sprintf("緊急停止失敗: %v", err))
		s.sendMessage(conn, errMsg)
		return
	}

	ack := protocol.NewCommandAck("robot-01", "stopped", "緊急停止を実行しました")
	s.sendMessage(conn, ack)
}

// =============================================================================
// handleConnect / handleDisconnect — アダプター接続管理
// =============================================================================
func (s *Server) handleConnect(conn *websocket.Conn) {
	if err := s.adapter.Connect(context.Background(), nil); err != nil {
		log.Printf("⚠️ 接続エラー: %v", err)
		errMsg := protocol.NewError(500, fmt.Sprintf("接続失敗: %v", err))
		s.sendMessage(conn, errMsg)
		return
	}

	ack := protocol.NewCommandAck("robot-01", "connected", "ロボットに接続しました")
	s.sendMessage(conn, ack)
}

func (s *Server) handleDisconnect(conn *websocket.Conn) {
	if err := s.adapter.Disconnect(context.Background()); err != nil {
		log.Printf("⚠️ 切断エラー: %v", err)
		errMsg := protocol.NewError(500, fmt.Sprintf("切断失敗: %v", err))
		s.sendMessage(conn, errMsg)
		return
	}

	ack := protocol.NewCommandAck("robot-01", "disconnected", "ロボットから切断しました")
	s.sendMessage(conn, ack)
}

// =============================================================================
// writePump — Adapter のセンサーデータを WebSocket 経由で送信
// =============================================================================
//
// 【Step 2 からの大きな変更】
// Step 2: ticker で1秒ごとにランダムデータを生成
// Step 3: adapter.SensorDataChannel() からリアルタイムデータを受信
//
// MockAdapter は 20Hz でオドメトリ、5秒ごとにバッテリーを送信。
// writePump はそれをそのまま WebSocket クライアントに転送する。
//
// 【チャネルからの受信と select】
// adapter.SensorDataChannel() は <-chan SensorData（受信専用チャネル）。
// select で done チャネルとセンサーデータチャネルを同時に待機する。
func (s *Server) writePump(conn *websocket.Conn, done chan struct{}) {
	// Adapter のセンサーデータチャネルを取得
	sensorCh := s.adapter.SensorDataChannel()

	for {
		select {
		case <-done:
			log.Println("writePump 停止（クライアント切断）")
			return

		case data, ok := <-sensorCh:
			if !ok {
				// チャネルが閉じられた
				log.Println("センサーデータチャネルが閉じられました")
				return
			}

			// SensorData → protocol.Message に変換して送信
			msg := sensorDataToMessage(data)
			s.sendMessage(conn, msg)
		}
	}
}

// =============================================================================
// sensorDataToMessage — adapter.SensorData を protocol.Message に変換
// =============================================================================
//
// 【パッケージ間の変換】
// adapter パッケージの SensorData と protocol パッケージの Message は
// 別のパッケージに属する別の型。型変換（mapping）が必要。
//
// なぜ adapter.SensorData をそのまま WebSocket に送らない？
// → protocol パッケージが定める「通信フォーマット」に合わせるため。
// → 内部データ構造と外部通信フォーマットを分離する設計。
func sensorDataToMessage(data adapter.SensorData) protocol.Message {
	return protocol.Message{
		Type:      protocol.TypeSensorData,
		RobotID:   data.RobotID,
		Timestamp: time.Unix(0, data.Timestamp),
		Payload:   data.Data, // map[string]any をそのまま渡す
	}
}

// =============================================================================
// describeVelocity — 速度コマンドを人間が読みやすい文字列に変換
// =============================================================================
// Step 2 から移植。変更なし。
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
// sendMessage — 構造化メッセージをエンコードして送信
// =============================================================================
func (s *Server) sendMessage(conn *websocket.Conn, msg protocol.Message) {
	data, err := s.codec.Encode(msg)
	if err != nil {
		log.Println("エンコードエラー:", err)
		return
	}

	err = conn.WriteMessage(websocket.TextMessage, data)
	if err != nil {
		log.Println("送信エラー:", err)
	}
}
