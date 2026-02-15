// =============================================================================
// ファイル: handler.go
// 概要: WebSocketメッセージの処理ハンドラー
//
// このファイルは、WebSocket経由で受信した全てのメッセージを処理する
// 中心的なファイルです。メッセージの種類に応じて適切な処理を行います。
//
// 【メッセージルーティング（振り分け）】
// HandleMessage() が「ルーター」として機能し、メッセージタイプに応じて
// 個別のハンドラー関数に処理を振り分けます。
//
// 対応するメッセージ:
//   - auth:         認証（ログイン）
//   - velocity:     速度コマンド（ロボットの移動制御）
//   - estop:        緊急停止
//   - nav_goal:     ナビゲーション目標地点の設定
//   - nav_cancel:   ナビゲーションのキャンセル
//   - op_lock:      操作ロックの取得
//   - op_unlock:    操作ロックの解放
//   - ping:         接続確認
//
// 【安全パイプライン - 速度コマンドの処理フロー】
// フロントエンドからの速度コマンドは、以下の安全チェックを通過します:
//
//	受信 → 認証チェック → E-Stop確認 → 操作ロック確認
//	→ 速度制限適用 → アダプターに送信 → ウォッチドッグ記録
//	→ Redis配信 → ACK返送
//
// 各段階で問題があれば、エラーメッセージを返して処理を中断します。
// =============================================================================
package server

// =============================================================================
// インポートセクション
// =============================================================================
import (
	// "context": ゴルーチン間のキャンセル伝搬に使用。
	// context.Background() でルートcontextを作成します。
	"context"

	// "time": タイムスタンプの取得やRFC3339形式への変換に使用。
	"time"

	// adapter: ロボットアダプターのインターフェースと型定義。
	// Command（コマンド）、SensorData（センサーデータ）の構造体を使います。
	"github.com/robot-ai-webapp/gateway/internal/adapter"

	// protocol: メッセージプロトコルの定義。
	// メッセージタイプの定数（MsgTypeAuth等）とメッセージ構造体を提供します。
	"github.com/robot-ai-webapp/gateway/internal/protocol"

	// safety: 安全機能パッケージ。
	// E-Stop（緊急停止）、速度制限、タイムアウトウォッチドッグ、操作ロックを提供します。
	"github.com/robot-ai-webapp/gateway/internal/safety"

	// zap: 構造化ログライブラリ
	"go.uber.org/zap"
)

// =============================================================================
// RedisPublisher インターフェース
// =============================================================================
//
// 【インターフェース（interface）とは？】
// GoのインターフェースはJavaのインターフェースに似ていますが、
// 「暗黙的実装」という大きな違いがあります。
// ある型がインターフェースの全メソッドを持っていれば、
// "implements" と宣言しなくても自動的にそのインターフェースを満たします。
//
// 【依存性注入（Dependency Injection, DI）】
// このインターフェースは「依存性注入」のために使われます。
// Handler は具体的な Redis 実装に依存せず、インターフェースに依存します。
// これにより:
//   - テスト時: モック（偽の）実装を注入できる
//   - 本番時: 実際の Redis 実装を注入できる
//
// 【なぜインターフェースを使う？】
// 1. テストが書きやすくなる（モックに差し替え可能）
// 2. 実装の差し替えが容易（Redis → Kafka への変更など）
// 3. 関心の分離（Handler は配信の「方法」を知る必要がない）

// RedisPublisher interface for dependency injection
type RedisPublisher interface {
	PublishSensorData(ctx context.Context, robotID string, data adapter.SensorData) error
	PublishCommand(ctx context.Context, robotID string, cmd adapter.Command) error
}

