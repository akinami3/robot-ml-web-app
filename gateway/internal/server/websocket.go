// =============================================================================
// ファイル: websocket.go
// 概要: WebSocketサーバーの実装
//
// このファイルは、ブラウザ（フロントエンド）とバックエンド間のリアルタイム
// 双方向通信を実現するWebSocketサーバーを実装しています。
//
// 【WebSocketとは？】
// 通常のHTTP通信は「リクエスト→レスポンス」の一方通行ですが、
// WebSocketは一度接続すると、サーバーとクライアントの両方から自由にデータを
// 送受信できます。ロボットのセンサーデータのようなリアルタイムデータの
// 配信に最適です。
//
// 【WebSocketのライフサイクル】
// 1. クライアントがHTTPでアクセス
// 2. サーバーが「アップグレード」してWebSocket接続に切り替え
// 3. 読み取りポンプ（readPump）と書き込みポンプ（writePump）が起動
// 4. 双方向でメッセージをやり取り
// 5. 接続が切れたらクリーンアップ
//
// 【Ping/Pongメカニズム】
// WebSocket接続が切れていないか確認するための「ハートビート」です。
// サーバーが定期的にPingを送り、クライアントがPongで応答します。
// 一定時間Pongが返ってこなければ、接続が切れたとみなします。
// =============================================================================
package server

// =============================================================================
// インポートセクション
// =============================================================================
import (
	// "net/http": HTTPサーバー機能を提供する標準パッケージ。
	// WebSocketの最初の接続（HTTPアップグレード）や、ヘルスチェックに使います。
	"net/http"

	// "time": 時間関連の機能。タイムアウトやPing間隔の設定に使います。
	"time"

	// "github.com/gorilla/websocket": WebSocketプロトコルの実装ライブラリ。
	// Go標準にはWebSocketサポートが限定的なので、このライブラリが広く使われています。
	// 接続のアップグレード、メッセージの送受信、Ping/Pongなどを提供します。
	"github.com/gorilla/websocket"

	// protocol: 独自メッセージフォーマットのエンコード/デコードを行うパッケージ。
	// WebSocket上でやり取りするメッセージの構造と変換を定義しています。
	"github.com/robot-ai-webapp/gateway/internal/protocol"

	// zap: 構造化ログライブラリ
	"go.uber.org/zap"
)

// =============================================================================
// 定数（const）定義
// =============================================================================
//
// 【constとは？】
// 実行中に変更されない値を定義します。コードの可読性と保守性が向上します。
// Goの定数は型推論が効くため、明示的な型指定は省略可能です。
const (
	// writeWait: 書き込みがタイムアウトするまでの待ち時間（10秒）
	// これを超えると接続に問題があるとみなします。
	writeWait = 10 * time.Second

	// pongWait: Pongメッセージを待つ最大時間（60秒）
	// この時間内にPongが来なければ、接続が切れたとみなします。
	pongWait = 60 * time.Second

	// pingPeriod: Pingメッセージを送る間隔（54秒 = 60秒 × 9/10）
	// pongWait より短い間隔で Ping を送ることで、
	// タイムアウト前に必ず1回はPingが送られるようになります。
	pingPeriod = (pongWait * 9) / 10

	// maxMessageSize: 受信可能な最大メッセージサイズ（64KB）
	// 巨大なメッセージによるメモリ枯渇攻撃を防ぎます。
	maxMessageSize = 65536
)

// =============================================================================
// WebSocketServer 構造体
// =============================================================================
//
// 【この構造体の役割】
// WebSocket接続の管理を担当します。HTTP接続のアップグレード、
// クライアントの登録、メッセージの読み書きを行います。
//
// 【各フィールドの関係】
// hub:     接続中の全クライアントを管理（hub.go で定義）
// handler: 受信メッセージの処理ロジック（handler.go で定義）
// codec:   メッセージのエンコード/デコード
// upgrader: HTTP → WebSocket のプロトコル変換
// logger:  ログ出力
type WebSocketServer struct {
	// hub: クライアント管理とメッセージ配信を行うハブ
	// Pub/Sub（出版/購読）パターンの中心的な存在です。
	hub *Hub

	// handler: 受信したメッセージをビジネスロジックに振り分ける
	handler *Handler

	// codec: メッセージのシリアライズ/デシリアライズ
	// バイナリデータ ↔ 構造化メッセージ の変換を行います
	codec *protocol.Codec

	// upgrader: HTTP接続をWebSocket接続にアップグレードするための設定
	// 【websocket.Upgrader】
	// バッファサイズやオリジンチェックの設定を持ちます。
	upgrader websocket.Upgrader

	// logger: 構造化ログ出力
	logger *zap.Logger
}

