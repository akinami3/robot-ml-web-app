// =============================================================================
// Step 5: Hub — クライアント管理と Pub/Sub メッセージ配信
// =============================================================================
//
// 【Hub パターン（ハブパターン）とは？】
// 中央の「ハブ」が複数のクライアントを管理し、メッセージを配信する設計。
// gorilla/websocket の公式サンプルでも採用されている定番パターン。
//
//   Client A ──┐
//              ├── Hub ── Adapter ── Robot
//   Client B ──┘
//
// Step 4 まで: 1クライアント前提（writePump が直接 conn に書き込み）
// Step 5:     Hub が複数クライアントを管理、ブロードキャストで配信
//
// 【Pub/Sub（Publish/Subscribe）】
// Publisher（発行者）: センサーデータを Hub に送信
// Subscriber（購読者）: Hub に登録された Client がデータを受信
//
// Hub が仲介することで、Publisher は Subscriber を知らなくていい。
// Subscriber が増えても Publisher のコードは変更不要。
//
// 【goroutine の安全性】
// 複数クライアントの同時接続/切断が goroutine 上で発生する。
// channel ベースの登録/解除で安全にクライアント管理を行う。
//
// =============================================================================
package server

import (
	"log"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
)

// =============================================================================
// Client — WebSocket クライアントを表す構造体
// =============================================================================
//
// 【Client の責務】
// 1. WebSocket 接続（conn）を保持
// 2. 送信バッファ（send channel）を管理
// 3. クライアント識別子（ID）を管理
//
// 【send channel の役割】
// Hub → Client のメッセージ配信に使う。
// Hub が send チャネルに書き込み → Client の writePump が読み出して送信。
// チャネルにバッファ（256）を設定し、遅いクライアントでもブロックしにくくする。
type Client struct {
	ID   string
	conn *websocket.Conn
	send chan []byte // 送信バッファ
	hub  *Hub
}

// NewClient — クライアントのコンストラクタ
func NewClient(id string, conn *websocket.Conn, hub *Hub) *Client {
	return &Client{
		ID:   id,
		conn: conn,
		send: make(chan []byte, 256), // バッファ付きチャネル
		hub:  hub,
	}
}

// =============================================================================
// Client.WritePump — 送信バッファからWebSocketへ書き込む
// =============================================================================
//
// 【goroutine として実行される】
// go client.WritePump() のように起動。
// send チャネルからメッセージを読み出して WebSocket に書き込み続ける。
//
// 【Ping/Pong ハートビート】
// WebSocket の Ping/Pong メカニズムで接続の生存を確認する。
// 54秒ごとに Ping を送信。クライアントが Pong を返さなければ接続断と判断。
func (c *Client) WritePump() {
	ticker := time.NewTicker(54 * time.Second) // Ping 間隔
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			// 書き込みデッドラインを設定
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				// Hub がチャネルを閉じた → 接続終了
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.conn.WriteMessage(websocket.TextMessage, message); err != nil {
				log.Printf("❌ Client %s: 書き込みエラー: %v", c.ID, err)
				return
			}

		case <-ticker.C:
			// Ping 送信（ハートビート）
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// =============================================================================
// Hub — クライアント管理の中央ハブ
// =============================================================================
//
// 【フィールドの説明】
// clients:    接続中の全クライアントを保持する map
// register:   クライアント登録用チャネル
// unregister: クライアント解除用チャネル
// broadcast:  全クライアントへのメッセージ配信用チャネル
// codec:      メッセージのエンコーダー
//
// 【なぜ channel で管理する？】
// map は goroutine safe ではない（同時に読み書きすると panic する）。
// channel 経由で操作を Run() ループに集約し、
// map への操作を1つの goroutine に限定する → 安全。
type Hub struct {
	clients    map[string]*Client
	register   chan *Client
	unregister chan *Client
	broadcast  chan protocol.Message
	codec      protocol.Codec
	mu         sync.RWMutex
}

// NewHub — Hub のコンストラクタ
func NewHub() *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan protocol.Message, 256),
		codec:      protocol.NewJSONCodec(),
	}
}

// =============================================================================
// Run — Hub のメインイベントループ（goroutine で実行）
// =============================================================================
//
// 【select ベースのイベントループ】
// Go の並行処理の定番パターン。
// 3つのチャネルを同時に待機し、イベントが来たら処理する。
//
//   for {
//       select {
//       case client := <-register:   // 新規接続
//       case client := <-unregister: // 切断
//       case msg := <-broadcast:     // メッセージ配信
//       }
//   }
//
// 【hub.Run() は1つの goroutine で動く】
// すべての map 操作がこの goroutine 内で行われるため、
// mutex なしで安全にクライアント管理できる。
func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.clients[client.ID] = client
			log.Printf("📥 Hub: クライアント登録 ID=%s (接続数: %d)",
				client.ID, len(h.clients))

		case client := <-h.unregister:
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				close(client.send)
				log.Printf("📤 Hub: クライアント解除 ID=%s (接続数: %d)",
					client.ID, len(h.clients))
			}

		case msg := <-h.broadcast:
			data, err := h.codec.Encode(msg)
			if err != nil {
				log.Printf("⚠️ Hub: エンコードエラー: %v", err)
				continue
			}

			// 全クライアントに配信
			for id, client := range h.clients {
				select {
				case client.send <- data:
					// 送信成功
				default:
					// バッファフルの場合、クライアントを切断
					// 遅いクライアントが全体を遅くするのを防止
					log.Printf("⚠️ Hub: Client %s のバッファフル → 切断", id)
					close(client.send)
					delete(h.clients, id)
				}
			}
		}
	}
}

// =============================================================================
// Register / Unregister — クライアントの登録・解除
// =============================================================================
func (h *Hub) Register(client *Client) {
	h.register <- client
}

func (h *Hub) Unregister(client *Client) {
	h.unregister <- client
}

// =============================================================================
// Broadcast — 全クライアントへのメッセージ配信
// =============================================================================
func (h *Hub) Broadcast(msg protocol.Message) {
	h.broadcast <- msg
}

// =============================================================================
// SendTo — 特定のクライアントにメッセージ送信
// =============================================================================
//
// 【ユニキャストとブロードキャスト】
// Broadcast: 全クライアントに送信（センサーデータなど）
// SendTo:    特定のクライアントに送信（コマンド応答など）
func (h *Hub) SendTo(clientID string, msg protocol.Message) error {
	h.mu.RLock()
	defer h.mu.RUnlock()

	// Run ループで管理している map に直接アクセスするのは本来危険だが、
	// 読み取りロックで保護。書き込みは Run ループのみ。
	// より厳密にはチャネル経由にすべきだが、教育目的で簡略化。
	data, err := h.codec.Encode(msg)
	if err != nil {
		return err
	}

	// clients map は Run() goroutine が管理しているが、
	// 読み取りのみなので軽量に参照する。
	// プロダクションではこのアクセスもチャネル経由にする。
	for _, client := range h.clients {
		if client.ID == clientID {
			select {
			case client.send <- data:
				return nil
			default:
				return nil // バッファフル → ドロップ
			}
		}
	}

	return nil
}

// ClientCount — 接続中のクライアント数
func (h *Hub) ClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}