// =============================================================================
// Handler 構造体
// =============================================================================
//
// 【この構造体の役割】
// WebSocketメッセージの処理を一手に引き受けるハンドラーです。
// 各種安全機能やアダプター、配信機能への参照を保持します。
//
// 【フィールドの一覧と役割】
// hub:       クライアント管理（ブロードキャスト、購読管理）
// registry:  ロボットアダプターの管理（ロボットIDからアダプターを取得）
// estop:     緊急停止の管理
// velLimit:  速度制限の管理
// watchdog:  タイムアウトウォッチドッグ（コマンドが来なくなったら停止）
// opLock:    操作ロック（複数ユーザーの排他制御）
// publisher: Redisへのデータ配信
// codec:     メッセージのエンコード/デコード
// logger:    ログ出力

// Handler processes incoming WebSocket messages
type Handler struct {
	hub       *Hub
	registry  *adapter.Registry
	estop     *safety.EStopManager
	velLimit  *safety.VelocityLimiter
	watchdog  *safety.TimeoutWatchdog
	opLock    *safety.OperationLock
	publisher RedisPublisher
	codec     *protocol.Codec
	logger    *zap.Logger
}

// =============================================================================
// NewHandler - ハンドラーのコンストラクタ
// =============================================================================
//
// 全ての依存コンポーネントを引数で受け取ります（依存性注入）。
// これにより、テスト時にモック実装を簡単に注入できます。
//
// 【引数の数が多い理由】
// Go言語にはコンストラクタの引数に名前付きパラメータがないため、
// 依存コンポーネントが多い場合は引数が長くなりがちです。
// 代替案として「Options パターン」（Functional Options）がありますが、
// ここではシンプルに全て引数で渡しています。

// NewHandler creates a new message handler
func NewHandler(
	hub *Hub,
	registry *adapter.Registry,
	estop *safety.EStopManager,
	velLimit *safety.VelocityLimiter,
	watchdog *safety.TimeoutWatchdog,
	opLock *safety.OperationLock,
	publisher RedisPublisher,
	logger *zap.Logger,
) *Handler {
	return &Handler{
		hub:       hub,
		registry:  registry,
		estop:     estop,
		velLimit:  velLimit,
		watchdog:  watchdog,
		opLock:    opLock,
		publisher: publisher,
		codec:     protocol.NewCodec(),
		logger:    logger,
	}
}

// =============================================================================
// HandleMessage - メッセージルーター（振り分け処理）
// =============================================================================
//
// 【switch文によるメッセージルーティング】
// 受信したメッセージのType（種類）に基づいて、対応するハンドラー関数に
// 処理を振り分けます。これは「ルーター」や「ディスパッチャー」と呼ばれるパターンです。
//
// 【msg.Type の型】
// protocol.MessageType 型（おそらくstringの型エイリアス）で、
// protocol パッケージで定数として定義されています。
// 例: protocol.MsgTypeAuth = "auth"
//
// 【default節】
// 未知のメッセージタイプが来た場合、警告ログを出力して無視します。
// 将来の拡張性を考えると、エラーではなく警告にしておくのが安全です。

// HandleMessage routes messages to the appropriate handler
func (h *Handler) HandleMessage(client *Client, msg *protocol.Message) {
	switch msg.Type {
	case protocol.MsgTypeAuth:
		h.handleAuth(client, msg)
	case protocol.MsgTypeVelocityCommand:
		h.handleVelocityCommand(client, msg)
	case protocol.MsgTypeEmergencyStop:
		h.handleEStop(client, msg)
	case protocol.MsgTypeNavigationGoal:
		h.handleNavigationGoal(client, msg)
	case protocol.MsgTypeNavigationCancel:
		h.handleNavigationCancel(client, msg)
	case protocol.MsgTypeOperationLock:
		h.handleOperationLock(client, msg)
	case protocol.MsgTypeOperationUnlock:
		h.handleOperationUnlock(client, msg)
	case protocol.MsgTypePing:
		h.sendPong(client, msg)
	default:
		h.logger.Warn("Unknown message type", zap.String("type", string(msg.Type)))
	}
}

