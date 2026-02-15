// =============================================================================
// ファイル: registry.go
// パッケージ: adapter（アダプターパッケージ）
//
// 【このファイルの概要】
// 「アダプターレジストリ（Adapter Registry）」を実装するファイルです。
// レジストリとは「登録簿」という意味で、以下の2つを管理します：
//
// 1. ファクトリ（Factory）: アダプターを「作る方法」の登録簿
//   - "ros2" → ROS2アダプターを作る関数
//   - "mqtt" → MQTTアダプターを作る関数
//   - "mock" → テスト用モックアダプターを作る関数
//
// 2. アクティブインスタンス: 現在動作中のアダプターの登録簿
//   - "robot_001" → ROS2アダプター（接続中）
//   - "robot_002" → MQTTアダプター（接続中）
//
// 【ファクトリパターン（Factory Pattern）とは？】
// オブジェクトの作成を専用の関数に任せるデザインパターンです。
//
// 通常の作成方法:
//
//	adapter := &ROS2Adapter{...}  // 具体的な型を直接指定
//
// ファクトリパターン:
//
//	adapter := factory(logger)     // 関数経由で作成（型を知らなくてよい）
//
// 利点：
// - 呼び出し側は具体的な型（ROS2Adapter, MQTTAdapterなど）を知る必要がない
// - 新しいアダプタータイプの追加時、既存コードの変更が不要
// - テスト時にモックアダプターに簡単に差し替えられる
//
// 【レジストリパターン（Registry Pattern）との組み合わせ】
// ファクトリパターンとレジストリパターンを組み合わせることで、
// 「名前（文字列）からアダプターを動的に作成する」ことができます。
//
// 例: ユーザーがUIで「ROS2」を選択
//
//	→ "ros2" という文字列がAPIに送られる
//	→ レジストリが "ros2" に対応するファクトリを見つける
//	→ ファクトリがROS2アダプターを作成する
//
// =============================================================================
package adapter

import (
	// fmt: フォーマット済みI/Oパッケージ
	// エラーメッセージの生成に使います。
	// fmt.Errorf() でフォーマット済みのエラーを作ります。
	"fmt"

	// sync: 同期プリミティブパッケージ
	// RWMutexで factories と active の map への
	// 安全な同時アクセスを提供します。
	"sync"

	// zap: 高性能ロガー（Uber社製）
	// アダプターの登録・作成・削除などのイベントをログに記録します。
	"go.uber.org/zap"
)

// =============================================================================
// AdapterFactory - アダプターファクトリ型
// =============================================================================
//
// 【型エイリアス（type alias）とは？】
// type AdapterFactory func(logger *zap.Logger) RobotAdapter は、
// 「関数型」に新しい名前を付けています。
//
// これは「*zap.Logger を引数に取り、RobotAdapter を返す関数」の型です。
//
// 【なぜ関数に型を付けるのか？】
//  1. コードが読みやすくなる
//     func(logger *zap.Logger) RobotAdapter → AdapterFactory
//  2. 関数の「契約」が明確になる
//     「この型の関数を渡してね」と伝えやすい
//
// 【使用例】
//
//	var factory AdapterFactory = func(logger *zap.Logger) RobotAdapter {
//	    return &MockAdapter{logger: logger}
//	}
//	adapter := factory(logger)  // ファクトリを使ってアダプターを作成
type AdapterFactory func(logger *zap.Logger) RobotAdapter

// =============================================================================
// Registry - アダプターレジストリ構造体
// =============================================================================
//
// 【この構造体の役割】
// 1. アダプターファクトリの登録と検索
// 2. アクティブなアダプタインスタンスの管理
//
// 【なぜレジストリが必要？】
// アプリケーションの様々な場所からアダプターにアクセスする必要があります。
// レジストリが中央管理することで：
// - どこからでもアダプターを取得できる
// - ロボットIDからアダプターへの対応が一元管理される
// - 並行アクセスの安全性が保証される
type Registry struct {
	// mu: 読み書きロック
	// factories と active の map を保護します。
	//
	// 【なぜ1つのRWMutexで2つのmapを保護するのか？】
	// 2つのmapは概念的に「レジストリの状態」として1つのまとまりなので、
	// 1つのロックで管理するのがシンプルです。
	// ただし、アクセスパターンが大きく異なる場合は、
	// 2つのロックに分けることもあります（トレードオフ）。
	mu sync.RWMutex

	// factories: アダプタータイプ名からファクトリ関数へのmap
	// キー: アダプタータイプ名（例: "ros2", "mqtt", "mock"）
	// 値: そのタイプのアダプターを作成するファクトリ関数
	factories map[string]AdapterFactory

	// active: ロボットIDからアクティブなアダプターへのmap
	// キー: ロボットID（例: "robot_001"）
	// 値: そのロボットに対応するアダプターインスタンス
	//
	// 【RobotAdapter インターフェース型の変数】
	// 値の型が RobotAdapter（インターフェース型）なのがポイントです。
	// 実際に格納されるのは具体的な型（*ROS2Adapter, *MockAdapterなど）ですが、
	// インターフェース型で保持することで、呼び出し側は具体的な型を知る必要がありません。
	//
	// 【ポリモーフィズム（多態性）】
	// 同じインターフェースで異なる実装を扱えることを「ポリモーフィズム」と言います。
	// active map に ROS2Adapter と MockAdapter を混在させても、
	// どちらも RobotAdapter インターフェースとして同じように操作できます。
	active map[string]RobotAdapter // robot_id -> adapter

	// logger: ログ出力用のロガー
	logger *zap.Logger
}

