// =============================================================================
// ファイル: main.go（メインエントリーポイント）
// 概要: ロボットAIゲートウェイサーバーの起動・停止を管理するメインファイル
//
// このファイルは、アプリケーション全体の「入口」です。
// Go言語では、プログラムは必ず「main」パッケージの「main」関数から実行されます。
//
// このゲートウェイは以下の役割を担います：
//   - WebSocketサーバーとして動作し、フロントエンド（ブラウザ）とリアルタイム通信
//   - ロボットアダプターを介してロボットを制御
//   - センサーデータをクライアントに配信
//   - Redisにデータを永続化（記録）
//   - 安全機構（緊急停止、速度制限など）を提供
//
// 【設計パターン: グレースフルシャットダウン（Graceful Shutdown）】
//
//	サーバーを停止する際に、処理中のリクエストを適切に完了してから終了する仕組み。
//	Ctrl+Cやkillコマンドで送られるシグナルをキャッチして、安全に停止します。
//
// =============================================================================
package main

import (
	// --- Go標準ライブラリ ---

	// context: ゴルーチン（goroutine）のキャンセルやタイムアウトを管理するパッケージ。
	// 「この処理はもう不要だから止めて」と伝える仕組み。
	// 例：サーバー停止時に全てのバックグラウンド処理を停止させる。
	"context"

	// fmt: 文字列のフォーマット（整形）と出力を行うパッケージ。
	// Fprintf でエラーメッセージを標準エラー出力に書き込む。
	"fmt"

	// net/http: HTTPサーバー・クライアントを提供するパッケージ。
	// WebSocketのための基盤となるHTTPサーバーを構築するのに使用。
	"net/http"

	// os: オペレーティングシステムとの対話を提供するパッケージ。
	// 環境変数の読み取り、プロセスの終了などに使用。
	"os"

	// os/signal: OSからのシグナル（Ctrl+Cなど）を受け取るパッケージ。
	// サーバーの安全な停止（グレースフルシャットダウン）に使用。
	"os/signal"

	// syscall: 低レベルのOSシステムコールを定義するパッケージ。
	// SIGINT（Ctrl+C）やSIGTERM（終了要求）などのシグナル定数を使用。
	"syscall"

	// time: 時間に関する操作を提供するパッケージ。
	// タイムアウトの設定、時間の計測などに使用。
	"time"

	// --- プロジェクト内部パッケージ ---

	// adapter: ロボットとの通信を抽象化するアダプターパッケージ。
	// 異なる種類のロボットを統一的に扱うためのインターフェースを提供。
	// 【設計パターン: アダプターパターン】
	// 異なるインターフェースを持つロボットを、共通のインターフェースで扱えるようにする。
	"github.com/robot-ai-webapp/gateway/internal/adapter"

	// mock: テスト・開発用のモック（偽物）ロボットアダプター。
	// 実際のロボットがなくても開発・テストできるようにする。
	// 【設計パターン: ファクトリーパターン】
	// mock.Factory は、モックアダプターを生成する「工場関数」。
	"github.com/robot-ai-webapp/gateway/internal/adapter/mock"

	// bridge: 外部サービス（Redis）との橋渡し（ブリッジ）を担当するパッケージ。
	// センサーデータやコマンドをRedisに記録する機能を提供。
	"github.com/robot-ai-webapp/gateway/internal/bridge"

	// config: 設定の読み込みを担当するパッケージ。
	// 環境変数やデフォルト値から設定を構築する。
	"github.com/robot-ai-webapp/gateway/internal/config"

	// mw: ミドルウェアパッケージ（エイリアスで短縮名「mw」を付けている）。
	// 【Go言語の知識: パッケージエイリアス】
	//
	//	import時に別名を付けることで、長いパッケージ名を短縮したり、
	//	名前の衝突を避けたりできます。
	//	例: mw "..." で、middleware の代わりに mw.XXX と書ける。
	mw "github.com/robot-ai-webapp/gateway/internal/middleware"

	// protocol: WebSocketメッセージの形式（プロトコル）を定義するパッケージ。
	// メッセージのエンコード（変換）・デコード（復元）も担当。
	"github.com/robot-ai-webapp/gateway/internal/protocol"

	// safety: ロボットの安全機構を提供するパッケージ。
	// 緊急停止、速度制限、タイムアウト監視などの安全機能。
	"github.com/robot-ai-webapp/gateway/internal/safety"

	// server: WebSocketサーバーの中核を提供するパッケージ。
	// Hub（接続管理）、Handler（メッセージ処理）を含む。
	"github.com/robot-ai-webapp/gateway/internal/server"

	// --- 外部ライブラリ ---

	// zap: Uber社が開発した高性能ログライブラリ。
	// 構造化ログ（JSON形式）を高速に出力できる。
	// zap.Int(), zap.String() などでログにフィールドを追加する。
	"go.uber.org/zap"

	// zapcore: zapの内部構成要素を提供するパッケージ。
	// ログレベル（Debug, Info, Warn, Error）の定義に使用。
	"go.uber.org/zap/zapcore"
)

