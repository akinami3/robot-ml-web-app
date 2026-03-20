// =============================================================================
// Step 3: Adapter パターン — アダプターレジストリ
// =============================================================================
//
// 【このファイルの概要】
// アダプターの「登録簿（Registry）」。2つの機能を持つ:
//
// 1. ファクトリ登録: アダプターを「作る方法」を名前で管理
//    "mock" → MockAdapter を作る関数
//    "ros2" → ROS2Adapter を作る関数（将来追加）
//
// 2. インスタンス管理: 現在動作中のアダプターを管理
//    "robot-01" → MockAdapter（接続中）
//    "robot-02" → ROS2Adapter（接続中）
//
// 【ファクトリパターン（Factory Pattern）とは？】
// オブジェクトの生成を専用の関数に任せるデザインパターン。
//
//   直接生成:    adapter := &MockAdapter{...}   ← 具体的な型を知る必要あり
//   ファクトリ:  adapter := factory()            ← 型を知らなくてもOK
//
// 【レジストリパターンとの組み合わせ】
// ファクトリ + レジストリ = 「文字列からオブジェクトを動的生成」
//
//   ユーザーが "mock" を選択
//   → registry.CreateAdapter("robot-01", "mock")
//   → registry が "mock" のファクトリを見つける
//   → ファクトリが MockAdapter を作成
//   → "robot-01" と紐づけて保存
//
// =============================================================================
package adapter

import (
	"fmt"
	"log"
	"sync"
)

// =============================================================================
// AdapterFactory — アダプターを生成する関数の型
// =============================================================================
//
// 【関数型とは？】
// Go では関数自体を変数に格納したり、引数として渡したりできる。
// type AdapterFactory func() RobotAdapter は、
// 「引数なしで RobotAdapter を返す関数」の型定義。
//
// 【使用例】
//   var factory AdapterFactory = func() RobotAdapter {
//       return NewMockAdapter()
//   }
//   adapter := factory()  // MockAdapter が返る
type AdapterFactory func() RobotAdapter

// =============================================================================
// Registry — アダプターレジストリ構造体
// =============================================================================
//
// 【sync.RWMutex とは？】
// 読み書きロック。複数の goroutine が同時にデータにアクセスする時の安全装置。
//
// - RLock() / RUnlock(): 読み取りロック（複数の goroutine が同時に読める）
// - Lock() / Unlock():   書き込みロック（1つだけがアクセス可能）
//
// 【なぜ RWMutex？（通常の Mutex との違い）】
// Mutex:   読み取りも書き込みも1つずつしかアクセスできない
// RWMutex: 読み取りは複数同時OK、書き込みは1つだけ
//
// GetAdapter() は頻繁に呼ばれる（コマンド送信のたびに）ので、
// 読み取り同士をブロックしない RWMutex のほうが効率的。
type Registry struct {
	mu        sync.RWMutex
	factories map[string]AdapterFactory      // タイプ名 → ファクトリ関数
	active    map[string]RobotAdapter        // ロボットID → アクティブなアダプター
}

// =============================================================================
// NewRegistry — Registry のコンストラクタ
// =============================================================================
//
// 【make(map[...]) が必要な理由】
// Go の map は宣言しただけでは nil。
// nil の map に書き込むと panic（プログラムクラッシュ）する。
// make() で初期化が必須。
func NewRegistry() *Registry {
	return &Registry{
		factories: make(map[string]AdapterFactory),
		active:    make(map[string]RobotAdapter),
	}
}

// =============================================================================
// RegisterFactory — ファクトリ関数を登録
// =============================================================================
//
// 【使用例】（main.go から）
//   registry.RegisterFactory("mock", func() adapter.RobotAdapter {
//       return mock.NewMockAdapter()
//   })
func (r *Registry) RegisterFactory(adapterType string, factory AdapterFactory) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.factories[adapterType] = factory
	log.Printf("📋 アダプターファクトリ登録: %s", adapterType)
}

// =============================================================================
// CreateAdapter — ロボット用のアダプターを作成して登録
// =============================================================================
//
// 【処理の流れ】
// 1. adapterType に対応するファクトリを検索
// 2. ファクトリを呼び出してアダプターを生成
// 3. active map にロボットID と紐づけて保存
// 4. 生成したアダプターを返す
//
// 【エラーハンドリング】
// 未知の adapterType の場合はエラーを返す（パニックしない）。
// Go では「エラーを返り値で伝える」のが基本。
func (r *Registry) CreateAdapter(robotID, adapterType string) (RobotAdapter, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// カンマOKイディオム: map からの取得 + 存在確認
	factory, ok := r.factories[adapterType]
	if !ok {
		return nil, fmt.Errorf("未知のアダプタータイプ: %s", adapterType)
	}

	// ファクトリでアダプターを生成
	a := factory()

	// active map に登録
	r.active[robotID] = a

	log.Printf("✅ アダプター作成: robot_id=%s, type=%s", robotID, adapterType)
	return a, nil
}

// =============================================================================
// GetAdapter — ロボットID からアダプターを取得
// =============================================================================
//
// 【カンマOKパターン】
// Go の map アクセスは2つの戻り値を受け取れる:
//   value, ok := myMap[key]
//   ok = true:  キーが存在する
//   ok = false: キーが存在しない（value はゼロ値）
//
// このパターンで「存在しない場合」を安全にハンドリングできる。
func (r *Registry) GetAdapter(robotID string) (RobotAdapter, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	a, ok := r.active[robotID]
	return a, ok
}

// =============================================================================
// RemoveAdapter — アダプターを登録から削除
// =============================================================================
//
// 【注意】
// この関数は map から削除するだけ。
// Disconnect（切断処理）は呼び出し側の責任。
//
// 【delete() とは？】
// Go の組み込み関数。map からエントリを削除する。
// キーが存在しなくてもエラーにならない（安全）。
func (r *Registry) RemoveAdapter(robotID string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	delete(r.active, robotID)
	log.Printf("🗑️ アダプター削除: robot_id=%s", robotID)
}

// =============================================================================
// GetAllActive — 全アクティブアダプターを取得
// =============================================================================
//
// 【防御的コピー（Defensive Copy）】
// 内部の active map をそのまま返すと、呼び出し側が変更した時に
// Registry の内部状態が壊れる。
// 新しい map を作ってコピーを返すことで、内部状態を保護する。
func (r *Registry) GetAllActive() map[string]RobotAdapter {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string]RobotAdapter, len(r.active))
	for k, v := range r.active {
		result[k] = v
	}
	return result
}

// =============================================================================
// ListFactories — 登録済みアダプタータイプ名のリストを返す
// =============================================================================
func (r *Registry) ListFactories() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	types := make([]string, 0, len(r.factories))
	for k := range r.factories {
		types = append(types, k)
	}
	return types
}
