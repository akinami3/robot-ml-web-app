// =============================================================================
// Step 5: 速度リミッター — コマンドの安全検証
// =============================================================================
//
// 【速度制限の必要性】
// ロボットに送信する速度コマンドを無制限にすると危険。
// - バグで huge な値が送られる可能性
// - ユーザーが意図しない高速コマンドを送る可能性
// - E-Stop 中にコマンドが通過してはいけない
//
// 【クランプ（Clamp）関数】
// 値を指定した範囲内に制限する数学関数。
//   clamp(value, min, max) → min ≤ result ≤ max
//
//   例: clamp(5.0, -1.0, 1.0) → 1.0
//       clamp(-0.3, -1.0, 1.0) → -0.3
//
// 【パイプラインパターン】
// 速度コマンドが最終的にロボットに到達するまでの多段チェック:
//
//   ユーザー入力 → VelocityLimiter → EStop チェック → Adapter
//
// 各段階で「安全でないものを弾き、安全なものだけ通す」。
// これを「安全パイプライン」と呼ぶ。
//
// =============================================================================
package safety

import (
	"fmt"
	"log"
	"math"
	"sync"
)

// =============================================================================
// VelocityLimiter — 速度制限マネージャー
// =============================================================================
type VelocityLimiter struct {
	maxLinear  float64 // 直進速度の上限 (m/s)
	maxAngular float64 // 回転速度の上限 (rad/s)
	mu         sync.RWMutex
	estop      *EStopManager // E-Stop の参照
}

// Velocity — 速度の値オブジェクト
type Velocity struct {
	LinearX  float64
	LinearY  float64
	AngularZ float64
}

// =============================================================================
// NewVelocityLimiter — コンストラクタ
// =============================================================================
//
// 【依存性注入】
// estop *EStopManager を受け取ることで、E-Stop 状態を参照できる。
// VelocityLimiter は EStopManager に依存するが、逆は依存しない。
// → 依存の方向が一方通行（これが良い設計）
func NewVelocityLimiter(maxLinear, maxAngular float64, estop *EStopManager) *VelocityLimiter {
	return &VelocityLimiter{
		maxLinear:  maxLinear,
		maxAngular: maxAngular,
		estop:      estop,
	}
}

// =============================================================================
// Limit — 速度コマンドを安全な範囲に制限
// =============================================================================
//
// 【ガード節パターン（Guard Clause）】
// 関数の先頭で「異常ケース」をチェックし、即座に返す。
// 正常ケースだけがメインロジックに到達する。
//
//   func Limit(v) (result, error) {
//       if E-Stop → return error      ← ガード1
//       if NaN   → return error       ← ガード2
//       clamped := clamp(v)            ← メインロジック
//       return clamped, nil
//   }
//
// 【多値戻り値（Multiple Return Values）】
// Go の関数は複数の値を返せる。(Velocity, error) のパターンは Go の慣例。
// error が nil なら成功、non-nil ならエラー。
func (vl *VelocityLimiter) Limit(v Velocity) (Velocity, error) {
	// --- ガード1: E-Stop チェック ---
	if vl.estop != nil && vl.estop.IsActive() {
		return Velocity{}, fmt.Errorf("E-Stop がアクティブです: すべての移動コマンドは拒否されます")
	}

	// --- ガード2: NaN / Inf チェック ---
	// 不正な浮動小数点値（NaN, ±Inf）を検出して拒否する。
	// NaN は比較が常に false になるため、気づかないとバグの原因になる。
	if math.IsNaN(v.LinearX) || math.IsNaN(v.LinearY) || math.IsNaN(v.AngularZ) ||
		math.IsInf(v.LinearX, 0) || math.IsInf(v.LinearY, 0) || math.IsInf(v.AngularZ, 0) {
		return Velocity{}, fmt.Errorf("不正な速度値が検出されました (NaN/Inf)")
	}

	// --- メインロジック: クランプ ---
	vl.mu.RLock()
	maxLin := vl.maxLinear
	maxAng := vl.maxAngular
	vl.mu.RUnlock()

	clamped := Velocity{
		LinearX:  clamp(v.LinearX, -maxLin, maxLin),
		LinearY:  clamp(v.LinearY, -maxLin, maxLin),
		AngularZ: clamp(v.AngularZ, -maxAng, maxAng),
	}

	// 制限された場合はログに記録
	if clamped != v {
		log.Printf("⚠️ 速度を制限しました: (%.2f, %.2f, %.2f) → (%.2f, %.2f, %.2f)",
			v.LinearX, v.LinearY, v.AngularZ,
			clamped.LinearX, clamped.LinearY, clamped.AngularZ)
	}

	return clamped, nil
}

// =============================================================================
// SetLimits — 速度上限を動的に変更
// =============================================================================
//
// 【動的変更の用途】
// - ロボットの状態に応じて速度を下げる（バッテリー残量低下時）
// - 狭い場所での低速モード
// - 管理者がリモートで速度制限を変更
func (vl *VelocityLimiter) SetLimits(maxLinear, maxAngular float64) {
	vl.mu.Lock()
	defer vl.mu.Unlock()
	vl.maxLinear = maxLinear
	vl.maxAngular = maxAngular
	log.Printf("📐 速度制限を変更: linear=%.2f m/s, angular=%.2f rad/s", maxLinear, maxAngular)
}

// GetLimits — 現在の速度上限を取得
func (vl *VelocityLimiter) GetLimits() (maxLinear, maxAngular float64) {
	vl.mu.RLock()
	defer vl.mu.RUnlock()
	return vl.maxLinear, vl.maxAngular
}

// =============================================================================
// clamp — 値を範囲内に制限するヘルパー関数
// =============================================================================
//
// 【math.Min / math.Max を使った実装】
// Go 1.21 から min/max ビルトインが追加されたが、
// ここでは明示的に math パッケージを使って教育的に示す。
func clamp(value, minVal, maxVal float64) float64 {
	return math.Max(minVal, math.Min(value, maxVal))
}
