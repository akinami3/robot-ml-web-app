// =============================================================================
// ファイル: hub.go
// 概要: WebSocketクライアントの管理とメッセージ配信ハブ
//
// このファイルは、接続中の全WebSocketクライアントを管理し、
// メッセージの配信（ブロードキャスト）を行う「ハブ」を実装しています。
//
// 【Pub/Sub（出版/購読）パターン】
// Hubは新聞社のような役割を果たします:
//   - 新聞社（Hub）: メッセージを受け取り、購読者に配信する
//   - 読者（Client）: 興味のあるトピック（ロボット）を購読する
//   - 記者（センサー等）: ニュース（データ）を新聞社に送る
//
// 例えば:
//   - クライアントAが robot-1 を購読 → robot-1 のデータだけ受信
//   - クライアントBが robot-2 を購読 → robot-2 のデータだけ受信
//   - 安全アラートは全員に配信（BroadcastToAll）
//
// 【チャネルベースのイベントループ】
// Hub.Run() は Go の select 文を使ったイベントループで動作します。
// 3つのチャネル（register, unregister, broadcast）からイベントを受け取り、
// 1つのゴルーチンで全てのクライアント管理を行います。
// これにより、マップへのアクセスが直列化され、データ競合を防ぎます。
//
// 【アーキテクチャ上の位置づけ】
//
//   ┌──────────────┐           ┌─────┐          ┌──────────────┐
//   │  WebSocket   │──register─→│ Hub │←─send───│   Handler    │
//   │  Server      │──unregist─→│     │←─broad──│              │
//   └──────────────┘           └─────┘          └──────────────┘
//                                 │
//                         ┌───────┼───────┐
//                         ▼       ▼       ▼
//                      Client  Client  Client
// =============================================================================
package server

// =============================================================================
// インポートセクション
// =============================================================================
import (
	// "sync": 同期プリミティブを提供するパッケージ。
	// sync.RWMutex（読み書きミューテックス）と sync.Mutex（ミューテックス）を使います。
	//
	// 【なぜ2種類のMutexを使い分ける？】
	// - sync.Mutex: 読み取りでも書き込みでも排他ロック。シンプルだが並行性が低い。
	// - sync.RWMutex: 読み取りは同時に複数可能、書き込みは排他。
	//   読み取りが多い場合（センサーデータの配信など）に性能が向上します。
	"sync"

	// "github.com/gorilla/websocket": WebSocket接続のオブジェクト型（*websocket.Conn）を使用。
	// Client構造体でWebSocket接続を保持するために必要です。
	"github.com/gorilla/websocket"

	// zap: 構造化ログライブラリ
	"go.uber.org/zap"
)

// =============================================================================
// Client 構造体 - WebSocketクライアントの表現
// =============================================================================
//
// 【この構造体の役割】
// 1つのWebSocket接続（＝1人のユーザー）を表現します。
// 接続情報、認証状態、購読情報を保持します。
//
// 【ライフサイクル】
// 1. WebSocket接続時: HandleWebSocket() で作成
// 2. 認証時: handleAuth() で UserID と Authenticated を設定
// 3. 購読時: SubscribeClient() で Subscriptions を更新
// 4. データ送信時: Send チャネルにデータを送信
// 5. 切断時: Hub から削除、Send チャネルをクローズ

