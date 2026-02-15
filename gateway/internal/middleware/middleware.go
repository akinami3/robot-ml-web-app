// =============================================================================
// ファイル: middleware.go（ミドルウェア）
// 概要: HTTPリクエストの前後に共通処理を挟む「ミドルウェア」を提供するパッケージ
//
// 【設計パターン: ミドルウェア（Middleware）パターン】
//
//	ミドルウェアは、HTTPリクエストがハンドラーに到達する前・後に
//	共通処理を挟み込む仕組みです。玉ねぎの皮のような層構造になっています。
//
//	リクエスト → [レート制限] → [ログ記録] → [ハンドラー] → [ログ記録] → [レート制限] → レスポンス
//
//	各ミドルウェアは次のミドルウェア（または最終ハンドラー）を呼び出す前後に
//	独自の処理を行えます。これにより：
//	- コードの再利用性が高まる（同じ処理を全エンドポイントに適用）
//	- 関心の分離（認証、ログ、制限を別々に管理）
//	- 組み合わせの自由度（必要なミドルウェアだけ使える）
//
// このファイルでは以下の2つのミドルウェアを実装しています：
//  1. RateLimiter: レート制限（過剰リクエストの防止）
//  2. LoggingMiddleware: リクエストのログ記録
//
// =============================================================================
package middleware

import (
	// net/http: Go 標準のHTTPパッケージ。
	// http.Handler インターフェースと http.HandlerFunc 型が重要。
	// 【Go言語の知識: http.Handler インターフェース】
	//
	//	type Handler interface {
	//	    ServeHTTP(ResponseWriter, *Request)
	//	}
	//	このインターフェースを満たす型は、HTTPリクエストを処理できる。
	//	ミドルウェアは Handler を受け取って Handler を返すことで「ラッピング」する。
	"net/http"

	// sync: 同期プリミティブ（排他制御や待機など）を提供する標準ライブラリ。
	// sync.Mutex（ミューテックス）を使って、複数のゴルーチンからの
	// 同時アクセスを安全に制御する。
	"sync"

	// time: 時間に関する操作を提供する標準ライブラリ。
	// レート制限のインターバル計算やリクエストの処理時間計測に使用。
	"time"

	// zap: 高性能構造化ログライブラリ。
	"go.uber.org/zap"
)

// =============================================================================
// RateLimiter: レート制限器（トークンバケットアルゴリズム）
//
// 【設計パターン: トークンバケット（Token Bucket）アルゴリズム】
//
//	レート制限は「一定時間内のリクエスト数を制限する」仕組み。
//	バケツ（bucket）にトークンが入っていて：
//	- リクエストごとにトークンを1つ消費する
//	- 一定時間（ここでは1分）ごとにトークンが全回復する
//	- トークンがなくなるとリクエストを拒否する（HTTP 429 Too Many Requests）
//
//	これにより、DDoS攻撃やAPIの過剰使用を防ぐことができます。
//
//	例: ratePerMinute=120 の場合
//	→ 各IPアドレスは1分間に120回までリクエストできる
//	→ 超えると 429 エラーが返される
//	→ 1分経つとトークンがリセットされる
//
// 【Go言語の知識: 構造体のフィールド】
//
//	大文字で始まるフィールド → エクスポートされる（外部パッケージからアクセス可能）
//	小文字で始まるフィールド → プライベート（同パッケージ内からのみアクセス可能）
//	ここでは全フィールドが小文字なので、外部から直接アクセスできない（カプセル化）。
//
// =============================================================================
type RateLimiter struct {
	// 【Go言語の知識: sync.Mutex（ミューテックス = 排他制御）】
	//
	//	複数のゴルーチン（スレッド）が同時にデータを読み書きすると
	//	データ競合（race condition）が発生する可能性がある。
	//	Mutex は「一つのゴルーチンだけがアクセスできる」ようにするロック機構。
	//	mu.Lock() でロック、mu.Unlock() でアンロックする。
	mu       sync.Mutex
	tokens   map[string]*bucket // IPアドレスごとのトークンバケット
	rate     int                // 1インターバルあたりの最大リクエスト数
	interval time.Duration      // トークンがリセットされるインターバル（ここでは1分）
	logger   *zap.Logger        // ログ出力器
}

