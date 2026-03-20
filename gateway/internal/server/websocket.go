// =============================================================================
// Step 5: WebSocket サーバー — Hub + Handler + Safety 統合版
// =============================================================================
//
// 【Step 4 からの変更点】
// 1. Hub を使ったマルチクライアント対応
// 2. Handler で安全パイプラインを統合
// 3. readPump / writePump を Client 単位に分離
// 4. センサーデータの Hub 経由ブロードキャスト
// 5. 接続時のクライアントID生成
//
// 【アーキテクチャの変化】
//
// Step 4:
//   Client ── 1:1 ── Server ── Adapter
//
// Step 5:
//   Client A ──┐
//              ├── Hub ── Handler ── Safety Pipeline ── Adapter
//   Client B ──┘
//              ↑
//          Broadcast
//          (Sensor)
//
// =============================================================================
package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
	"github.com/robot-ai-webapp/gateway/internal/safety"
)

// =============================================================================
// clientCounter — 一意なクライアントIDの生成用
// =============================================================================
//
// 【atomic.Int64 とは？】
// 複数の goroutine から安全にインクリメントできるカウンター。
// sync/atomic パッケージが提供する低レベル同期プリミティブ。
//
// mutex を使わずにスレッドセーフなカウンターを実現できる。
// 用途: ユニークID生成、統計カウンターなど。
var clientCounter atomic.Int64

// =============================================================================
// Server 構造体（Step 5 版）
// =============================================================================
type Server struct {
	adapter  adapter.RobotAdapter
	hub      *Hub
	handler  *Handler
	estop    *safety.EStopManager
	watchdog *safety.TimeoutWatchdog
	codec    protocol.Codec
	upgrader websocket.Upgrader
	port     string
}

// =============================================================================
// NewServer — サーバーのコンストラクタ（Step 5 版）
// =============================================================================
//
// 【引数が増えた理由】
// Step 4: adapter と port だけ
// Step 5: 安全コンポーネント（estop, limiter, watchdog, opLock）も受け取る
//
// これは「依存性が増えた」ことを意味する。
// Step 6 以降ではさらに増えるため、将来的には Config 構造体にまとめる。
func NewServer(
	robotAdapter adapter.RobotAdapter,
	hub *Hub,
	estop *safety.EStopManager,
	limiter *safety.VelocityLimiter,
	watchdog *safety.TimeoutWatchdog,
	opLock *safety.OperationLock,
	port string,
) *Server {
	handler := NewHandler(robotAdapter, estop, limiter, watchdog, opLock, hub)

	return &Server{
		adapter:  robotAdapter,
		hub:      hub,
		handler:  handler,
		estop:    estop,
		watchdog: watchdog,
		codec:    protocol.NewJSONCodec(),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			CheckOrigin: func(r *http.Request) bool {
				return true
			},
		},
		port: port,
	}
}

// =============================================================================
// Start — サーバーを起動
// =============================================================================
func (s *Server) Start(ctx context.Context) error {
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", s.handleWebSocket)
	mux.HandleFunc("/health", s.handleHealth)

	// --- Hub のイベントループを開始 ---
	go s.hub.Run()

	// --- センサーデータの Hub 経由ブロードキャスト開始 ---
	go s.sensorBroadcastLoop(ctx)

	// --- ウォッチドッグ開始 ---
	go s.watchdog.Start(ctx)

	log.Printf("🚀 WebSocket サーバー起動 (Step 5: 安全パイプライン)")
	log.Printf("   エンドポイント: ws://localhost%s/ws", s.port)
	log.Printf("   ヘルス: http://localhost%s/health", s.port)
	log.Printf("   アダプター: %s", s.adapter.Name())
	log.Printf("   E-Stop: %v", s.estop.IsActive())
	log.Printf("   Ctrl+C で停止")

	return http.ListenAndServe(s.port, mux)
}