// Client represents a connected WebSocket client
type Client struct {
	// ID: クライアントの一意な識別子
	// generateClientID() で生成されます（例: "client-20260215143022-abc123"）
	ID string

	// UserID: 認証後に設定されるユーザーID
	// 認証前は空文字列（""）です。操作ロックのチェックなどに使用されます。
	UserID string

	// Conn: WebSocket接続オブジェクト
	// 【*websocket.Conn とは？】
	// gorilla/websocket ライブラリが提供する WebSocket接続の構造体へのポインタです。
	// メッセージの送受信、Ping/Pong、接続のクローズなどのメソッドを持ちます。
	//
	// 【注意点】
	// gorilla/websocket は同時にWriteMessage()を呼ぶことを許可しません。
	// そのため、書き込みは writePump（1つのゴルーチン）に集約します。
	Conn *websocket.Conn

	// Send: 送信バッファ用のバッファ付きチャネル
	// 【このチャネルの役割】
	// Hub やその他のゴルーチンがこのチャネルにメッセージを送信すると、
	// writePump（websocket.go）がチャネルからメッセージを取り出して
	// WebSocket経由でクライアントに送信します。
	//
	// 【バッファサイズ: 256】
	// 256個のメッセージを溜められます。
	// バッファが溢れた場合（クライアントが遅い場合）、メッセージはドロップされます。
	Send chan []byte

	// Subscriptions: 購読しているロボットIDのマップ
	// 【map[string]bool の使い方】
	// Goには「セット（集合）」型がないため、map[string]bool で代用します。
	//   - robot-1 を購読中: Subscriptions["robot-1"] = true
	//   - robot-2 は未購読: Subscriptions["robot-2"] は false（ゼロ値）
	//
	// BroadcastToRobot() で使用され、そのロボットを購読しているクライアントだけに
	// データが配信されます。
	Subscriptions map[string]bool // robot_id -> subscribed

	// Authenticated: 認証済みかどうかのフラグ
	// handleAuth() で true に設定されます。
	// 認証前のクライアントからのコマンドは拒否されます。
	Authenticated bool

	// mu: クライアント固有のミューテックス
	// Subscriptions マップへの同時アクセスを防ぐために使います。
	// 【sync.Mutex vs sync.RWMutex】
	// ここでは sync.Mutex を使っています。
	// Subscriptions の更新（SubscribeClient）は頻繁ではないため、
	// RWMutex よりもシンプルな Mutex で十分です。
	mu sync.Mutex
}

// =============================================================================
// Hub 構造体 - クライアント管理とメッセージ配信のハブ
// =============================================================================
//
// 【Hub（ハブ）とは？】
// 車輪の「ハブ」のように、全てのスポーク（クライアント接続）の中心となる存在です。
// クライアントの登録/解除、メッセージの配信を一元管理します。
//
// 【設計上のポイント - チャネルベースの同期】
// clients マップへのアクセスは Run() ゴルーチン内で行われます。
// register/unregister チャネルを通じてリクエストを送ることで、
// マップアクセスが直列化（シリアライズ）されます。
//
// しかし、BroadcastToRobot() や SendToClient() では直接 clients にアクセスするため、
// sync.RWMutex も併用してスレッドセーフを確保しています。

// Hub manages connected clients and message broadcasting
type Hub struct {
	// clients: 接続中の全クライアントを管理するマップ
	// キー: クライアントID（string）
	// 値: Client構造体へのポインタ
	clients map[string]*Client // client_id -> client

	// register: クライアント登録用チャネル
	// 新しいクライアントが接続した時に、このチャネルに送信されます。
	// 【バッファなしチャネル（unbuffered channel）】
	// make(chan *Client) で作成されるバッファなしチャネルです。
	// 送信側と受信側が同時に準備できないとブロックされます。
	// これは「同期的な」通信で、データの引き渡しが保証されます。
	register chan *Client

	// unregister: クライアント登録解除用チャネル
	// クライアントが切断した時に使われます。
	unregister chan *Client

	// broadcast: 全クライアントへのブロードキャスト用チャネル
	// 【バッファ付きチャネル: make(chan []byte, 256)】
	// 256個のメッセージを溜められるバッファ付きチャネルです。
	// バッファなしチャネルと違い、受信側が即座に処理しなくても
	// バッファ内に溜めておけるため、送信側がブロックされにくくなります。
	broadcast chan []byte

	// mu: 読み書きミューテックス
	// clients マップへの並行アクセスを保護します。
	mu sync.RWMutex

	// logger: 構造化ログ出力
	logger *zap.Logger
}

// =============================================================================
// NewHub - Hubのコンストラクタ
// =============================================================================
//
// 全てのフィールドを初期化してHubを返します。
// 【make の使い方】
// - make(map[string]*Client): 空のマップを作成
// - make(chan *Client): バッファなしチャネルを作成（同期的）
// - make(chan []byte, 256): バッファ256のチャネルを作成（非同期的）
//
// 【注意】
// NewHub() で作成した後、必ず go hub.Run() で
// イベントループを起動する必要があります。

// NewHub creates a new Hub
func NewHub(logger *zap.Logger) *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan []byte, 256),
		logger:     logger,
	}
}