// =============================================================================
// NewRegistry - Registryのコンストラクタ
// =============================================================================
//
// 【引数】
// - logger: ログ出力用のロガー
//
// 【戻り値】
// - *Registry: 初期化されたRegistryへのポインタ
func NewRegistry(logger *zap.Logger) *Registry {
	return &Registry{
		// make(): mapの初期化
		// mapは宣言しただけでは nil で、nilのmapに書き込むとパニックになります。
		// 必ず make() で初期化してから使います。
		factories: make(map[string]AdapterFactory),
		active:    make(map[string]RobotAdapter),
		logger:    logger,
	}
}

// =============================================================================
// RegisterFactory - アダプターファクトリを登録する
// =============================================================================
//
// 【この関数の用途】
// アプリケーション起動時に、対応するロボットタイプのファクトリを登録します。
//
// 使用例（アプリケーション起動時）：
//
//	registry := adapter.NewRegistry(logger)
//	registry.RegisterFactory("ros2", ros2.NewAdapter)
//	registry.RegisterFactory("mqtt", mqtt.NewAdapter)
//	registry.RegisterFactory("mock", mock.NewAdapter)
//
// 【引数】
// - adapterType: アダプタータイプ名（例: "ros2"）
// - factory: そのタイプのアダプターを作成するファクトリ関数
func (r *Registry) RegisterFactory(adapterType string, factory AdapterFactory) {
	// 書き込みロック（mapへの書き込み）
	r.mu.Lock()
	defer r.mu.Unlock()

	// ファクトリを登録する
	r.factories[adapterType] = factory

	// 登録完了のログを出力する
	r.logger.Info("Registered adapter factory", zap.String("type", adapterType))
}

// =============================================================================
// CreateAdapter - ロボット用のアダプターを作成して登録する
// =============================================================================
//
// 【この関数の動作】
// 1. 指定されたアダプタータイプのファクトリを検索する
// 2. ファクトリを使ってアダプターインスタンスを作成する
// 3. active map にロボットIDと紐づけて保存する
//
// 【引数】
// - robotID: ロボットの識別子（例: "robot_001"）
// - adapterType: アダプタータイプ（例: "ros2", "mqtt"）
//
// 【戻り値】
// - RobotAdapter: 作成されたアダプター（インターフェース型で返す）
// - error: 未知のアダプタータイプの場合のエラー
//
// 【インターフェース型で返す利点】
// 戻り値が RobotAdapter（インターフェース型）なので、
// 呼び出し側は具体的な型を知る必要がありません。
// これが「疎結合（loose coupling）」の実現方法です。
func (r *Registry) CreateAdapter(robotID, adapterType string) (RobotAdapter, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// ファクトリを検索する（カンマOKイディオム）
	factory, ok := r.factories[adapterType]
	if !ok {
		// ファクトリが見つからない場合 → エラーを返す
		// fmt.Errorf(): フォーマット文字列からエラーを作成する
		// %s: 文字列のプレースホルダー
		return nil, fmt.Errorf("unknown adapter type: %s", adapterType)
	}

	// ファクトリを使ってアダプターを作成する
	//
	// 【logger.With() とは？】
	// ロガーに固定のフィールドを追加した「子ロガー」を作成します。
	// この子ロガーで出力されるすべてのログには、
	// 自動的に robot_id と adapter のフィールドが追加されます。
	//
	// 例: adapter.logger.Info("Connected")
	// → {"msg": "Connected", "robot_id": "robot_001", "adapter": "ros2"}
	//
	// これにより、大量のログの中から特定のロボットのログを
	// 簡単にフィルタリングできます。
	adapter := factory(r.logger.With(zap.String("robot_id", robotID), zap.String("adapter", adapterType)))

	// active map にアダプターを登録する
	r.active[robotID] = adapter

	r.logger.Info("Created adapter",
		zap.String("robot_id", robotID),
		zap.String("type", adapterType),
	)

	return adapter, nil
}