// =============================================================================
// handleAuth - 認証（ログイン）処理
// =============================================================================
//
// 【認証フロー】
// 1. PayloadからJWTトークンを取得
// 2. トークンを検証（現在はプレースホルダー）
// 3. クライアントの認証状態を更新
// 4. 指定されたロボットへの購読を設定
// 5. 接続状態レスポンスを返送
//
// 【型アサーション msg.Payload["token"].(string)】
// msg.Payload は map[string]any 型なので、取得した値は any 型です。
// .(string) で「この値はstring型のはず」と宣言します（型アサーション）。
//
// 2値の型アサーション: token, ok := value.(string)
// - ok が true: アサーション成功（token にstring値が入る）
// - ok が false: アサーション失敗（token は空文字列""が入る）
//
// 1値の型アサーション: token := value.(string)
// - 失敗するとpanic（プログラムが強制終了）するので危険！
// - 必ず2値の形式を使いましょう。
func (h *Handler) handleAuth(client *Client, msg *protocol.Message) {
	// Extract token from payload
	// Payload から "token" キーの値を取得し、string型へアサーション
	token, _ := msg.Payload["token"].(string)
	if token == "" {
		// トークンが空なら認証失敗
		h.sendError(client, msg.RobotID, "Missing auth token")
		return
	}

	// TODO: Validate JWT token
	// TODO: 本来はここでJWTトークンの検証を行います
	// JWTトークンには、ユーザーID、権限、有効期限などの情報が含まれています。
	// 現在はプレースホルダー（仮）実装です。
	client.UserID = "user-from-token" // Placeholder
	client.Authenticated = true

	// Auto-subscribe to default robot if specified
	// ロボットIDが指定されていたら、そのロボットのデータ購読を開始
	if msg.RobotID != "" {
		h.hub.SubscribeClient(client, msg.RobotID)
	}

	h.logger.Info("Client authenticated",
		zap.String("client_id", client.ID),
		zap.String("user_id", client.UserID),
	)

	// Send connection status
	// 接続状態のレスポンスメッセージを作成して送信
	// protocol.NewMessage() でメッセージの雛形を作成し、Payloadにデータを追加します。
	response := protocol.NewMessage(protocol.MsgTypeConnectionStatus, msg.RobotID)
	response.Payload["authenticated"] = true
	response.Payload["client_id"] = client.ID
	h.sendToClient(client, response)
}