// =============================================================================
// Register - クライアントの登録（チャネル経由）
// =============================================================================
//
// 直接 clients マップを操作するのではなく、register チャネルに
// クライアントを送信します。Run() のイベントループが実際の登録を行います。
//
// 【なぜチャネルを使う？】
// 複数のゴルーチン（複数のWebSocket接続ハンドラー）から同時に
// Register() が呼ばれる可能性があります。チャネルを使うことで、
// 処理が Run() ゴルーチン内で直列化され、マップアクセスが安全になります。

// Register adds a client to the hub
func (h *Hub) Register(client *Client) {
	h.register <- client
}

// =============================================================================
// Unregister - クライアントの登録解除（チャネル経由）
// =============================================================================
//
// Register と同様に、unregister チャネル経由で登録解除を依頼します。

// Unregister removes a client from the hub
func (h *Hub) Unregister(client *Client) {
	h.unregister <- client
}

// =============================================================================
// Run - Hubのメインイベントループ
// =============================================================================
//
// 【イベントループとは？】
// 「何かイベント（出来事）が起きるまで待機し、イベントが来たら処理する」
// という無限ループです。ゲームエンジンやGUIアプリケーションでも
// 同じパターンが使われています。
//
// 【3つのイベントを監視】
// 1. register: 新しいクライアントの登録
// 2. unregister: 既存クライアントの削除
// 3. broadcast: 全クライアントへのメッセージ配信
//
// 【使い方】
// この関数はブロッキング（永久ループ）なので、go hub.Run() で
// ゴルーチンとして起動します。
//
// 【select文の動作】
// select は複数のチャネルを同時に監視し、データが到着したチャネルの
// case を実行します。複数のチャネルに同時にデータがある場合、
// ランダムに1つが選ばれます（公平性のため）。
// すべてのチャネルにデータがなければ、データが来るまでブロックします。

// Run starts the hub's main event loop
func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			// 【クライアントの登録】
			// clients マップにクライアントを追加します。
			h.mu.Lock()
			h.clients[client.ID] = client
			h.mu.Unlock()

			// 登録ログを出力
			// len(h.clients) で現在の接続数を表示します。
			h.logger.Info("Client registered",
				zap.String("client_id", client.ID),
				zap.Int("total_clients", len(h.clients)),
			)

		case client := <-h.unregister:
			// 【クライアントの登録解除】
			h.mu.Lock()
			// マップにクライアントが存在するか確認
			// 【カンマOKパターン】
			// _, ok := h.clients[client.ID]
			// マップの値は使わないので _ で無視し、存在するかを ok で確認します。
			if _, ok := h.clients[client.ID]; ok {
				// マップからクライアントを削除
				delete(h.clients, client.ID)
				// 【close(client.Send)】
				// Sendチャネルを閉じます。チャネルを閉じると:
				// - 以降の送信はpanicを起こす
				// - 受信側（writePump）は即座に値を受け取り、ok=falseが返る
				// - これにより writePump が正常に終了する
				//
				// 【重要】チャネルは送信側が閉じるのがGoの慣例です。
				// 受信側が閉じると、他の送信者がpanicを起こす可能性があります。
				close(client.Send)
			}
			h.mu.Unlock()

			h.logger.Info("Client unregistered",
				zap.String("client_id", client.ID),
				zap.Int("total_clients", len(h.clients)),
			)

		case message := <-h.broadcast:
			// 【全クライアントへのブロードキャスト】
			// 読み取りロック（RLock）で clients マップを参照します。
			// 複数のブロードキャストが同時に実行されても安全です。
			h.mu.RLock()
			for _, client := range h.clients {
				// 各クライアントの Send チャネルにメッセージを送信
				select {
				case client.Send <- message:
					// 正常に送信成功
				default:
					// 【default: チャネルのバッファが満杯】
					// クライアントの処理が遅く、Sendバッファが溢れている場合。
					// メッセージをドロップ（破棄）して次のクライアントに進みます。
					// これにより、1つの遅いクライアントがシステム全体を
					// ブロックすることを防ぎます。
					// Client too slow, skip
				}
			}
			h.mu.RUnlock()
		}
	}
}

