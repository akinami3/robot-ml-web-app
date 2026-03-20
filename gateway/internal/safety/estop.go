// =============================================================================
// Step 5: 緊急停止（E-Stop）マネージャー
// =============================================================================
//
// 【E-Stop（Emergency Stop）とは？】
// ロボットの安全において最も重要な機能。
// ハードウェアの E-Stop ボタンは ISO 13850 で規格化されている。
// ソフトウェア E-Stop はその補助的な実装。
//
// 【設計原則: フェイルセーフ（Fail-Safe）】
// 「故障したら安全な側に倒れる」設計思想。
// E-Stop の場合:
//   - 通信が途切れた → E-Stop 状態にする（動き続けるのは危険）
//   - 状態が不明 → E-Stop 状態にする（不明 = 危険として扱う）
//   - E-Stop 解除は明示的な操作が必要（勝手に復帰しない）
//
// 【sync.RWMutex とは？】
// 読み書きロック。複数の goroutine から安全にアクセスするための仕組み。
//
//   RLock / RUnlock — 読み取りロック（複数同時OK）
//   Lock / Unlock   — 書き込みロック（1つだけ、排他）
//
// 以下の場面で使い分ける:
//   - 状態の参照（IsActive） → RLock で十分
//   - 状態の変更（Activate） → Lock が必要
//
// =============================================================================
package safety

import (
	"log"
	"sync"
	"time"
)

// =============================================================================
// EStopManager — 緊急停止の状態と履歴を管理
// =============================================================================
//
// 【構造体の設計】
// active:     現在 E-Stop がアクティブかどうか
// activatedAt: いつ E-Stop が発動したか（ログ・UI表示に使用）
// mu:         並行アクセスを保護するロック
// listeners:  E-Stop 状態変化を通知するコールバック
//
// 【コールバックパターン】
// E-Stop が発動/解除されたとき、他のコンポーネントに通知する。
// 例: VelocityLimiter は E-Stop 中は速度を 0 に制限する。
type EStopManager struct {
	active      bool
	activatedAt time.Time
	mu          sync.RWMutex
	listeners   []func(active bool)
}

// NewEStopManager — コンストラクタ
func NewEStopManager() *EStopManager {
	return &EStopManager{
		active:    false,
		listeners: make([]func(active bool), 0),
	}
}

// =============================================================================
// Activate — 緊急停止を発動
// =============================================================================
//
// 【べき等性（Idempotency）】
// 何回呼んでも結果が同じ。
// E-Stop が既にアクティブなら何もしない（二重発動を防止）。
func (e *EStopManager) Activate(reason string) {
	e.mu.Lock()
	defer e.mu.Unlock()

	if e.active {
		log.Printf("🛑 E-Stop: 既にアクティブです（理由: %s）", reason)
		return
	}

	e.active = true
	e.activatedAt = time.Now()

	log.Printf("🛑🛑🛑 E-Stop 発動！ 理由: %s", reason)

	// リスナーに通知
	for _, listener := range e.listeners {
		listener(true)
	}
}

// =============================================================================
// Deactivate — 緊急停止を解除
// =============================================================================
//
// 【解除は慎重に】
// E-Stop の解除は「明示的な操作」でのみ行う。
// 自動復帰は危険（ロボットが突然動き出す可能性）。
func (e *EStopManager) Deactivate(reason string) {
	e.mu.Lock()
	defer e.mu.Unlock()

	if !e.active {
		return
	}

	duration := time.Since(e.activatedAt)
	e.active = false

	log.Printf("✅ E-Stop 解除。持続時間: %v、理由: %s", duration, reason)

	// リスナーに通知
	for _, listener := range e.listeners {
		listener(false)
	}
}

// =============================================================================
// IsActive — E-Stop がアクティブかどうかを確認
// =============================================================================
//
// 【RLock を使う理由】
// 読み取りだけなので RLock（読み取りロック）で十分。
// RLock は複数の goroutine から同時に取得できるため、
// 書き込みロック（Lock）よりパフォーマンスが良い。
func (e *EStopManager) IsActive() bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.active
}

// Status — E-Stop の現在状態を返す
func (e *EStopManager) Status() EStopStatus {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return EStopStatus{
		Active:      e.active,
		ActivatedAt: e.activatedAt,
	}
}

// =============================================================================
// OnStateChange — E-Stop 状態変化のリスナーを登録
// =============================================================================
//
// 【Observer パターン】
// E-Stop の状態が変わったときに通知を受ける関数を登録する。
// ライトな Pub/Sub のような仕組み。
//
// 使用例:
//   estop.OnStateChange(func(active bool) {
//       if active {
//           limiter.SetMaxVelocity(0) // 速度を0に
//       }
//   })
func (e *EStopManager) OnStateChange(listener func(active bool)) {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.listeners = append(e.listeners, listener)
}

// =============================================================================
// EStopStatus — E-Stop の状態を表す値オブジェクト
// =============================================================================
type EStopStatus struct {
	Active      bool      `json:"active"`
	ActivatedAt time.Time `json:"activated_at,omitempty"`
}