// =============================================================================
// handleVelocityCommand - 速度コマンド処理（安全パイプライン）
// =============================================================================
//
// 【安全パイプライン（Safety Pipeline）】
// これは最も重要な関数の一つです。ロボットの移動コマンドを処理しますが、
// 安全のために多段階のチェックを行います。
//
// 【処理フロー（安全パイプライン）】
//
//  1. 認証チェック     - ログイン済みか？
//  2. ロボットID確認   - どのロボットへのコマンドか？
//  3. E-Stopチェック   - 緊急停止中でないか？
//  4. 操作ロック確認   - 他のユーザーが操作中でないか？
//  5. 速度制限適用     - 安全な範囲内に速度を制限
//  6. コマンド送信     - アダプター経由でロボットに送信
//  7. ウォッチドッグ記録 - タイムアウト監視のために記録
//  8. Redis配信       - 他のサービスにコマンドを通知
//  9. ACK返送         - クライアントに確認応答を返す
//
// 各段階で問題が検出されると、エラーメッセージを返して処理を中断（early return）します。
// これは「ガード節（guard clause）」パターンと呼ばれ、ネストを深くせずに
// エラーチェックを行う手法です。
func (h *Handler) handleVelocityCommand(client *Client, msg *protocol.Message) {
	// ===== 段階1: 認証チェック =====
	// ログインしていないユーザーからのコマンドは拒否します。
	if !client.Authenticated {
		h.sendError(client, msg.RobotID, "Not authenticated")
		return
	}

	// ===== 段階2: ロボットID確認 =====
	robotID := msg.RobotID
	if robotID == "" {
		h.sendError(client, "", "Missing robot_id")
		return
	}

	// ===== 段階3: E-Stop（緊急停止）チェック =====
	// Check E-Stop
	// E-Stopが有効になっている場合、全てのコマンドを拒否します。
	// 安全のため、E-Stopは最も優先度が高いチェックです。
	if h.estop.IsActive(robotID) {
		h.sendError(client, robotID, "E-Stop is active")
		return
	}

	// ===== 段階4: 操作ロック確認 =====
	// 【操作ロックとは？】
	// 複数のユーザーが同時に同じロボットを操作するのを防ぐ仕組みです。
	// 例えば、ユーザーAがロボットを操作中にユーザーBが同じロボットを
	// 操作しようとすると、衝突が起きます。
	//
	// CheckLock(): このユーザーがロックを持っているか確認
	// Acquire(): ロックの取得を試みる（既に他のユーザーが持っていたらエラー）
	// Check operation lock
	if !h.opLock.CheckLock(robotID, client.UserID) {
		// Try to acquire lock
		// ロックを持っていない場合、取得を試みる
		if _, err := h.opLock.Acquire(robotID, client.UserID); err != nil {
			h.sendError(client, robotID, "Operation locked: "+err.Error())
			return
		}
	}

	// ===== 段階5: 速度値の抽出 =====
	// Extract velocity values
	// Payload から3つの速度成分を取得します。
	// toFloat() は any型 → float64 への安全な変換関数（このファイルの末尾で定義）
	input := safety.VelocityInput{
		LinearX:  toFloat(msg.Payload["linear_x"]),  // 前進/後退速度
		LinearY:  toFloat(msg.Payload["linear_y"]),  // 横方向速度
		AngularZ: toFloat(msg.Payload["angular_z"]), // 回転速度
	}

	// ===== 段階6: 速度制限の適用 =====
	// 【速度リミッターとは？】
	// ユーザーが指定した速度がロボットの安全な範囲を超えている場合、
	// 自動的に安全な値にクランプ（制限）します。
	// 例: 最大速度1.0m/sのロボットに2.0m/sのコマンドが来たら、1.0m/sに制限
	//
	// limited.Clamped が true なら、速度が制限されたことを示します。
	// Apply velocity limiting
	limited := h.velLimit.Limit(input)

	// ===== 段階7: アダプターの取得とコマンド送信 =====
	// 【レジストリパターン】
	// registry はロボットIDとアダプターの対応を管理するマップです。
	// GetAdapter() は、指定されたIDに対応するアダプターを返します。
	//
	// 【多値戻り値: adp, ok】
	// Goのmap参照と同様に、値が存在するかどうかをboolで返します。
	// ok が false なら、そのロボットIDは登録されていません。
	// Send to adapter
	adp, ok := h.registry.GetAdapter(robotID)
	if !ok {
		h.sendError(client, robotID, "Robot not found")
		return
	}

	// コマンド構造体を作成
	cmd := adapter.Command{
		RobotID: robotID,
		Type:    "velocity",
		Payload: map[string]any{
			"linear_x":  limited.LinearX,  // 制限後の前進速度
			"linear_y":  limited.LinearY,  // 制限後の横方向速度
			"angular_z": limited.AngularZ, // 制限後の回転速度
		},
		Timestamp: time.Now().UnixMilli(), // ミリ秒単位のタイムスタンプ
	}

	// 【context.Background()】
	// 最もベースとなる空のcontextを作成します。
	// キャンセルやタイムアウトの設定がないシンプルなcontextです。
	// 短時間で完了する処理にはこれで十分です。
	ctx := context.Background()

	// アダプターにコマンドを送信
	if err := adp.SendCommand(ctx, cmd); err != nil {
		h.sendError(client, robotID, "Command failed: "+err.Error())
		return
	}

	// ===== 段階8: ウォッチドッグにコマンドを記録 =====
	// 【ウォッチドッグ（タイムアウト監視）とは？】
	// 一定時間コマンドが来なかった場合、自動的にロボットを停止させる安全機能です。
	// 例えば、ユーザーがブラウザを閉じてしまった場合、ロボットが暴走するのを防ぎます。
	// RecordCommand() でコマンドの受信時刻を記録し、タイムアウトタイマーをリセットします。
	// Record command for watchdog timeout
	h.watchdog.RecordCommand(robotID)

	// ===== 段階9: Redisにコマンドを配信 =====
	// 他のマイクロサービス（ログ記録、分析など）にコマンド情報を配信します。
	// publisher が nil の場合（Redisが設定されていない場合）はスキップします。
	//
	// 【_ でエラーを無視】
	// _ = h.publisher.PublishCommand(...) は「エラーがあっても無視する」という意味です。
	// Redis配信は「ベストエフォート（最善努力）」で行い、失敗してもコマンド自体は
	// 実行済みなので、ここではエラーを無視します。
	// Publish to Redis
	if h.publisher != nil {
		_ = h.publisher.PublishCommand(ctx, robotID, cmd)
	}

	// ===== 段階10: ACK（確認応答）をクライアントに返送 =====
	// コマンドが正常に処理されたことをクライアントに通知します。
	// "clamped" フィールドで、速度が制限されたかどうかも伝えます。
	// Send ack
	ack := protocol.NewMessage(protocol.MsgTypeCommandAck, robotID)
	ack.Payload["command"] = "velocity"
	ack.Payload["clamped"] = limited.Clamped
	h.sendToClient(client, ack)
}