// =============================================================================
// BroadcastToRobot - 特定のロボットの購読者にメッセージを配信
// =============================================================================
//
// 【トピックベースのフィルタリング】
// 全クライアントに送信するのではなく、指定された robotID を
// 購読しているクライアントにのみ送信します。
// これにより、不要なデータの送信を避け、ネットワーク帯域を節約します。
//
// 例: robot-1 のセンサーデータは、robot-1 を購読しているクライアントにのみ配信
//
// 【パフォーマンスの考慮】
// RLock（読み取りロック）を使用しているので、複数の BroadcastToRobot() が
// 同時に実行されても互いにブロックしません。
// これは重要です。なぜなら、複数のロボットが同時にセンサーデータを
// 生成する可能性があるからです。

// BroadcastToRobot sends a message to all clients subscribed to a robot
func (h *Hub) BroadcastToRobot(robotID string, data []byte) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for _, client := range h.clients {
		// 【マップの参照: client.Subscriptions[robotID]】
		// マップに存在しないキーを参照すると、ゼロ値（boolの場合はfalse）が返ります。
		// つまり、購読していないクライアントでは false が返り、if文をスキップします。
		if client.Subscriptions[robotID] {
			select {
			case client.Send <- data:
				// 送信成功
			default:
				// バッファ満杯の警告ログ
				// 頻繁に発生する場合、クライアントの処理速度に問題があります
				h.logger.Warn("Client send buffer full",
					zap.String("client_id", client.ID),
				)
			}
		}
	}
}

// =============================================================================
// BroadcastToAll - 全クライアントへのメッセージ配信
// =============================================================================
//
// 購読状態に関係なく、接続中の全クライアントにメッセージを送信します。
// 主に安全アラート（E-Stop）やシステム通知に使用されます。
//
// 【BroadcastToRobot vs BroadcastToAll】
// - BroadcastToRobot: 特定のロボットの購読者のみ → センサーデータ配信
// - BroadcastToAll: 全員に配信 → 安全アラート、システム通知

// BroadcastToAll sends a message to all connected clients
func (h *Hub) BroadcastToAll(data []byte) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for _, client := range h.clients {
		select {
		case client.Send <- data:
		default:
			// バッファ満杯の場合、メッセージをドロップ
		}
	}
}

// =============================================================================
// SendToClient - 特定のクライアントにメッセージを送信
// =============================================================================
//
// 1対1の通信です。ブロードキャスト（1対多）ではなく、
// 特定のクライアントだけにメッセージを送ります。
// 主にコマンドのACK（確認応答）やエラーメッセージの送信に使います。
//
// 【select + default パターン】
// チャネルが満杯の場合はブロックせず、警告ログを出力します。
// 重要なメッセージ（ACKなど）がドロップされる可能性がありますが、
// システムの安定性（ブロックしないこと）を優先しています。

// SendToClient sends a message to a specific client
func (h *Hub) SendToClient(client *Client, data []byte) {
	select {
	case client.Send <- data:
		// 正常に送信キューに追加
	default:
		// Sendチャネルのバッファ（256個）が満杯
		h.logger.Warn("Client send buffer full",
			zap.String("client_id", client.ID),
		)
	}
}

// =============================================================================
// SubscribeClient - クライアントをロボットのデータに購読登録
// =============================================================================
//
// 【購読（サブスクライブ）とは？】
// クライアントが「このロボットのデータを受け取りたい」と宣言することです。
// 認証時に自動的に呼ばれるほか、クライアントが明示的に購読を追加することもできます。
//
// 【Mutexの使い分け】
// client.mu（sync.Mutex）を使って、Client.Subscriptions マップへの
// アクセスを保護しています。Hub.mu（sync.RWMutex）とは別のロックです。
//
// 【なぜ別のロック？】
// Hub のミューテックスはクライアントの追加/削除を保護するためのものです。
// 個々のクライアントの Subscriptions マップは、クライアント固有のデータなので、
// クライアント自身のミューテックスで保護します。
// これにより、異なるクライアントの購読変更が互いにブロックしません（きめ細かいロック）。

// SubscribeClient subscribes a client to a robot's data
func (h *Hub) SubscribeClient(client *Client, robotID string) {
	// クライアント固有のロックを取得
	client.mu.Lock()
	defer client.mu.Unlock()

	// 購読マップにロボットIDを追加（true = 購読中）
	client.Subscriptions[robotID] = true

	h.logger.Info("Client subscribed to robot",
		zap.String("client_id", client.ID),
		zap.String("robot_id", robotID),
	)
}