// =============================================================================
// main関数: プログラムのエントリーポイント（入口）
//
// 【Go言語の基本】
//   - Go言語のプログラムは必ず main パッケージの main() 関数から始まる
//   - main() は引数なし・戻り値なし
//   - os.Exit() でプロセスの終了コードを指定して終了できる
//
// この関数では以下の順序で処理を行います：
//  1. 設定を読み込む
//  2. ロガー（ログ出力器）を初期化する
//  3. Redisに接続する
//  4. アダプター（ロボット通信）を初期化する
//  5. 安全機構を初期化する
//  6. WebSocket Hub（接続管理）を起動する
//  7. モックロボットを作成・接続する
//  8. HTTPサーバーを起動する
//  9. 停止シグナルを待って、グレースフルシャットダウンする
//
// =============================================================================
func main() {
	// -------------------------------------------------------------------------
	// ステップ1: 設定を読み込む
	// -------------------------------------------------------------------------
	// config.Load() は環境変数やデフォルト値から設定を構築して返す。
	// 【Go言語の知識: 多値返却（Multiple Return Values）】
	//
	//	Goの関数は複数の値を返すことができる。
	//	特に (結果, エラー) のパターンは Go で最も一般的なエラーハンドリング手法。
	//	err != nil ならエラーが発生したことを意味する。
	cfg, err := config.Load()
	if err != nil {
		// 【Go言語の知識: fmt.Fprintf】
		//
		//	os.Stderr（標準エラー出力）にエラーメッセージを書き込む。
		//	%v はエラーの内容を文字列として埋め込むフォーマット指定子。
		fmt.Fprintf(os.Stderr, "Failed to load config: %v\n", err)
		// 【Go言語の知識: os.Exit(1)】
		//
		//	プログラムを終了コード 1 で即座に終了する。
		//	0 = 正常終了、1 = エラー終了（Unix/Linuxの慣例）。
		os.Exit(1)
	}

	// -------------------------------------------------------------------------
	// ステップ2: ロガー（ログ出力器）を初期化する
	// -------------------------------------------------------------------------
	// ログレベルに応じたロガーを生成。
	// ログレベルとは、出力するログの詳細度を制御する仕組み。
	// debug > info > warn > error の順に、より重要なログだけ出力される。
	logger := initLogger(cfg.Logging.Level)

	// 【Go言語の知識: defer（ディファー）】
	//
	//	defer は「この関数が終了する直前に実行する」という予約。
	//	main() が終了する直前に logger.Sync() が呼ばれ、
	//	バッファに残っているログを確実に出力する。
	//	複数の defer がある場合、LIFO（後入れ先出し）の順で実行される。
	defer logger.Sync()

	// ログを出力。zap.Int(), zap.String() で構造化ログフィールドを追加。
	// 構造化ログは JSON 形式で出力されるため、ログ解析ツールで検索しやすい。
	logger.Info("Starting Robot AI Gateway",
		zap.Int("ws_port", cfg.Server.Port),
		zap.Int("grpc_port", cfg.Server.GRPCPort),
	)

	// -------------------------------------------------------------------------
	// ステップ3: Redisに接続する
	// -------------------------------------------------------------------------
	// Redis はインメモリデータストア（高速なデータベース）。
	// センサーデータやコマンドを一時的に保存し、バックエンドで利用可能にする。
	//
	// 接続に失敗しても、Redis なしで動作を継続する（degraded mode）。
	// これにより、開発環境で Redis がなくても動作可能。
	redisPublisher, err := bridge.NewRedisPublisher(cfg.Redis.URL, logger)
	if err != nil {
		// logger.Warn: 警告レベルのログ。エラーではないが注意が必要な状況。
		logger.Warn("Redis connection failed, running without persistence", zap.Error(err))
		// 接続失敗時は nil（null）を設定し、後で nil チェックで使用を回避する。
		redisPublisher = nil
	}

	// -------------------------------------------------------------------------
	// ステップ4: アダプターレジストリ（登録簿）を初期化する
	// -------------------------------------------------------------------------
	// 【設計パターン: レジストリパターン + ファクトリーパターン】
	//
	//	Registry: 利用可能なアダプタの種類を管理する「登録簿」。
	//	Factory: アダプタを生成する「工場関数」。
	//	これにより、新しいロボットの種類を追加する際は、
	//	ファクトリーを登録するだけで済む（拡張が容易）。
	registry := adapter.NewRegistry(logger)
	// "mock" タイプのアダプターを登録。mock.Factory がモックアダプターを生成する関数。
	registry.RegisterFactory("mock", mock.Factory)

	// -------------------------------------------------------------------------
	// ステップ5: 安全機構を初期化する
	// -------------------------------------------------------------------------
	// ロボット制御では安全性が最重要。複数の安全レイヤーで保護する。

	// EStopManager: 緊急停止（Emergency Stop）を管理。
	// 緊急時にロボットの全動作を即座に停止させる。
	estopMgr := safety.NewEStopManager(registry, logger)

	// VelocityLimiter: 速度制限器。
	// ロボットの移動速度が設定された上限を超えないようにする。
	// MaxLinearVelocity: 直線速度の上限、MaxAngularVelocity: 回転速度の上限。
	velLimiter := safety.NewVelocityLimiter(cfg.Safety.MaxLinearVelocity, cfg.Safety.MaxAngularVelocity, logger)

	// OperationLock: 操作ロック。
	// 同時に一人のユーザーだけがロボットを操作できるようにする（排他制御）。
	opLock := safety.NewOperationLock(cfg.Safety.OperationLockTimeout(), logger)

	// TimeoutWatchdog: タイムアウト監視（ウォッチドッグ）。
	// 一定時間コマンドが来ない場合、ロボットを安全に停止させる。
	// これにより、通信が途切れた場合の暴走を防ぐ。
	watchdog := safety.NewTimeoutWatchdog(cfg.Safety.CommandTimeout(), registry, logger)

	// -------------------------------------------------------------------------
	// ステップ6: WebSocket Hub（接続管理ハブ）を起動する
	// -------------------------------------------------------------------------
	// Hub はすべてのWebSocket接続を管理する中央管理者。
	// クライアントの接続・切断・メッセージ配信を一元管理する。
	hub := server.NewHub(logger)

	// 【Go言語の知識: ゴルーチン（goroutine）】
	//
	//	「go 関数名()」で、その関数を別のスレッド（軽量スレッド）で並行実行する。
	//	ゴルーチンは Go 言語の最も重要な機能の一つで、
	//	何千もの並行処理を効率的に実行できる。
	//	ここでは Hub のメインループをバックグラウンドで実行している。
	go hub.Run()

	// -------------------------------------------------------------------------
	// ステップ7: ハンドラー（メッセージ処理器）を作成する
	// -------------------------------------------------------------------------
	// 【Go言語の知識: インターフェース（interface）】
	//
	//	var publisher server.RedisPublisher は、インターフェース型の変数宣言。
	//	インターフェースは「どんなメソッドを持つべきか」だけを定義し、
	//	実装の詳細は気にしない。これにより疎結合（loose coupling）を実現。
	//	nil（null）も有効な値として扱える。
	var publisher server.RedisPublisher
	if redisPublisher != nil {
		publisher = redisPublisher
	}

	// Handler: WebSocketメッセージを受け取り、適切な処理を行うハンドラー。
	// 依存するコンポーネントを全て引数として受け取る（依存性注入: DI）。
	// 【設計パターン: 依存性注入（Dependency Injection）】
	//
	//	コンポーネントが必要とする依存オブジェクトを外部から渡す手法。
	//	テストしやすく、モジュール間の結合度が低くなる。
	handler := server.NewHandler(hub, registry, estopMgr, velLimiter, watchdog, opLock, publisher, logger)
	wsServer := server.NewWebSocketServer(hub, handler, logger)

	// -------------------------------------------------------------------------
	// ステップ8: バックグラウンド処理を開始する
	// -------------------------------------------------------------------------
	// 【Go言語の知識: context.WithCancel】
	//
	//	キャンセル可能なコンテキストを作成する。
	//	cancel() を呼ぶと、ctx.Done() チャネルが閉じられ、
	//	ctx を使っているすべてのゴルーチンに「停止してください」と伝わる。
	//	これがゴルーチンのライフサイクル管理の基本パターン。
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// ウォッチドッグ（タイムアウト監視）をバックグラウンドで開始。
	// ctx がキャンセルされると自動的に停止する。
	watchdog.Start(ctx)

	// 操作ロックのクリーンアップ処理を開始。
	// 【Go言語の知識: チャネル（channel）】
	//
	//	チャネルはゴルーチン間でデータをやり取りするための仕組み。
	//	make(chan struct{}) は「シグナル専用」のチャネルを作成する。
	//	struct{} は空の構造体で、メモリを消費しない（シグナルだけに使う）。
	//	close(done) でチャネルを閉じると、受信側に「終了」のシグナルが伝わる。
	done := make(chan struct{})
	opLock.StartCleanup(done)

	// -------------------------------------------------------------------------
	// ステップ9: モックロボットを作成・接続する（開発用）
	// -------------------------------------------------------------------------
	// 開発時は実際のロボットがないため、モック（偽物）のロボットを使う。
	// 実運用では、実際のロボットのアダプターに置き換える。
	mockAdapter, err := registry.CreateAdapter("mock-robot-1", "mock")
	if err != nil {
		// logger.Fatal: 致命的エラー。ログ出力後にプロセスを即座に終了する。
		logger.Fatal("Failed to create mock adapter", zap.Error(err))
	}
	// モックロボットに接続開始。nil はオプション設定がないことを示す。
	if err := mockAdapter.Connect(ctx, nil); err != nil {
		logger.Fatal("Failed to connect mock adapter", zap.Error(err))
	}

	// -------------------------------------------------------------------------
	// ステップ10: センサーデータ転送ゴルーチンを開始する
	// -------------------------------------------------------------------------
	// Codec: メッセージのエンコード（バイト列への変換）・デコード（復元）を担当。
	codec := protocol.NewCodec()

	// センサーデータをロボットから受信し、WebSocketクライアントとRedisに転送する
	// ゴルーチンをバックグラウンドで開始。
	go forwardSensorData(ctx, "mock-robot-1", mockAdapter, hub, codec, redisPublisher, logger)

	// -------------------------------------------------------------------------
	// ステップ11: HTTPサーバーを設定・起動する
	// -------------------------------------------------------------------------
	// レート制限器を作成（1分あたり120リクエストまで許可）。
	// 【設計パターン: トークンバケット（Token Bucket）】
	//
	//	一定間隔でトークン（許可券）が補充され、
	//	リクエストごとにトークンを消費する。
	//	トークンがなくなるとリクエストを拒否する。
	//	DDoS攻撃やサーバー過負荷を防ぐための仕組み。
	rateLimiter := mw.NewRateLimiter(120, logger)

	// 【Go言語の知識: ServeMux（マルチプレクサ）】
	//
	//	HTTPリクエストのURLパスに応じて、適切なハンドラーに振り分ける「ルーター」。
	//	HandleFunc でパスとハンドラー関数を登録する。
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", wsServer.HandleWebSocket)   // WebSocket接続エンドポイント
	mux.HandleFunc("/health", wsServer.HealthHandler) // ヘルスチェック用（監視ツール用）
	mux.HandleFunc("/ready", wsServer.HealthHandler)  // 準備完了チェック用（Kubernetes用）

	// 【Go言語の知識: 構造体リテラル（Struct Literal）と & 演算子】
	//
	//	&http.Server{...} は http.Server 構造体を作成し、そのポインタを返す。
	//	ポインタを使うことで、同じインスタンスを複数箇所で共有できる。
	//
	// 【設計パターン: ミドルウェアチェーン】
	//
	//	Handler フィールドで複数のミドルウェアが入れ子になっている：
	//	rateLimiter.Middleware(  // 外側: レート制限
	//	  LoggingMiddleware(     // 内側: ログ記録
	//	    mux                  // 中心: 実際のルーティング
	//	  )
	//	)
	//	リクエストは外側から内側に通過し、レスポンスは内側から外側に戻る。
	httpServer := &http.Server{
		// fmt.Sprintf で "ホスト:ポート" 形式のアドレス文字列を生成。
		Addr:         fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port),
		Handler:      rateLimiter.Middleware(mw.LoggingMiddleware(logger)(mux)),
		ReadTimeout:  15 * time.Second, // リクエスト読み取りのタイムアウト
		WriteTimeout: 15 * time.Second, // レスポンス書き込みのタイムアウト
		IdleTimeout:  60 * time.Second, // キープアライブ接続のアイドルタイムアウト
	}

	// サーバーを別のゴルーチンで起動する。
	// メインゴルーチンはシグナル待ちに使うため、サーバーはバックグラウンドで動かす。
	go func() {
		logger.Info("WebSocket server starting", zap.String("addr", httpServer.Addr))
		// ListenAndServe: 指定アドレスでHTTPリクエストの受付を開始する。
		// この関数はサーバーが停止するまでブロック（待機）し続ける。
		// 正常に Shutdown() された場合は http.ErrServerClosed を返す。
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Server failed", zap.Error(err))
		}
	}()

	// -------------------------------------------------------------------------
	// ステップ12: グレースフルシャットダウン（安全な停止）
	// -------------------------------------------------------------------------
	// 【設計パターン: グレースフルシャットダウン（Graceful Shutdown）】
	//   1. OS からの停止シグナル（Ctrl+C, kill）を受け取る
	//   2. 新しいリクエストの受付を停止する
	//   3. 処理中のリクエストが完了するのを待つ
	//   4. リソース（DB接続、ファイルなど）を解放する
	//   5. プロセスを終了する

	// シグナルを受け取るためのチャネルを作成（バッファサイズ 1）。
	// 【Go言語の知識: バッファ付きチャネル】
	//
	//	make(chan os.Signal, 1) はバッファサイズ 1 のチャネルを作成。
	//	バッファにより、シグナル送信側が受信を待たずに済む。
	sigCh := make(chan os.Signal, 1)

	// signal.Notify: 指定したシグナルを sigCh チャネルに通知するよう登録。
	// SIGINT: Ctrl+C で送られるシグナル。
	// SIGTERM: kill コマンドや Docker stop で送られるシグナル。
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	// 【Go言語の知識: <-ch（チャネル受信）】
	//
	//	<-sigCh はチャネルからデータを受信するまでブロック（待機）する。
	//	ここでは、Ctrl+C が押されるまでプログラムがここで待機する。
	<-sigCh

	logger.Info("Shutting down gracefully...")

	// すべてのバックグラウンドゴルーチンにキャンセルを通知。
	// cancel() を呼ぶと、ctx.Done() チャネルが閉じられ、
	// ctx を使っているすべてのゴルーチン内の select 文の case <-ctx.Done() が発火する。
	cancel()
	// done チャネルを閉じて、opLock のクリーンアップゴルーチンを停止。
	close(done)

	// モックロボットとの接続を切断。
	// 【Go言語の知識: _ （アンダースコア）によるエラー無視】
	//
	//	_ = は戻り値のエラーを意図的に無視することを明示。
	//	シャットダウン時のエラーは通常無視しても問題ないため。
	//	ただし、通常のコードでは err を必ずチェックすべき。
	_ = mockAdapter.Disconnect(context.Background())

	// Redis接続を閉じる。
	if redisPublisher != nil {
		_ = redisPublisher.Close()
	}

	// HTTPサーバーを停止する。
	// 【Go言語の知識: context.WithTimeout】
	//
	//	10秒以内にシャットダウンが完了しなければ強制終了する。
	//	タイムアウト付きコンテキストにより、永遠に待ち続けることを防ぐ。
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	// httpServer.Shutdown: 新しい接続を受け付けず、既存の接続が完了するのを待つ。
	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server shutdown error", zap.Error(err))
	}

	logger.Info("Gateway stopped")
}