// =============================================================================
// NewWebSocketServer - WebSocketサーバーのコンストラクタ
// =============================================================================
//
// 各コンポーネント（hub, handler, logger）を受け取り、
// WebSocketサーバーを初期化して返します。
//
// 【websocket.Upgrader の設定】
// - ReadBufferSize/WriteBufferSize: 読み書きバッファのサイズ（バイト単位）
//   4096バイト（4KB）は一般的なメッセージサイズに十分です。
// - CheckOrigin: CORS（クロスオリジン）チェック関数
//   開発環境では全てのオリジンを許可（return true）しています。
//   本番環境ではセキュリティのため、特定のオリジンのみ許可すべきです。
func NewWebSocketServer(hub *Hub, handler *Handler, logger *zap.Logger) *WebSocketServer {
	return &WebSocketServer{
		hub:     hub,
		handler: handler,
		codec:   protocol.NewCodec(),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  4096,
			WriteBufferSize: 4096,
			// 【CheckOrigin関数】
			// クロスオリジンリクエストを許可するかどうかを判定する関数
			// *http.Request を受け取り、bool を返す無名関数（クロージャ）です。
			// 開発環境: return true（全て許可）
			// 本番環境: ドメインチェックを行うべき
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins in dev
			},
		},
		logger: logger,
	}
}

// =============================================================================
// HandleWebSocket - WebSocket接続のハンドラー
// =============================================================================
//
// 【HTTPハンドラーとしての役割】
// この関数は http.HandlerFunc のシグネチャに合致するため、
// HTTPルーターに直接登録できます。
// 例: http.HandleFunc("/ws", server.HandleWebSocket)
//
// 【処理フロー】
// 1. HTTP接続をWebSocketにアップグレード
// 2. Client構造体を作成
// 3. Hubにクライアントを登録
// 4. 書き込みポンプ（writePump）を起動
// 5. 読み取りポンプ（readPump）を起動
//
// 【w http.ResponseWriter, r *http.Request】
// Go標準のHTTPハンドラーのパラメータです。
// - w: レスポンスを書き込むためのインターフェース
// - r: クライアントからのHTTPリクエスト情報
func (s *WebSocketServer) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	// 【Upgrade - HTTPからWebSocketへの切り替え】
	// HTTPの「101 Switching Protocols」レスポンスを送信し、
	// 接続をWebSocketプロトコルに切り替えます。
	// 失敗した場合（ブラウザがWebSocketをサポートしないなど）、エラーを返します。
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		s.logger.Error("WebSocket upgrade failed", zap.Error(err))
		return
	}

	// 【Clientの作成】
	// 新しく接続したクライアントの情報を保持する構造体を作成します。
	// - ID: 一意な識別子（日時+ランダム文字列で生成）
	// - Conn: WebSocket接続オブジェクト（メッセージの送受信に使用）
	// - Send: 送信バッファ用のバッファ付きチャネル（256メッセージ分）
	// - Subscriptions: どのロボットのデータを購読するかのマップ
	client := &Client{
		ID:            generateClientID(),
		Conn:          conn,
		Send:          make(chan []byte, 256),
		Subscriptions: make(map[string]bool),
	}

	// Hubにクライアントを登録（他のゴルーチンからも参照可能にする）
	s.hub.Register(client)

	// 接続ログの出力
	// zap.String() でキー・バリューペアを作成します（構造化ログ）
	s.logger.Info("WebSocket client connected",
		zap.String("client_id", client.ID),
		zap.String("remote_addr", conn.RemoteAddr().String()),
	)

	// 【ゴルーチンでポンプを起動】
	// writePump と readPump はそれぞれ独立したゴルーチンで動作します。
	// writePump: サーバー→クライアントへの送信を担当
	// readPump: クライアント→サーバーの受信を担当
	//
	// 一般的に、WebSocketでは「書き込み」と「読み取り」を別々のゴルーチンで
	// 行います。gorilla/websocket は同時書き込みを許可しないため、
	// 書き込みは1つのゴルーチンに集約する必要があります。
	go s.writePump(client)
	go s.readPump(client)
}