// =============================================================================
// bucket: 各IPアドレス（クライアント）ごとのトークン状態を管理する内部構造体
//
// 【なぜ小文字で始まるのか？】
//
//	小文字で始まる型名は「非エクスポート」（= プライベート）。
//	このパッケージの外からは使えない内部実装の詳細。
//	外部に公開する必要がない型は小文字にするのが Go の慣例。
//
// =============================================================================
type bucket struct {
	tokens    int       // 残りトークン数
	lastReset time.Time // 最後にトークンがリセットされた時刻
}

// =============================================================================
// NewRateLimiter: レート制限器を作成するコンストラクタ関数
//
// 【Go言語の知識: コンストラクタパターン】
//
//	Go にはクラスのコンストラクタがないため、
//	New〇〇() という命名規則の関数で構造体を初期化するのが慣例。
//	この関数は初期化済みのポインタを返す。
//
// 引数:
//
//	ratePerMinute: 1分あたりの最大リクエスト数
//	logger: ログ出力器
//
// 戻り値:
//
//	初期化された RateLimiter のポインタ
//
// =============================================================================
func NewRateLimiter(ratePerMinute int, logger *zap.Logger) *RateLimiter {
	// 【Go言語の知識: make関数】
	//
	//	make() はスライス、マップ、チャネルを初期化するための組み込み関数。
	//	make(map[string]*bucket) は空のマップを作成する。
	//	マップは使う前に make で初期化しないと nil マップとなり、
	//	書き込み時に panic が発生する。
	return &RateLimiter{
		tokens:   make(map[string]*bucket),
		rate:     ratePerMinute,
		interval: time.Minute, // time.Minute は 1分を表す定数
		logger:   logger,
	}
}

// =============================================================================
// Middleware: レート制限を適用するHTTPミドルウェアを返すメソッド
//
// 【Go言語の知識: http.Handler と http.HandlerFunc】
//
//	http.Handler はインターフェース（ServeHTTP メソッドを持つ型）。
//	http.HandlerFunc は関数型で、関数を http.Handler に変換するアダプター。
//
//	つまり、普通の関数（func(w, r)）を http.Handler インターフェースに
//	適合させるための仕組み。
//
// 【ミドルウェアの構造】
//
//	func(next http.Handler) http.Handler
//	→ next: 次に呼ぶべきハンドラー（チェーンの次の層）
//	→ 戻り値: next をラップした新しいハンドラー
//
//	処理の流れ:
//	1. レート制限チェック（リクエスト前の処理）
//	2. 制限内なら next.ServeHTTP() で次のハンドラーを呼ぶ
//	3. 制限超過なら 429 エラーを返して終了
//
// =============================================================================
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	// 【Go言語の知識: クロージャ（Closure）】
	//
	//	http.HandlerFunc(func(...) { ... }) は無名関数（クロージャ）。
	//	外側の変数（rl, next）を「キャプチャ」して内部で使用できる。
	//	rl と next はこの関数が作られた時点の値を参照し続ける。
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// クライアントのIPアドレスを取得。
		// RemoteAddr は "IPアドレス:ポート" 形式の文字列。
		ip := r.RemoteAddr

		// レート制限チェック。allow() が false を返したら制限超過。
		if !rl.allow(ip) {
			rl.logger.Warn("Rate limit exceeded", zap.String("ip", ip))
			// HTTP 429 Too Many Requests エラーを返す。
			// http.Error() はエラーメッセージとステータスコードをレスポンスに書き込む。
			http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
			// return で関数を終了。next.ServeHTTP() を呼ばないため、
			// 実際のハンドラーは実行されない（リクエストがブロックされる）。
			return
		}

		// レート制限内なら、次のハンドラーにリクエストを渡す。
		// 【Go言語の知識: ServeHTTP】
		//
		//	http.Handler インターフェースのメソッド。
		//	w: レスポンスを書き込む先（ResponseWriter）
		//	r: 受信したHTTPリクエスト（Request）
		next.ServeHTTP(w, r)
	})
}