// =============================================================================
// forwardSensorData: センサーデータをロボットからクライアントに転送する関数
//
// この関数はゴルーチンとして実行され、ロボットのセンサーデータを
// 継続的に受信し、以下の2つの宛先に転送します：
//  1. WebSocketクライアントへのリアルタイム配信（Hub経由）
//  2. Redisへの永続化（バックエンドでの記録・分析用）
//
// 【Go言語の知識: チャネルと select 文】
//
//	この関数は Go 言語の並行処理の典型的なパターンを示しています：
//	- チャネルからデータを受信する
//	- select 文で複数のチャネルを同時に監視する
//	- context のキャンセルで安全に停止する
//
// 引数の説明：
//
//	ctx           : キャンセル可能なコンテキスト。停止シグナルを受け取る
//	robotID       : ロボットの一意な識別子（例: "mock-robot-1"）
//	adp           : ロボットアダプター（センサーデータのソース）
//	hub           : WebSocket Hub（クライアントへの配信を管理）
//	codec         : メッセージのエンコーダー（バイト列に変換）
//	redisPublisher: Redis への発行者（nil の場合は Redis に記録しない）
//	logger        : ログ出力器
//
// =============================================================================
func forwardSensorData(
	ctx context.Context,
	robotID string,
	adp adapter.RobotAdapter,
	hub *server.Hub,
	codec *protocol.Codec,
	redisPublisher *bridge.RedisPublisher,
	logger *zap.Logger,
) {
	// ロボットアダプターからセンサーデータを受信するチャネルを取得。
	// 【Go言語の知識: チャネル（Channel）の方向】
	//
	//	SensorDataChannel() は受信専用チャネル (<-chan SensorData) を返す。
	//	これにより、この関数はチャネルにデータを送信できない（読み取り専用）。
	ch := adp.SensorDataChannel()

	// 【Go言語の知識: for ループ + select 文による無限ループ】
	//
	//	for { ... } は無限ループ。
	//	select { ... } は複数のチャネル操作を同時に待つ構文。
	//	最初に準備ができた case が実行される。
	//	これが Go のゴルーチンにおけるイベントループの基本パターン。
	for {
		select {
		// ctx がキャンセルされたら（main で cancel() が呼ばれたら）ループを終了。
		case <-ctx.Done():
			return

		// センサーデータチャネルからデータを受信。
		// data: 受信したセンサーデータ
		// ok: チャネルが閉じられた場合は false になる
		case data, ok := <-ch:
			// チャネルが閉じられた場合は関数を終了。
			// 【Go言語の知識: チャネルのクローズ検出】
			//
			//	チャネルが閉じられると、受信操作はゼロ値と false を返す。
			//	これにより、データソースの終了を検出できる。
			if !ok {
				return
			}

			// ロボットIDをセンサーデータに設定（どのロボットからのデータか識別するため）。
			data.RobotID = robotID

			// --- WebSocket クライアントへの転送 ---

			// WebSocket用のメッセージを作成。
			// protocol.NewMessage: タイプとロボットIDを指定してメッセージ構造体を生成。
			msg := protocol.NewMessage(protocol.MsgTypeSensorData, robotID)
			msg.Topic = data.Topic

			// 【Go言語の知識: map[string]any（マップ）】
			//
			//	map[string]any は「文字列キー → 任意の型の値」のマップ。
			//	any は interface{} のエイリアスで、どんな型でも格納できる。
			//	JSON のオブジェクトに似た構造。
			msg.Payload = map[string]any{
				"data_type": data.DataType,
				"frame_id":  data.FrameID,
				"data":      data.Data,
			}

			// メッセージをバイト列にエンコード（MessagePack形式）。
			encoded, err := codec.Encode(msg)
			if err != nil {
				logger.Error("Failed to encode sensor data", zap.Error(err))
				// 【Go言語の知識: continue】
				//
				//	ループの残りの処理をスキップし、次のイテレーション（繰り返し）に進む。
				//	エンコードに失敗したデータは諦めて、次のデータを処理する。
				continue
			}
			// 指定したロボットIDのクライアントにブロードキャスト（一斉送信）。
			hub.BroadcastToRobot(robotID, encoded)

			// --- Redis への永続化 ---
			// Redis が有効な場合のみ、センサーデータを Redis Stream に発行。
			// Redis Stream はログのような時系列データに最適。
			if redisPublisher != nil {
				_ = redisPublisher.PublishSensorData(ctx, robotID, data)
			}
		}
	}
}

