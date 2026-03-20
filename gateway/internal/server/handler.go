// =============================================================================
// Step 5: メッセージハンドラー — 安全パイプライン統合版
// =============================================================================
//
// 【Step 4 からの変更】
// Step 4: websocket.go の readPump 内で直接メッセージを処理
// Step 5: Handler 構造体に切り出し、安全パイプラインを統合
//
// 【安全パイプラインの流れ】
//
//   クライアント → readPump → Handler
//                                ↓
//                   ┌─── Watchdog.Ping()（活動記録）
//                   │
//                   ├─── EStop チェック（発動中はコマンド拒否）
//                   │
//                   ├─── OperationLock チェック（排他制御）
//                   │
//                   ├─── VelocityLimiter（速度制限）
//                   │
//                   └─── Adapter.SendCommand()（ロボットに送信）
//
// 各段階で「安全でない場合はエラー応答を返す」。
// すべてのチェックをパスしたコマンドだけがロボットに届く。
//
// =============================================================================
package server

import (
	"context"
	"fmt"
	"log"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
	"github.com/robot-ai-webapp/gateway/internal/safety"
)

// =============================================================================
// Handler — メッセージ処理と安全パイプラインの統合
// =============================================================================
//
// 【Handler の依存関係】
// Handler は以下のコンポーネントに依存する:
//   - adapter: ロボット制御
//   - estop: 緊急停止管理
//   - limiter: 速度制限
//   - watchdog: タイムアウト監視
//   - opLock: 操作排他制御
//   - hub: メッセージ配信
//
// すべてコンストラクタで注入（Dependency Injection）。
// Handler 自体は状態を持たない（Stateless）。
type Handler struct {
	adapter  adapter.RobotAdapter
	estop    *safety.EStopManager
	limiter  *safety.VelocityLimiter
	watchdog *safety.TimeoutWatchdog
	opLock   *safety.OperationLock
	hub      *Hub
	codec    protocol.Codec
}

// NewHandler — コンストラクタ
func NewHandler(
	robotAdapter adapter.RobotAdapter,
	estop *safety.EStopManager,
	limiter *safety.VelocityLimiter,
	watchdog *safety.TimeoutWatchdog,
	opLock *safety.OperationLock,
	hub *Hub,
) *Handler {
	return &Handler{
		adapter:  robotAdapter,
		estop:    estop,
		limiter:  limiter,
		watchdog: watchdog,
		opLock:   opLock,
		hub:      hub,
		codec:    protocol.NewJSONCodec(),
	}
}

// =============================================================================
// HandleMessage — メッセージを Type に応じて処理
// =============================================================================
//
// 【clientID を引数に取る理由】
// 誰からのメッセージか識別するため。
// - OperationLock: 誰がロックを持っているか
// - ログ: どのクライアントのメッセージか
// - 応答: 送信元に返す
func (h *Handler) HandleMessage(clientID string, msg protocol.Message) {
	// --- ウォッチドッグを更新 ---
	// コマンド受信 = クライアントが生きている証拠
	h.watchdog.Ping()

	log.Printf("📨 [%s] 受信: type=%s", clientID, msg.Type)

	switch msg.Type {
	case protocol.TypeVelocityCmd:
		h.handleVelocityCmd(clientID, msg)

	case "estop":
		h.handleEStop(clientID)

	case "estop_release":
		h.handleEStopRelease(clientID)

	case "connect":
		h.handleConnect(clientID)

	case "disconnect":
		h.handleDisconnect(clientID)

	case "status":
		h.handleStatusRequest(clientID)

	default:
		log.Printf("⚠️ [%s] 未対応タイプ: %s", clientID, msg.Type)
		errMsg := protocol.NewError(404, fmt.Sprintf("未対応メッセージタイプ: %s", msg.Type))
		h.sendToClient(clientID, errMsg)
	}
}

// =============================================================================
// handleVelocityCmd — 安全パイプラインを通して速度コマンドを処理
// =============================================================================
//
// 【パイプラインの各段階】
// 1. Payload デコード
// 2. VelocityLimiter でクランプ（E-Stop チェックも含む）
// 3. Adapter に送信
// 4. 成功応答を返す
func (h *Handler) handleVelocityCmd(clientID string, msg protocol.Message) {
	// --- 1. Payload のデコード ---
	payload, ok := msg.Payload.(protocol.VelocityPayload)
	if !ok {
		errMsg := protocol.NewError(400, "velocity_cmd のペイロード形式が不正です")
		h.sendToClient(clientID, errMsg)
		return
	}

	// --- 2. 速度制限 ---
	// VelocityLimiter 内で E-Stop チェックとクランプを行う
	limited, err := h.limiter.Limit(safety.Velocity{
		LinearX:  payload.LinearX,
		LinearY:  payload.LinearY,
		AngularZ: payload.AngularZ,
	})
	if err != nil {
		log.Printf("⚠️ [%s] 速度コマンド拒否: %v", clientID, err)
		errMsg := protocol.NewError(403, err.Error())
		h.sendToClient(clientID, errMsg)
		return
	}

	// --- 3. Adapter にコマンド送信 ---
	cmd := adapter.Command{
		Type: "velocity",
		Payload: map[string]any{
			"linear_x":  limited.LinearX,
			"linear_y":  limited.LinearY,
			"angular_z": limited.AngularZ,
		},
	}

	if err := h.adapter.SendCommand(context.Background(), cmd); err != nil {
		log.Printf("⚠️ [%s] コマンド送信エラー: %v", clientID, err)
		errMsg := protocol.NewError(500, fmt.Sprintf("コマンド送信失敗: %v", err))
		h.sendToClient(clientID, errMsg)
		return
	}

	// --- 4. 成功応答 ---
	description := describeVelocity(protocol.VelocityPayload{
		LinearX:  limited.LinearX,
		LinearY:  limited.LinearY,
		AngularZ: limited.AngularZ,
	})
	ack := protocol.NewCommandAck("robot-01", "executing", description)
	h.sendToClient(clientID, ack)
}