// =============================================================================
// readPump - クライアントからのメッセージ読み取りポンプ
// =============================================================================
//
// 【読み取りポンプとは？】
// クライアントから送られてくるメッセージを継続的に読み取り、
// 処理ハンドラーに渡す無限ループです。「ポンプ」という名前は、
// データを汲み上げ続けるイメージから来ています。
//
// 【処理フロー】
// 1. 接続の読み取り設定（サイズ制限、タイムアウト、Pongハンドラー）
// 2. メッセージを読み取り
// 3. メッセージをデコード
// 4. ハンドラーに処理を委譲
// 5. エラーが起きたらループを終了し、クリーンアップ
//
// 【重要なポイント】
// この関数はゴルーチンの終了時（return時）に、deferで自動的に
// クライアントの登録解除と接続のクローズを行います。
func (s *WebSocketServer) readPump(client *Client) {
	// 【defer - クリーンアップ処理】
	// 関数終了時に実行される処理を登録します。
	// 無名関数（クロージャ）を使って複数の処理をまとめています。
	// これにより、どのような原因で関数が終了しても確実にクリーンアップされます。
	defer func() {
		// Hubからクライアントを登録解除
		s.hub.Unregister(client)
		// WebSocket接続を閉じる
		client.Conn.Close()
	}()

	// 【接続の読み取り設定】

	// 受信可能な最大メッセージサイズを設定
	// これを超えるメッセージは自動的にエラーになります（DoS攻撃対策）
	client.Conn.SetReadLimit(maxMessageSize)

	// 読み取りのデッドライン（タイムアウト）を設定
	// 現在時刻 + pongWait（60秒）以内にメッセージが来なければタイムアウト
	client.Conn.SetReadDeadline(time.Now().Add(pongWait))

	// 【Pongハンドラーの設定】
	// クライアントからPongメッセージを受信した時に呼ばれるコールバック関数。
	// Pongを受信するたびに読み取りデッドラインをリセット（延長）します。
	// これにより、「Pongが来ている限り接続は生きている」と判断できます。
	//
	// func(string) error は、Pongメッセージの本文（通常は空）を受け取り、
	// エラーを返す関数型です。
	client.Conn.SetPongHandler(func(string) error {
		client.Conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	// 【メッセージ読み取りループ】
	for {
		// ReadMessage() は次のメッセージが来るまでブロック（待機）します。
		// 戻り値: messageType（テキスト/バイナリ）, data（メッセージ本文）, error
		// _ はmessageTypeを使わないことを示します（Goでは未使用変数はエラーになるため）
		_, data, err := client.Conn.ReadMessage()
		if err != nil {
			// 【予期しない切断のチェック】
			// IsUnexpectedCloseError は、正常な切断（GoingAway, NormalClosure）以外の
			// エラーかどうかを判定します。
			// 正常な切断: ブラウザを閉じた、明示的にclose()を呼んだ
			// 異常な切断: ネットワーク断、サーバーエラー
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				s.logger.Warn("WebSocket read error",
					zap.String("client_id", client.ID),
					zap.Error(err),
				)
			}
			// エラーが発生したらループを抜ける → defer でクリーンアップ
			return
		}

		// 【メッセージのデコード（バイナリ → 構造体）】
		// 受信したバイナリデータを、protocol.Message 構造体に変換します。
		// JSONやProtobufなどのフォーマットで送られてきたデータを解析します。
		// Decode the message
		msg, err := s.codec.Decode(data)
		if err != nil {
			s.logger.Error("Message decode error",
				zap.String("client_id", client.ID),
				zap.Error(err),
			)
			// デコードエラーの場合は接続を切らず、次のメッセージを待つ
			continue
		}

		// 【メッセージの処理】
		// デコードされたメッセージを Handler に渡して処理します。
		// Handler はメッセージの種類（速度コマンド、緊急停止など）に応じて
		// 適切な処理を行います（handler.go で実装）。
		// Handle the message
		s.handler.HandleMessage(client, msg)
	}
}

// =============================================================================
// writePump - クライアントへのメッセージ書き込みポンプ
// =============================================================================
//
// 【書き込みポンプとは？】
// サーバーからクライアントへのメッセージ送信と、
// 定期的なPingメッセージの送信を担当するゴルーチンです。
//
// 【なぜチャネルを使う？】
// gorilla/websocket は同時に複数の書き込みを許可しません。
// そのため、全ての書き込みを1つのゴルーチン（writePump）に集約し、
// チャネル（client.Send）経由でメッセージを受け取ります。
//
// 【select文による2つのイベント監視】
// 1. client.Send チャネルからメッセージが来たら送信
// 2. ticker.C からPing間隔が来たらPingを送信
func (s *WebSocketServer) writePump(client *Client) {
	// Pingを定期的に送信するためのタイマー
	ticker := time.NewTicker(pingPeriod)
	// defer で関数終了時にタイマー停止と接続クローズ
	defer func() {
		ticker.Stop()
		client.Conn.Close()
	}()

	// 【無限ループ + select で2つのイベントを監視】
	for {
		select {
		case message, ok := <-client.Send:
			// 【チャネルの受信と状態チェック】
			// ok が false の場合、チャネルが閉じられたことを意味します。
			// Hub がクライアントを登録解除する際に close(client.Send) を呼びます。

			// 書き込みデッドラインを設定（10秒以内に書き込み完了しなければタイムアウト）
			client.Conn.SetWriteDeadline(time.Now().Add(writeWait))

			if !ok {
				// チャネルが閉じられた → クライアントに切断メッセージを送信
				// CloseMessage は WebSocket の正常終了を示すフレームです
				client.Conn.WriteMessage(websocket.CloseMessage, nil)
				return
			}

			// 【BinaryMessageでメッセージを送信】
			// WebSocketには「テキストメッセージ」と「バイナリメッセージ」があります。
			// バイナリメッセージはProtobufやMessagePackなどの効率的な
			// シリアライゼーション形式に適しています。
			if err := client.Conn.WriteMessage(websocket.BinaryMessage, message); err != nil {
				// 書き込みエラー → 接続に問題があるので終了
				return
			}

		case <-ticker.C:
			// 【Pingメッセージの送信】
			// 定期的にPingを送信して、接続が生きているか確認します。
			// クライアントがPongで応答すると、readPumpのPongハンドラーが
			// 読み取りデッドラインをリセットします。
			client.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := client.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				// Ping送信失敗 → 接続に問題があるので終了
				return
			}
		}
	}
}