// =============================================================================
// handleEStop - 緊急停止（E-Stop）処理
// =============================================================================
//
// 【E-Stop（Emergency Stop, 緊急停止）とは？】
// ロボットの動作を即座に停止する最も重要な安全機能です。
// 工業用ロボットでは法律で義務付けられていることもあります。
//
// 【2つのモード】
// 1. 単体E-Stop: 特定のロボット（msg.RobotID指定）のみ停止
// 2. 全体E-Stop: ロボットID未指定の場合、全てのロボットを停止
//
// 【activate パラメータ】
// - true:  E-Stopを有効化（停止）
// - false: E-Stopを解除（復帰）
//
// 【ブロードキャスト】
// E-Stop発動/解除時は、全クライアントに安全アラートを配信します。
// これにより、全てのユーザーがE-Stopの状態変化を把握できます。
func (h *Handler) handleEStop(client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, msg.RobotID, "Not authenticated")
		return
	}

	// 型アサーションで activate（有効化フラグ）と reason（理由）を取得
	// .(bool) や .(string) が失敗した場合、ok は false になり、
	// activate は false（ゼロ値）、reason は ""（ゼロ値）になります。
	activate, _ := msg.Payload["activate"].(bool)
	reason, _ := msg.Payload["reason"].(string)
	ctx := context.Background()

	if activate {
		// 【E-Stopの有効化】
		if msg.RobotID != "" {
			// Single robot E-Stop
			// 特定のロボットのみ緊急停止
			if err := h.estop.Activate(ctx, msg.RobotID, client.UserID, reason); err != nil {
				h.sendError(client, msg.RobotID, "E-Stop failed: "+err.Error())
				return
			}
		} else {
			// All robots E-Stop
			// 全てのロボットを緊急停止
			h.estop.ActivateAll(ctx, client.UserID, reason)
		}

		// Broadcast safety alert
		// 安全アラートを全クライアントにブロードキャスト
		alert := protocol.NewMessage(protocol.MsgTypeSafetyAlert, msg.RobotID)
		alert.Payload["type"] = "estop_activated"
		alert.Payload["reason"] = reason
		alert.Payload["user_id"] = client.UserID
		h.broadcastAlert(alert)
	} else {
		// 【E-Stopの解除】
		if msg.RobotID != "" {
			h.estop.Release(msg.RobotID, client.UserID)
		}

		// E-Stop解除のアラートを配信
		alert := protocol.NewMessage(protocol.MsgTypeSafetyAlert, msg.RobotID)
		alert.Payload["type"] = "estop_released"
		alert.Payload["user_id"] = client.UserID
		h.broadcastAlert(alert)
	}
}