// =============================================================================
// initLogger: ログレベルに応じた zap ロガーを初期化する関数
//
// ログレベルは「どの程度詳細なログを出力するか」を制御する仕組み。
// - debug: 最も詳細。開発時のデバッグ情報を含む
// - info:  通常の動作状況。本番環境向け
// - warn:  警告。問題の予兆だが、動作は継続可能
// - error: エラー。問題が発生したが、プロセスは継続
//
// 【Go言語の知識: switch文】
//
//	switch は複数の条件分岐を簡潔に書くための構文。
//	Go の switch は C/Java と異なり、自動的に break される（fall-through しない）。
//	default は、どの case にも一致しない場合に実行される。
//
// =============================================================================
func initLogger(level string) *zap.Logger {
	// zapcore.Level: ログレベルの型。数値で定義されている。
	var zapLevel zapcore.Level
	switch level {
	case "debug":
		zapLevel = zapcore.DebugLevel
	case "info":
		zapLevel = zapcore.InfoLevel
	case "warn":
		zapLevel = zapcore.WarnLevel
	case "error":
		zapLevel = zapcore.ErrorLevel
	default:
		// 不明なレベルの場合は info をデフォルトにする。
		zapLevel = zapcore.InfoLevel
	}

	// 【Go言語の知識: 構造体の初期化】
	//
	//	zap.Config{...} で構造体を初期化する。
	//	フィールド名: 値 の形式で指定。指定しないフィールドはゼロ値になる。
	config := zap.Config{
		// ログレベルの設定。AtomicLevel は実行中に動的に変更可能。
		Level: zap.NewAtomicLevelAt(zapLevel),
		// debug レベルの場合は開発モードを有効化（スタックトレースなどが追加される）。
		Development: zapLevel == zapcore.DebugLevel,
		// "json": ログを JSON 形式で出力する（構造化ログ）。
		// 本番環境では JSON が推奨（ログ解析ツールとの互換性）。
		Encoding: "json",
		// エンコーダーの設定。本番用のプリセットを使用。
		EncoderConfig: zap.NewProductionEncoderConfig(),
		// ログ出力先。"stdout" は標準出力。
		OutputPaths: []string{"stdout"},
		// エラーログの出力先。"stderr" は標準エラー出力。
		ErrorOutputPaths: []string{"stderr"},
	}
	// タイムスタンプのキー名を "timestamp" に変更（デフォルトは "ts"）。
	config.EncoderConfig.TimeKey = "timestamp"
	// タイムスタンプの形式を ISO 8601 にする（例: "2026-02-15T10:30:00.000Z"）。
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	// Build(): 設定からロガーインスタンスを構築する。
	logger, err := config.Build()
	if err != nil {
		// 【Go言語の知識: panic】
		//
		//	panic はプログラムを即座に停止させる。
		//	ロガーの初期化失敗は回復不可能なエラーのため panic を使用。
		//	通常のエラーハンドリングには使わず、本当に致命的な場合のみ使う。
		panic(err)
	}
	return logger
}