// =============================================================================
// handleEStop — 緊急停止の発動
// =============================================================================
//
// 【E-Stop の発動フロー】
// 1. EStopManager.Activate() で状態を更新
// 2. Adapter.EmergencyStop() でロボットを物理停止
// 3. OperationLock を強制解放（E-Stop が最優先）
// 4. 全クライアントにブロードキャスト通知
func (h *Handler) handleEStop(clientID string) {
	// E-Stop 発動
	h.estop.Activate(fmt.Sprintf("クライアント %s の操作", clientID))

	// ロボットの物理停止
	if err := h.adapter.EmergencyStop(context.Background()); err != nil {
		log.Printf("⚠️ 緊急停止エラー: %v", err)
	}

	// 操作ロックを強制解放
	h.opLock.ForceUnlock("E-Stop 発動")

	// 全クライアントに通知
	notification := protocol.NewCommandAck("robot-01", "stopped", "🛑 緊急停止が発動しました")
	h.hub.Broadcast(notification)

	// 安全状態を全クライアントに配信
	h.broadcastSafetyStatus()
}

// =============================================================================
// handleEStopRelease — 緊急停止の解除（Step 5 で新規追加）
// =============================================================================
func (h *Handler) handleEStopRelease(clientID string) {
	h.estop.Deactivate(fmt.Sprintf("クライアント %s の操作", clientID))

	ack := protocol.NewCommandAck("robot-01", "estop_released", "✅ 緊急停止を解除しました")
	h.hub.Broadcast(ack)

	h.broadcastSafetyStatus()
}

// =============================================================================
// handleConnect / handleDisconnect — ロボット接続管理
// =============================================================================
func (h *Handler) handleConnect(clientID string) {
	if err := h.adapter.Connect(context.Background(), nil); err != nil {
		errMsg := protocol.NewError(500, fmt.Sprintf("接続失敗: %v", err))
		h.sendToClient(clientID, errMsg)
		return
	}

	ack := protocol.NewCommandAck("robot-01", "connected", "ロボットに接続しました")
	h.hub.Broadcast(ack)
}

func (h *Handler) handleDisconnect(clientID string) {
	if err := h.adapter.Disconnect(context.Background()); err != nil {
		errMsg := protocol.NewError(500, fmt.Sprintf("切断失敗: %v", err))
		h.sendToClient(clientID, errMsg)
		return
	}

	ack := protocol.NewCommandAck("robot-01", "disconnected", "ロボットから切断しました")
	h.hub.Broadcast(ack)
}

// =============================================================================
// handleStatusRequest — 安全状態の問い合わせ（Step 5 新規）
// =============================================================================
//
// 【status メッセージ】
// クライアントが接続直後に安全状態を問い合わせるために使う。
// E-Stop の状態、速度制限、操作ロックの情報を返す。
func (h *Handler) handleStatusRequest(clientID string) {
	maxLin, maxAng := h.limiter.GetLimits()
	lockStatus := h.opLock.Status()

	status := protocol.Message{
		Type:    "safety_status",
		RobotID: "robot-01",
		Payload: map[string]any{
			"estop":    h.estop.Status(),
			"velocity_limits": map[string]any{
				"max_linear":  maxLin,
				"max_angular": maxAng,
			},
			"operation_lock": map[string]any{
				"locked":    lockStatus.Locked,
				"owner":     lockStatus.Owner,
				"operation": lockStatus.Operation,
			},
			"adapter_connected": h.adapter.IsConnected(),
		},
	}
	h.sendToClient(clientID, status)
}

// =============================================================================
// broadcastSafetyStatus — 全クライアントに安全状態を配信
// =============================================================================
//
// 【安全状態のブロードキャスト】
// E-Stop の発動/解除など、安全に関する状態変化は全クライアントに通知する。
// 1クライアントが E-Stop を発動したら、全員がその状態を知る必要がある。
func (h *Handler) broadcastSafetyStatus() {
	maxLin, maxAng := h.limiter.GetLimits()

	status := protocol.Message{
		Type:    "safety_status",
		RobotID: "robot-01",
		Payload: map[string]any{
			"estop": h.estop.Status(),
			"velocity_limits": map[string]any{
				"max_linear":  maxLin,
				"max_angular": maxAng,
			},
			"adapter_connected": h.adapter.IsConnected(),
		},
	}
	h.hub.Broadcast(status)
}

// =============================================================================
// sendToClient — 特定のクライアントにメッセージ送信
// =============================================================================
func (h *Handler) sendToClient(clientID string, msg protocol.Message) {
	h.hub.SendTo(clientID, msg)
}
