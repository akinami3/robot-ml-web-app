// =============================================================================
// Step 5: タイムアウトウォッチドッグ — 通信断の検知と自動停止
// =============================================================================
//
// 【ウォッチドッグ（Watchdog）とは？】
// 定期的な「生存確認」を行い、応答がなければ異常と判断する仕組み。
//
// 実世界の例:
//   - 番犬（watchdog）が侵入者を発見して吠える
//   - マイコンのウォッチドッグタイマー: 一定時間プログラムが動かなければリセット
//
// このプロジェクトでの用途:
//   - 最後のコマンド受信からの経過時間を監視
//   - タイムアウト → E-Stop 発動（ロボットが制御不能になるのを防ぐ）
//
// 【なぜウォッチドッグが必要？】
// WebSocket 接続が突然切れた場合、最後に送った速度コマンドで
// ロボットが動き続ける可能性がある（デッドマン問題）。
// ウォッチドッグが「コマンドが来ない = 異常」と判断して停止命令を出す。
//
// 【Goroutine と Context によるライフサイクル管理】
// ウォッチドッグは別 goroutine で動く長時間タスク。
// context.WithCancel で作った ctx をキャンセルすると、goroutine が終了する。
//
//   ctx, cancel := context.WithCancel(parentCtx)
//   go watchdog.Start(ctx)
//   ...
//   cancel()  // ← これで goroutine が停止する
//
// =============================================================================
package safety

import (
	"context"
	"log"
	"sync"
	"time"
)

// =============================================================================
// TimeoutWatchdog — コマンドタイムアウトの監視
// =============================================================================
type TimeoutWatchdog struct {
	timeout      time.Duration // タイムアウト時間
	lastActivity time.Time     // 最後にコマンドを受信した時刻
	mu           sync.RWMutex
	estop        *EStopManager
	onTimeout    func() // タイムアウト時に呼ばれるコールバック
}

// =============================================================================
// NewTimeoutWatchdog — コンストラクタ
// =============================================================================
//
// 【time.Duration とは？】
// Go の時間の長さを表す型。int64 のナノ秒値。
// 以下のように使う:
//   3 * time.Second     → 3秒
//   500 * time.Millisecond → 500ms
//   time.Minute         → 1分
func NewTimeoutWatchdog(timeout time.Duration, estop *EStopManager) *TimeoutWatchdog {
	return &TimeoutWatchdog{
		timeout:      timeout,
		lastActivity: time.Now(),
		estop:        estop,
	}
}

// =============================================================================
// Start — ウォッチドッグの監視を開始（別 goroutine で実行）
// =============================================================================
//
// 【time.NewTicker とは？】
// 指定間隔で繰り返しイベントを発生させるタイマー。
// 例: time.NewTicker(1 * time.Second) → 毎秒 ticker.C チャネルにイベント発生。
//
// 【select で複数チャネルを待機】
// select 文で ticker と ctx.Done() を同時に待機する。
// - ticker → タイムアウトチェック
// - ctx.Done() → 停止シグナル（graceful shutdown）
//
// 【defer ticker.Stop()】
// Ticker は使い終わったら Stop() する。しないとリソースリーク。
// defer で関数終了時に確実にクリーンアップする。
func (w *TimeoutWatchdog) Start(ctx context.Context) {
	// タイムアウトの半分の間隔でチェック（Nyquist 的発想）
	checkInterval := w.timeout / 2
	if checkInterval < 100*time.Millisecond {
		checkInterval = 100 * time.Millisecond
	}

	ticker := time.NewTicker(checkInterval)
	defer ticker.Stop()

	log.Printf("🐕 ウォッチドッグ開始: タイムアウト=%v, チェック間隔=%v",
		w.timeout, checkInterval)

	for {
		select {
		case <-ctx.Done():
			// コンテキストがキャンセルされた → 停止
			log.Println("🐕 ウォッチドッグ停止（コンテキストキャンセル）")
			return

		case <-ticker.C:
			w.check()
		}
	}
}

// =============================================================================
// Ping — アクティビティを記録（「生きている」信号）
// =============================================================================
//
// 【呼び出しタイミング】
// クライアントからコマンドを受信するたびに Ping() を呼ぶ。
// これにより lastActivity が更新され、タイムアウトがリセットされる。
func (w *TimeoutWatchdog) Ping() {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.lastActivity = time.Now()
}

// =============================================================================
// OnTimeout — タイムアウト時のコールバックを設定
// =============================================================================
func (w *TimeoutWatchdog) OnTimeout(callback func()) {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.onTimeout = callback
}

// =============================================================================
// check — タイムアウトの確認（内部メソッド）
// =============================================================================
//
// 【time.Since の使い方】
// time.Since(t) は「t から現在までの経過時間」を返す。
// time.Now().Sub(t) と等価だが、読みやすい。
func (w *TimeoutWatchdog) check() {
	w.mu.RLock()
	elapsed := time.Since(w.lastActivity)
	timeout := w.timeout
	callback := w.onTimeout
	w.mu.RUnlock()

	if elapsed > timeout {
		log.Printf("🐕 ⚠️ タイムアウト検出！ 最終アクティビティから %v 経過（制限: %v）",
			elapsed.Round(time.Millisecond), timeout)

		// E-Stop を発動
		if w.estop != nil {
			w.estop.Activate("通信タイムアウト")
		}

		// コールバック実行
		if callback != nil {
			callback()
		}

		// タイムアウト後、lastActivity をリセットして連続発動を防止
		w.mu.Lock()
		w.lastActivity = time.Now()
		w.mu.Unlock()
	}
}

// GetLastActivity — 最終アクティビティ時刻を返す
func (w *TimeoutWatchdog) GetLastActivity() time.Time {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return w.lastActivity
}