// =============================================================================
// GetAdapter - ロボットIDに対応するアダプターを取得する
// =============================================================================
//
// 【この関数の用途】
// ロボットにコマンドを送りたい時、ロボットIDから対応するアダプターを取得します。
//
// 使用例：
//
//	if adapter, ok := registry.GetAdapter("robot_001"); ok {
//	    adapter.SendCommand(ctx, cmd)
//	}
//
// 【カンマOKパターン】
// (RobotAdapter, bool) を返すことで、呼び出し側は
// アダプターが存在するかどうかを安全に確認できます。
//
// 【読み取りロック（RLock）を使う理由】
// アダプターの取得は非常に頻繁に行われます（コマンド送信のたびに）。
// RLockを使うことで、複数のゴルーチンが同時にGetAdapterを呼べます。
func (r *Registry) GetAdapter(robotID string) (RobotAdapter, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// mapからの値取得
	// 変数名を adapter にすると、パッケージ名の adapter と衝突するので注意。
	// ここでは go の変数スコープにより、ローカル変数が優先されます。
	adapter, ok := r.active[robotID]
	return adapter, ok
}

// =============================================================================
// RemoveAdapter - アダプターを削除する
// =============================================================================
//
// 【この関数の用途】
// ロボットが切断された時や、アダプターが不要になった時に呼び出します。
// active map からアダプターを削除します。
//
// 【注意】
// この関数はアダプターをmapから削除するだけで、
// Disconnect（切断処理）は行いません。
// 切断は呼び出し側の責任です。
func (r *Registry) RemoveAdapter(robotID string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// mapからアダプターを削除する
	// delete(map, key): Goの組み込み関数でmapから要素を削除する
	// キーが存在しなくてもエラーにはなりません（安全）。
	delete(r.active, robotID)

	r.logger.Info("Removed adapter", zap.String("robot_id", robotID))
}

// =============================================================================
// GetAllActive - すべてのアクティブなアダプターを取得する
// =============================================================================
//
// 【この関数の用途】
// 全ロボットを一斉に緊急停止する場合など、
// すべてのアクティブなアダプターが必要な場面で使います。
//
// 【戻り値】
// - map[string]RobotAdapter: ロボットIDからアダプターへのmap（コピー）
//
// 【mapのコピーを返す理由（非常に重要！）】
// 内部の active map をそのまま返すと、呼び出し側がmapを変更した時に
// レジストリの内部状態が壊れてしまいます。
// そのため、新しいmapを作ってコピーを返しています。
//
// これは「防御的コピー（defensive copy）」と呼ばれるテクニックです。
//
// また、ロックの外でmapを安全にイテレーションするためにも
// コピーが必要です。元のmapはロック保護下にあるため、
// ロックの外で直接イテレーションするとdata raceになります。
func (r *Registry) GetAllActive() map[string]RobotAdapter {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// 新しいmapを作成する
	// make(map[string]RobotAdapter, len(r.active))
	// 第2引数は「初期容量（capacity）」のヒントです。
	// 事前にサイズがわかっている場合、初期容量を指定すると
	// メモリの再割り当てが減り、パフォーマンスが向上します。
	result := make(map[string]RobotAdapter, len(r.active))

	// すべてのエントリをコピーする
	for k, v := range r.active {
		result[k] = v
	}
	return result
}

// =============================================================================
// ListFactories - 登録されているアダプタータイプ名のリストを返す
// =============================================================================
//
// 【この関数の用途】
// UIでロボット追加画面を表示する時、
// 「利用可能なアダプタータイプ」のドロップダウンリストを作るために使います。
//
// 例: ["ros2", "mqtt", "grpc", "mock"] が返される
//
// 【戻り値】
// - []string: アダプタータイプ名のスライス
func (r *Registry) ListFactories() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// スライスを事前確保する
	// make([]string, 0, len(r.factories))
	//
	// 【make でスライスを作る時の引数】
	// make([]型, 長さ, 容量)
	// - 長さ（length）= 0: 現在の要素数は0
	// - 容量（capacity）= len(r.factories): 事前に確保するメモリ量
	//
	// 【なぜ容量を指定するのか？】
	// append() でスライスに要素を追加する時、容量が足りないと
	// 新しいメモリを確保してデータをコピーする処理が発生します。
	// 事前に容量を指定することで、この再割り当てを避けられます。
	// 要素数がわかっている場合のベストプラクティスです。
	types := make([]string, 0, len(r.factories))

	// mapのキー（アダプタータイプ名）をスライスに追加する
	for k := range r.factories {
		types = append(types, k)
	}
	return types
}
