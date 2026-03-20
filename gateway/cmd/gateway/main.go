// =============================================================================
// Step 11: cmd/gateway/main.go — Redis Streams 統合版
// =============================================================================
//
// 【Step 10 からの変更点（Step 11）】
// 1. Redis パブリッシャーの初期化と配線
// 2. サーバーへの Redis パブリッシャーの注入
// 3. センサーデータが WebSocket + Redis 両方に配信される
//
// 【配線（Wiring）の全体像】
//
//	main.go が各コンポーネントを作成し、依存関係を接続する。
//
//	            ┌─ EStopManager
//	            │
//	Registry ─ MockAdapter ─┐
//	                         │
//	Hub ──────────────────── Server
//	                         │
//	            ├─ VelocityLimiter ─── EStopManager（参照）
//	            ├─ TimeoutWatchdog ─── EStopManager（参照）
//	            ├─ OperationLock
//	            └─ RedisPublisher ★Step 11 新規
//
// =============================================================================
package main

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/adapter/mock"
	"github.com/robot-ai-webapp/gateway/internal/bridge"
	"github.com/robot-ai-webapp/gateway/internal/safety"
	"github.com/robot-ai-webapp/gateway/internal/server"
)

func main() {
	// =================================================================
	// 1. アダプターの準備（Step 3 と同じ）
	// =================================================================
	registry := adapter.NewRegistry()
	registry.RegisterFactory("mock", mock.Factory)
	log.Println("📋 登録済みアダプター:", registry.ListFactories())

	robotAdapter, err := registry.CreateAdapter("robot-01", "mock")
	if err != nil {
		log.Fatalf("❌ アダプター作成失敗: %v", err)
	}

	if err := robotAdapter.Connect(context.Background(), nil); err != nil {
		log.Fatalf("❌ ロボット接続失敗: %v", err)
	}

	// =================================================================
	// 2. 安全コンポーネントの初期化（Step 5 で新規追加）
	// =================================================================
	//
	// 【初期化の順序が重要】
	// EStopManager を最初に作る。
	// VelocityLimiter と TimeoutWatchdog が EStopManager を参照するため。
	// 依存関係の順に初期化する。

	// --- 2a. E-Stop マネージャー ---
	estop := safety.NewEStopManager()

	// --- 2b. 速度リミッター ---
	// maxLinear: 1.0 m/s, maxAngular: 1.0 rad/s
	// MockAdapter の能力に合わせた値。
	limiter := safety.NewVelocityLimiter(1.0, 1.0, estop)

	// --- 2c. タイムアウトウォッチドッグ ---
	// 30秒間コマンドが来なければタイムアウト
	// 開発中は長めに設定（本番では 5-10 秒が適切）
	watchdog := safety.NewTimeoutWatchdog(30*time.Second, estop)

	// --- 2d. 操作排他ロック ---
	opLock := safety.NewOperationLock()

	// --- 2e. E-Stop リスナーの設定 ---
	// E-Stop が発動されたら、操作ロックを強制解放する
	estop.OnStateChange(func(active bool) {
		if active {
			opLock.ForceUnlock("E-Stop 発動による強制解放")
			log.Println("🛑 E-Stop 発動: 操作ロックを強制解放しました")
		}
	})

	log.Println("🛡️ 安全コンポーネント初期化完了")
	log.Printf("   速度制限: linear=1.0 m/s, angular=1.0 rad/s")
	log.Printf("   ウォッチドッグ: タイムアウト=30s")

	// =================================================================
	// 3. Hub の作成（Step 5 で新規追加）
	// =================================================================
	hub := server.NewHub()

	// =================================================================
	// 4. Redis パブリッシャーの初期化（Step 11 で新規追加）
	// =================================================================
	//
	// 【環境変数から Redis URL を取得】
	// 環境変数 REDIS_URL が設定されていれば Redis に接続する。
	// 設定されていなければ、Redis なしで動作する（Graceful Degradation）。
	//
	// 【Graceful Degradation（優雅な劣化）とは？】
	// 一部の機能が利用できなくても、アプリ全体は動作し続ける設計パターン。
	// Redis がなくても WebSocket 通信は動く。データ記録だけが無効になる。
	var publisher *bridge.RedisPublisher
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://localhost:6379/0" // デフォルト URL
	}

	pub, err := bridge.NewRedisPublisher(redisURL)
	if err != nil {
		// Redis 接続失敗してもサーバーは起動する（Graceful Degradation）
		log.Printf("⚠️ Redis 接続失敗（データ記録無効）: %v", err)
		publisher = nil
	} else {
		publisher = pub
		defer publisher.Close()
		log.Println("📊 Redis パブリッシャー初期化完了（データ記録有効）")
	}

	// =================================================================
	// 5. サーバーの起動
	// =================================================================
	//
	// 【依存性注入の数が増えた】
	// Step 4: NewServer(adapter, port)
	// Step 5: NewServer(adapter, hub, estop, limiter, watchdog, opLock, port)
	// Step 11: NewServer(adapter, hub, estop, limiter, watchdog, opLock, publisher, port)
	srv := server.NewServer(
		robotAdapter,
		hub,
		estop,
		limiter,
		watchdog,
		opLock,
		publisher,
		":8080",
	)

	if err := srv.Start(context.Background()); err != nil {
		log.Fatalf("❌ サーバーエラー: %v", err)
	}
}