// =============================================================================
// handleNavigationGoal - ナビゲーション目標地点の処理
// =============================================================================
//
// 【ナビゲーションとは？】
// ロボットを指定した座標に自律的に移動させる機能です。
// ユーザーが地図上でクリックすると、そのX,Y座標がこの関数に送られます。
// 実際のロボットでは、パスプランニング（経路計画）を行って目標地点まで
// 自動で移動します。
//
// 【現在の実装】
// ログを出力してACKを返すのみの簡易実装です。
// 将来的にはROSのmove_baseやNav2への連携が実装される予定です。
func (h *Handler) handleNavigationGoal(client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, msg.RobotID, "Not authenticated")
		return
	}

	// zap.Any() は任意の型の値をログに出力できるフィールドです
	h.logger.Info("Navigation goal received",
		zap.String("robot_id", msg.RobotID),
		zap.Any("payload", msg.Payload),
	)

	ack := protocol.NewMessage(protocol.MsgTypeCommandAck, msg.RobotID)
	ack.Payload["command"] = "nav_goal"
	h.sendToClient(client, ack)
}

// =============================================================================
// handleNavigationCancel - ナビゲーションキャンセル処理
// =============================================================================
//
// 進行中のナビゲーション（自律移動）を中止します。
// ロボットはその場で停止します。
func (h *Handler) handleNavigationCancel(client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, msg.RobotID, "Not authenticated")
		return
	}

	h.logger.Info("Navigation cancelled",
		zap.String("robot_id", msg.RobotID),
	)

	ack := protocol.NewMessage(protocol.MsgTypeCommandAck, msg.RobotID)
	ack.Payload["command"] = "nav_cancel"
	h.sendToClient(client, ack)
}

// =============================================================================
// handleOperationLock - 操作ロックの取得処理
// =============================================================================
//
// 【操作ロック（Operation Lock）とは？】
// 1人のユーザーだけがロボットを操作できるように排他制御する仕組みです。
// 例えば、教室でロボットを使う場合、先生だけが操作できるようにロックします。
//
// 【Acquire（取得）の仕組み】
// opLock.Acquire() が成功すると、指定したユーザーだけが
// そのロボットを操作できるようになります。
// ロックには有効期限（ExpiresAt）があり、一定時間後に自動解除されます。
//
// 【lock構造体】
// Acquire() が返す lock にはロック情報（所有者、有効期限など）が含まれます。
// time.Format(time.RFC3339) で有効期限を標準的な日時形式に変換して返します。
// RFC3339は "2026-02-15T14:30:00Z" のような形式です。
func (h *Handler) handleOperationLock(client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, msg.RobotID, "Not authenticated")
		return
	}

	// ロックの取得を試みる
	lock, err := h.opLock.Acquire(msg.RobotID, client.UserID)
	if err != nil {
		// 他のユーザーが既にロックを持っている場合など
		h.sendError(client, msg.RobotID, err.Error())
		return
	}

	// ロック状態のレスポンスを返す
	response := protocol.NewMessage(protocol.MsgTypeLockStatus, msg.RobotID)
	response.Payload["locked"] = true
	response.Payload["user_id"] = lock.UserID
	// 有効期限をRFC3339形式の文字列に変換
	response.Payload["expires_at"] = lock.ExpiresAt.Format(time.RFC3339)
	h.sendToClient(client, response)
}

// =============================================================================
// handleOperationUnlock - 操作ロックの解放処理
// =============================================================================
//
// ロボットの操作ロックを解放します。
// ロックを所有しているユーザーのみが解放できます。
// 解放が成功すると、他のユーザーがそのロボットを操作できるようになります。
func (h *Handler) handleOperationUnlock(client *Client, msg *protocol.Message) {
	if !client.Authenticated {
		h.sendError(client, msg.RobotID, "Not authenticated")
		return
	}

	// ロックの解放を試みる
	if err := h.opLock.Release(msg.RobotID, client.UserID); err != nil {
		// ロックを持っていない or 他のユーザーのロック
		h.sendError(client, msg.RobotID, err.Error())
		return
	}

	// ロック解除のレスポンスを返す
	response := protocol.NewMessage(protocol.MsgTypeLockStatus, msg.RobotID)
	response.Payload["locked"] = false
	h.sendToClient(client, response)
}