// =============================================================================
// HealthHandler - ヘルスチェック用HTTPハンドラー
// =============================================================================
//
// 【ヘルスチェックとは？】
// サービスが正常に動作しているかを確認するためのエンドポイントです。
// Kubernetes、Docker、ロードバランサーなどのインフラストラクチャが
// 定期的にこのエンドポイントにアクセスして、サービスの状態を監視します。
//
// 【レスポンス】
// HTTP 200 OK + JSON {"status":"ok","service":"gateway"}
// ステータスコード200は「正常」を意味します。
func (s *WebSocketServer) HealthHandler(w http.ResponseWriter, r *http.Request) {
	// Content-Type ヘッダーを設定（レスポンスがJSON形式であることを示す）
	w.Header().Set("Content-Type", "application/json")
	// ステータスコード200（OK）を設定
	w.WriteHeader(http.StatusOK)
	// JSONレスポンスボディを書き込み
	// バッククォート（`...`）はGoの「raw stringリテラル」で、エスケープ不要です
	w.Write([]byte(`{"status":"ok","service":"gateway"}`))
}

// =============================================================================
// generateClientID - 一意なクライアントIDを生成する関数
// =============================================================================
//
// 【ID生成の仕組み】
// "client-" + 日時（YYYYMMDDHHmmss形式） + "-" + ランダム6文字
// 例: "client-20260215143022-abc123"
//
// 【time.Now().Format() について】
// Goの日時フォーマットは独特で、「2006年1月2日 15時4分5秒」という
// 特定の日時（Goの誕生日に近い参照時刻）を使ってフォーマットを指定します。
// "20060102150405" = YYYYMMDDHHMMSS
func generateClientID() string {
	return "client-" + time.Now().Format("20060102150405") + "-" + randomString(6)
}

// =============================================================================
// randomString - ランダムな文字列を生成する関数
// =============================================================================
//
// 【注意】
// この実装は簡易的なものです。time.Now().UnixNano() を使っているため、
// 厳密にはランダムではなく、セキュリティ目的には適しません。
// 本番環境では crypto/rand パッケージを使うべきです。
//
// 【rangeの使い方】
// for i := range b は、スライス b の各インデックスでループします。
// Go の range は配列・スライス・マップ・チャネルに使えます。
func randomString(n int) string {
	// 使用可能な文字（英小文字 + 数字）
	const letters = "abcdefghijklmnopqrstuvwxyz0123456789"

	// n バイトのスライスを作成
	b := make([]byte, n)

	// 各位置にランダムな文字を割り当て
	for i := range b {
		// UnixNano() を文字数で割った余り（%）でインデックスを決定
		// int64(len(letters)) で型をint64に合わせています
		b[i] = letters[time.Now().UnixNano()%int64(len(letters))]
		// 1ナノ秒待つことで、次の呼び出しで異なる値を得る
		// （簡易な実装であり、本番には不向き）
		time.Sleep(time.Nanosecond)
	}

	// []byte を string に変換して返す
	return string(b)
}
