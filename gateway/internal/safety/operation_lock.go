// =============================================================================
// Step 5: 操作排他ロック — 同時操作の制御
// =============================================================================
//
// 【排他制御（Mutual Exclusion）とは？】
// 同時に1つの操作しか実行できないようにする仕組み。
//
// 実世界の例:
//   - トイレの鍵: 中に入ったらロック → 他の人は待つ
//   - ATM: 1人が操作中は他の人は使えない
//
// ロボット制御での用途:
//   - 複数の WebSocket クライアントが同時にロボットを操作する危険防止
//   - ナビゲーション中に速度コマンドで割り込まれるのを防止
//   - E-Stop 発動中は他の操作をブロック
//
// 【sync.Mutex vs sync.RWMutex vs channel】
// Mutex:    最もシンプルな排他ロック。Lock/Unlock のみ。
// RWMutex:  読み書き分離。複数読み取り可、書き込みは排他。
// channel:  Go らしい並行制御。`struct{}` を送受信して同期。
//
// ここでは操作の「所有者（owner）」を管理するため、
// Mutex + 状態フィールドの組み合わせを使う。
//
// =============================================================================
package safety

import (
	"fmt"
	"log"
	"sync"
	"time"
)

// =============================================================================
// OperationLock — 操作の排他制御
// =============================================================================
type OperationLock struct {
	locked    bool
	owner     string    // ロックの所有者（クライアントID）
	operation string    // 現在の操作種別（"manual", "navigation" 等）
	lockedAt  time.Time // ロック取得時刻
	mu        sync.RWMutex
}

// NewOperationLock — コンストラクタ
func NewOperationLock() *OperationLock {
	return &OperationLock{
		locked: false,
	}
}

// =============================================================================
// TryLock — ロックの取得を試みる（ノンブロッキング）
// =============================================================================
//
// 【TryLock パターン】
// 通常の Lock() はロック取得まで待つ（ブロッキング）。
// TryLock() は取得できなかったら即座に false を返す（ノンブロッキング）。
//
// ロボット制御では「待つ」よりも「拒否する」方が安全:
//   - A がロボットを操作中 → B のコマンドは拒否（待たせると古いコマンドが溜まる）
//
// 【戻り値: (bool, error)】
// bool:  ロック取得に成功したか
// error: エラー情報（誰が何の操作でロック中か）
func (ol *OperationLock) TryLock(owner, operation string) (bool, error) {
	ol.mu.Lock()
	defer ol.mu.Unlock()

	if ol.locked {
		if ol.owner == owner {
			// 同じ所有者なら操作を更新（再入可能）
			ol.operation = operation
			return true, nil
		}
		return false, fmt.Errorf(
			"操作がロックされています: 所有者=%s, 操作=%s, 経過時間=%v",
			ol.owner, ol.operation, time.Since(ol.lockedAt).Round(time.Millisecond),
		)
	}

	ol.locked = true
	ol.owner = owner
	ol.operation = operation
	ol.lockedAt = time.Now()

	log.Printf("🔒 操作ロック取得: owner=%s, op=%s", owner, operation)
	return true, nil
}

// =============================================================================
// Unlock — ロックを解放
// =============================================================================
//
// 【所有者チェック】
// ロックを解放できるのは、ロックの所有者だけ。
// 他人がロックを解放するのは危険（意図しない操作再開の可能性）。
// ただし forceUnlock は管理者権限で強制解放を許可。
func (ol *OperationLock) Unlock(owner string) error {
	ol.mu.Lock()
	defer ol.mu.Unlock()

	if !ol.locked {
		return nil // 既に解放済み
	}

	if ol.owner != owner {
		return fmt.Errorf(
			"ロック解放権限がありません: 所有者=%s, 要求者=%s",
			ol.owner, owner,
		)
	}

	duration := time.Since(ol.lockedAt)
	log.Printf("🔓 操作ロック解放: owner=%s, 保持時間=%v", owner, duration.Round(time.Millisecond))

	ol.locked = false
	ol.owner = ""
	ol.operation = ""
	return nil
}

// =============================================================================
// ForceUnlock — 強制ロック解放（E-Stop 等の緊急時用）
// =============================================================================
func (ol *OperationLock) ForceUnlock(reason string) {
	ol.mu.Lock()
	defer ol.mu.Unlock()

	if ol.locked {
		log.Printf("🔓⚡ 強制ロック解放: owner=%s, op=%s, 理由=%s",
			ol.owner, ol.operation, reason)
	}

	ol.locked = false
	ol.owner = ""
	ol.operation = ""
}

// =============================================================================
// Status — ロックの現在状態を返す
// =============================================================================
func (ol *OperationLock) Status() LockStatus {
	ol.mu.RLock()
	defer ol.mu.RUnlock()
	return LockStatus{
		Locked:    ol.locked,
		Owner:     ol.owner,
		Operation: ol.operation,
		LockedAt:  ol.lockedAt,
	}
}

// IsLocked — ロック中かどうか
func (ol *OperationLock) IsLocked() bool {
	ol.mu.RLock()
	defer ol.mu.RUnlock()
	return ol.locked
}

// LockStatus — ロック状態の値オブジェクト
type LockStatus struct {
	Locked    bool      `json:"locked"`
	Owner     string    `json:"owner,omitempty"`
	Operation string    `json:"operation,omitempty"`
	LockedAt  time.Time `json:"locked_at,omitempty"`
}