// =============================================================================
// sendError - エラーメッセージの送信ヘルパー
// =============================================================================
//
// 【ヘルパー関数とは？】
// 繰り返し使う処理をまとめた小さな関数です。
// エラーの送信ロジックを一箇所にまとめることで:
// - コードの重複を減らす（DRY原則: Don't Repeat Yourself）
// - エラーフォーマットの一貫性を保つ
// - 変更が必要なとき一箇所の修正で済む
func (h *Handler) sendError(client *Client, robotID, errMsg string) {
	msg := protocol.NewMessage(protocol.MsgTypeError, robotID)
	msg.Error = errMsg
	h.sendToClient(client, msg)
}

// =============================================================================
// sendPong - Pong（接続確認応答）の送信
// =============================================================================
//
// クライアントからのPingメッセージに対してPongを返します。
// アプリケーションレベルのPing/Pongです（WebSocketプロトコルレベルの
// Ping/Pongとは別のものです）。
func (h *Handler) sendPong(client *Client, msg *protocol.Message) {
	pong := protocol.NewMessage(protocol.MsgTypePong, "")
	h.sendToClient(client, pong)
}

// =============================================================================
// sendToClient - 特定クライアントへのメッセージ送信
// =============================================================================
//
// 【処理の流れ】
// 1. protocol.Message をバイナリデータにエンコード
// 2. Hub経由でクライアントのSendチャネルにデータを送信
// 3. writePump がチャネルからデータを取り出してWebSocket経由で送信
//
// 【なぜ直接送信しない？】
// gorilla/websocket は同時書き込みを許可しないため、全ての書き込みを
// writePump（1つのゴルーチン）に集約する必要があります。
// チャネルを使うことで、複数のゴルーチンから安全にメッセージを送信できます。
func (h *Handler) sendToClient(client *Client, msg *protocol.Message) {
	data, err := h.codec.Encode(msg)
	if err != nil {
		h.logger.Error("Failed to encode message", zap.Error(err))
		return
	}
	h.hub.SendToClient(client, data)
}

// =============================================================================
// broadcastAlert - 全クライアントへのアラート配信
// =============================================================================
//
// E-Stopの発動/解除など、全ユーザーに通知すべき安全アラートを
// 接続中の全クライアントに配信します。
//
// 【ブロードキャストとは？】
// 全ての接続先に同じメッセージを送信することです。
// テレビの放送（broadcast）と同じ概念です。
func (h *Handler) broadcastAlert(msg *protocol.Message) {
	data, err := h.codec.Encode(msg)
	if err != nil {
		h.logger.Error("Failed to encode alert", zap.Error(err))
		return
	}
	h.hub.BroadcastToAll(data)
}

// =============================================================================
// toFloat - any型からfloat64への安全な型変換ヘルパー関数
// =============================================================================
//
// 【型スイッチ（type switch）による安全な型変換】
// JSONデコード時の数値型は通常float64ですが、他の数値型で来る可能性もあります。
// この関数はどの型で来ても安全にfloat64に変換します。
//
// 【mock_adapter.go の toFloat64 と同じ？】
// はい、ほぼ同じ関数ですが、パッケージが異なるため別途定義が必要です。
// Go言語では、パッケージを超えた関数共有にはexport（大文字開始）が必要ですが、
// このようなユーティリティ関数は各パッケージのローカルに持つことも一般的です。
func toFloat(v any) float64 {
	switch val := v.(type) {
	case float64:
		return val
	case float32:
		return float64(val)
	case int:
		return float64(val)
	case int64:
		return float64(val)
	default:
		return 0.0
	}
}