// =============================================================================
// allow: 指定キー（IPアドレス）のリクエストを許可するかチェックする内部メソッド
//
// トークンバケットアルゴリズムの核心部分。
//
// 【Go言語の知識: sync.Mutex の使い方】
//
//	複数のHTTPリクエストが同時に来た場合、tokens マップに同時アクセスされる。
//	データ競合を防ぐため、Mutex でロック・アンロックする。
//
//	mu.Lock()   → ロック取得（他のゴルーチンはここで待機）
//	defer mu.Unlock() → 関数終了時に自動アンロック
//
//	defer を使うことで、どの return パスでも確実にアンロックされる。
//	ロック忘れやアンロック忘れを防ぐ Go の重要なイディオム。
//
// =============================================================================
func (rl *RateLimiter) allow(key string) bool {
	// Mutex をロックして排他制御を開始。
	rl.mu.Lock()
	// 【Go言語の知識: defer + Unlock】
	//
	//	defer は「関数の終了時に実行」を予約する。
	//	これにより、どの return で抜けても Unlock が確実に呼ばれる。
	//	ロック・アンロックの対はバグの温床なので、defer で安全に管理する。
	defer rl.mu.Unlock()

	now := time.Now()

	// マップからこのキー（IPアドレス）のバケットを取得。
	// 【Go言語の知識: マップの2値返却】
	//
	//	b, ok := map[key] で、ok はキーが存在するかの真偽値。
	//	キーが存在しない場合は ok == false となる。
	b, ok := rl.tokens[key]
	if !ok {
		// 新しいIPアドレスの場合、バケットを作成（トークンを1つ使用済み）。
		// rate - 1 は、今回のリクエストで1トークン消費するため。
		rl.tokens[key] = &bucket{tokens: rl.rate - 1, lastReset: now}
		return true // 新規なので許可
	}

	// インターバル（1分）が経過していたら、トークンをリセット。
	// 【Go言語の知識: time.Sub() と比較】
	//
	//	now.Sub(b.lastReset) は「現在時刻 - 最終リセット時刻」の期間を返す。
	//	>= rl.interval で、インターバル以上経過しているかチェック。
	if now.Sub(b.lastReset) >= rl.interval {
		b.tokens = rl.rate - 1 // トークンをリセット（1つ消費）
		b.lastReset = now      // リセット時刻を更新
		return true            // リセットしたので許可
	}

	// トークンが残っている場合。
	if b.tokens > 0 {
		b.tokens--  // トークンを1つ消費
		return true // 許可
	}

	// トークン切れ → リクエスト拒否
	return false
}

// =============================================================================
// LoggingMiddleware: HTTPリクエストをログに記録するミドルウェア
//
// 【設計パターン: 高階関数（Higher-Order Function）】
//
//	「関数を引数に取る関数」または「関数を返す関数」を高階関数と呼ぶ。
//	この関数は「logger を受け取り、ミドルウェア関数を返す」高階関数。
//
//	呼び出し方: LoggingMiddleware(logger)(mux)
//	1. LoggingMiddleware(logger) → func(http.Handler) http.Handler を返す
//	2. その戻り値に (mux) を渡して最終的なハンドラーを取得
//
// 【ログに記録する情報】
//   - method: HTTPメソッド（GET, POST など）
//   - path: リクエストされたURLパス
//   - remote_addr: クライアントのIPアドレス
//   - duration: リクエストの処理にかかった時間
//
// =============================================================================
func LoggingMiddleware(logger *zap.Logger) func(http.Handler) http.Handler {
	// 外側の関数: logger を受け取る
	return func(next http.Handler) http.Handler {
		// 中間の関数: next ハンドラーを受け取る
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// リクエスト処理前に開始時刻を記録。
			start := time.Now()

			// 次のハンドラー（実際の処理）を呼び出す。
			next.ServeHTTP(w, r)

			// リクエスト処理後にログを出力。
			// 【Go言語の知識: time.Since(start)】
			//
			//	time.Since(start) は time.Now().Sub(start) と同じ。
			//	開始時刻からの経過時間を Duration として返す。
			//	zap.Duration で自動的にフォーマットされる（例: "1.234ms"）。
			logger.Info("HTTP request",
				zap.String("method", r.Method),              // HTTPメソッド（GET, POST等）
				zap.String("path", r.URL.Path),              // リクエストパス（/ws, /health等）
				zap.String("remote_addr", r.RemoteAddr),     // クライアントのIPアドレス
				zap.Duration("duration", time.Since(start)), // 処理時間
			)
		})
	}
}