// =============================================================================
// handleWebSocket — 新規 WebSocket 接続の処理
// =============================================================================
//
// 【Step 4 との違い】
// Step 4: 直接 readPump/writePump を起動
// Step 5: Client を作成して Hub に登録 → Client の WritePump を起動
func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket アップグレード失敗:", err)
		return
	}

	// --- クライアントIDの生成 ---
	clientID := fmt.Sprintf("client-%d", clientCounter.Add(1))

	// --- Client をHub に登録 ---
	client := NewClient(clientID, conn, s.hub)
	s.hub.Register(client)

	log.Printf("✅ 新しいクライアント: %s", clientID)

	// --- 接続時の初期情報を送信 ---
	s.sendAdapterInfo(client)

	// --- WritePump を goroutine で起動 ---
	go client.WritePump()

	// --- ReadPump はこの goroutine で実行（ブロッキング） ---
	s.readPump(client)

	// --- 切断処理 ---
	s.hub.Unregister(client)
	conn.Close()
	log.Printf("❌ クライアント切断: %s", clientID)
}

// =============================================================================
// sendAdapterInfo — 接続時にアダプター情報を Client に送信
// =============================================================================
func (s *Server) sendAdapterInfo(client *Client) {
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
			// Step 5 追加: 安全状態も含める
			"estop_active": s.estop.IsActive(),
		},
	}

	data, err := s.codec.Encode(info)
	if err != nil {
		log.Printf("⚠️ adapter_info エンコードエラー: %v", err)
		return
	}

	select {
	case client.send <- data:
	default:
		log.Printf("⚠️ Client %s のバッファフル（adapter_info 送信失敗）", client.ID)
	}
}

// =============================================================================
// readPump — クライアントからのメッセージを読み取り Handler に委譲
// =============================================================================
//
// 【Step 4 との違い】
// Step 4: switch 文で直接メッセージを処理
// Step 5: Handler.HandleMessage() に委譲（責任の分離）
func (s *Server) readPump(client *Client) {
	// Pong ハンドラ: クライアントからの Pong メッセージで読み取りデッドラインを延長
	client.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	client.conn.SetPongHandler(func(string) error {
		client.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := client.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("⚠️ [%s] 予期しない切断: %v", client.ID, err)
			}
			return
		}

		msg, err := s.codec.Decode(message)
		if err != nil {
			log.Printf("⚠️ [%s] デコードエラー: %v", client.ID, err)
			errMsg := protocol.NewError(400, fmt.Sprintf("メッセージの解析に失敗: %v", err))
			data, _ := s.codec.Encode(errMsg)
			select {
			case client.send <- data:
			default:
			}
			continue
		}

		// Handler に委譲
		s.handler.HandleMessage(client.ID, msg)
	}
}

// =============================================================================
// sensorBroadcastLoop — センサーデータを Hub 経由で全クライアントに配信
// =============================================================================
//
// 【Step 4 との違い】
// Step 4: writePump が直接 conn に書き込み
// Step 5: Hub.Broadcast() で全クライアントに配信
//
// これにより、新しいクライアントが接続しても
// 追加のgoroutineを起動する必要がない。
func (s *Server) sensorBroadcastLoop(ctx context.Context) {
	sensorCh := s.adapter.SensorDataChannel()

	for {
		select {
		case <-ctx.Done():
			log.Println("センサーブロードキャスト停止")
			return

		case data, ok := <-sensorCh:
			if !ok {
				log.Println("センサーデータチャネルが閉じられました")
				return
			}

			msg := sensorDataToMessage(data)
			s.hub.Broadcast(msg)
		}
	}
}

// =============================================================================
// sensorDataToMessage — adapter.SensorData → protocol.Message 変換
// =============================================================================
func sensorDataToMessage(data adapter.SensorData) protocol.Message {
	return protocol.Message{
		Type:      protocol.TypeSensorData,
		RobotID:   data.RobotID,
		Timestamp: time.Unix(0, data.Timestamp),
		Payload:   data.Data,
	}
}

// =============================================================================
// handleHealth — ヘルスチェックエンドポイント（Step 5 拡張）
// =============================================================================
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	maxLin, maxAng := s.handler.limiter.GetLimits()

	status := map[string]any{
		"status":    "ok",
		"adapter":   s.adapter.Name(),
		"connected": s.adapter.IsConnected(),
		"safety": map[string]any{
			"estop_active": s.estop.IsActive(),
			"velocity_limits": map[string]any{
				"max_linear":  maxLin,
				"max_angular": maxAng,
			},
		},
		"clients": s.hub.ClientCount(),
	}
	json.NewEncoder(w).Encode(status)
}

// =============================================================================
// describeVelocity — 速度コマンドの説明文を生成
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
