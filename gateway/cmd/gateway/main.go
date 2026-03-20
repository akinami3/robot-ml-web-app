// =============================================================================
// Step 3: cmd/gateway/main.go — エントリーポイント
// =============================================================================
//
// 【このファイルの概要】
// Go プロジェクトの慣例的なディレクトリ構造:
//
//   cmd/gateway/main.go   ← エントリーポイント（配線だけ）
//   internal/adapter/     ← ロボットアダプター（ビジネスロジック）
//   internal/server/      ← WebSocket サーバー（通信層）
//   internal/protocol/    ← メッセージ定義（データ層）
//
// 【cmd/ の役割】
// main パッケージを置く場所。
// ここでは「配線（wiring）」のみを行い、ロジックは internal/ に任せる。
//
// 【internal/ の役割】
// Go の特別なディレクトリ名。
// internal/ 配下のパッケージは、同じモジュール内からしかインポートできない。
// 外部のプロジェクトが勝手に使うことを防ぐ。
//
// 【Step 2 の main.go との違い】
// Step 2: main.go に WebSocket 処理がすべて入っていた（約300行）
// Step 3: main.go は約60行。配線だけ。処理は各パッケージに分散。
//
// =============================================================================
package main

import (
	"context"
	"log"

	// 各パッケージをインポート
	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/adapter/mock"
	"github.com/robot-ai-webapp/gateway/internal/server"
)

// =============================================================================
// main — プログラムのエントリーポイント
// =============================================================================
//
// 【処理の流れ】
// 1. アダプターレジストリを作成
// 2. MockAdapter ファクトリを登録
// 3. MockAdapter インスタンスを生成
// 4. MockAdapter をロボットに「接続」
// 5. WebSocket サーバーを起動
//
// 【依存性の流れ（上から下へ）】
// main.go → server.Server → adapter.RobotAdapter (= mock.MockAdapter)
//
// main.go は「全体の組み立て役」。
// 各パーツ（adapter, server）は互いを直接知らない。
// main.go がそれらを繋ぎ合わせる。
func main() {
	// --- 1. レジストリを作成 ---
	// レジストリはアダプターのファクトリ関数を管理する。
	// 将来複数のアダプター（mock, ros, gazebo 等）を切り替え可能にする。
	registry := adapter.NewRegistry()

	// --- 2. MockAdapter のファクトリを登録 ---
	// "mock" という名前で MockAdapter のファクトリ関数を登録。
	// ファクトリ関数: 呼ぶたびに新しいアダプターを作って返す関数。
	registry.RegisterFactory("mock", mock.Factory)

	log.Println("📋 登録済みアダプター:", registry.ListFactories())

	// --- 3. MockAdapter インスタンスを生成 ---
	// registry.CreateAdapter("mock") は:
	//   1. "mock" に対応するファクトリ関数（mock.Factory）を見つける
	//   2. mock.Factory() を呼んで MockAdapter を生成
	//   3. active マップに登録
	//   4. adapter.RobotAdapter インターフェースとして返す
	robotAdapter, err := registry.CreateAdapter("robot-01", "mock")
	if err != nil {
		log.Fatalf("❌ アダプター作成失敗: %v", err)
	}

	// --- 4. モックロボットに接続 ---
	// Connect を呼ぶと、MockAdapter 内部でセンサーデータ生成が開始される。
	// config は nil（MockAdapter は設定不要）
	if err := robotAdapter.Connect(context.Background(), nil); err != nil {
		log.Fatalf("❌ ロボット接続失敗: %v", err)
	}

	// --- 5. WebSocket サーバーを作成して起動 ---
	// robotAdapter を注入（Dependency Injection）
	srv := server.NewServer(robotAdapter, ":8080")

	// サーバー起動（ブロッキング）
	// ListenAndServe が返るのはエラー時のみ
	if err := srv.Start(context.Background()); err != nil {
		log.Fatalf("❌ サーバーエラー: %v", err)
	}
}
