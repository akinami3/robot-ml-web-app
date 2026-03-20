// =============================================================================
// Step 1: Hello WebSocket — 最小限の WebSocket サーバー
// =============================================================================
//
// 【このファイルの概要】
// Go言語で書かれた、最小限のWebSocketサーバーです。
// ブラウザから接続して、テキストメッセージを双方向にやりとりできます。
//
// 【Go言語とは？】
// Googleが開発したプログラミング言語。シンプルで高速。
// 特に「並行処理」（複数の仕事を同時にこなすこと）が得意です。
// このプロジェクトでは、複数のブラウザから同時に接続されても
// 効率的に処理できるようにGoを使っています。
//
// 【このファイルの構成】
//   1. main()           — プログラムの入口。サーバーを起動する
//   2. handleWebSocket() — 新しいWebSocket接続を処理する
//   3. readPump()        — クライアントからのメッセージを受信し続ける
//   4. writePump()       — クライアントにデータを送信し続ける
//
// 【なぜ readPump と writePump を分けるの？】
// gorilla/websocket ライブラリのルール:
//   - 1つの接続に対して、同時に書き込めるのは1つのgoroutineだけ
//   - 読み取りと書き込みは別々のgoroutineで行う必要がある
// そのため「読む専用」と「書く専用」のループを分けています。
//
// =============================================================================
package main

// =============================================================================
// import — 使用するパッケージの宣言
// =============================================================================
//
// 【import とは？】
// 他の人（や自分）が書いたコードの「部品」を取り込む宣言です。
// Go言語では、使わないimportがあるとコンパイルエラーになります。
// （無駄なコードを持たない文化）
import (
	// --- Go 標準ライブラリ（Goに最初から入っているパッケージ）---

	// fmt: 文字列のフォーマット（整形）と出力
	// Println で画面にメッセージを表示するのに使います
	"fmt"

	// log: ログ出力（タイムスタンプ付きのメッセージ出力）
	// fmt.Println と似ていますが、日時が自動で付きます
	// 例: 2026/03/21 10:30:00 メッセージ受信: forward
	"log"

	// math/rand: 乱数（ランダムな数値）の生成
	// モックセンサーデータ（温度、バッテリーなど）を作るのに使います
	"math/rand"

	// net/http: HTTPサーバーの機能を提供
	// WebSocketは最初HTTPで接続してから「アップグレード」する仕組みなので、
	// まずHTTPサーバーが必要です
	"net/http"

	// time: 時刻の取得、タイマー、スリープなどの時間関連機能
	// 定期的にセンサーデータを送信するためのタイマーに使います
	"time"

	// --- 外部パッケージ（go.mod で管理、go mod tidy で自動取得）---

	// gorilla/websocket: Go で最も使われている WebSocket ライブラリ
	// HTTPの接続をWebSocketに「アップグレード」する機能を提供します
	"github.com/gorilla/websocket"
)

// =============================================================================
// 定数の定義
// =============================================================================
//
// 【const（定数）とは？】
// プログラム実行中に変わらない値。設定値を1箇所にまとめるのに使います。
// 変更したい時にここだけ直せばOK。
const (
	// サーバーが待ち受けるポート番号
	// ブラウザからは ws://localhost:8080/ws でアクセスします
	port = ":8080"

	// センサーデータの送信間隔（1秒ごと）
	// 【time.Second とは？】
	// Go言語の時間の単位。1 * time.Second = 1秒。
	// 500 * time.Millisecond = 0.5秒 のように細かく指定もできます。
	sensorInterval = 1 * time.Second
)

// =============================================================================
// upgrader — HTTP → WebSocket のアップグレード設定
// =============================================================================
//
// 【WebSocket の接続手順】
// 1. ブラウザが HTTP リクエストを送る（"WebSocketにアップグレードしたい"）
// 2. サーバーが OK すると、HTTP接続がWebSocket接続に「アップグレード」される
// 3. 以降は双方向通信が可能になる
//
// 【CheckOrigin について】
// 通常、WebSocketサーバーは「同じドメインからの接続のみ許可」します。
// ここでは学習用に全ての接続を許可しています（true を返す）。
// ⚠️ 本番環境では、許可するドメインを制限する必要があります！
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // 全てのオリジンを許可（開発用）
	},
}

// =============================================================================
// main — プログラムのエントリーポイント（入口）
// =============================================================================
//
// 【Go言語のルール】
// - プログラムは必ず `package main` の `func main()` から実行される
// - main() が終了すると、プログラム全体が終了する
//
// 【この関数の処理】
// 1. HTTPルーティングの設定（どのURLにアクセスしたら何をするか）
// 2. HTTPサーバーの起動（接続を待ち受ける）
func main() {
	// ルーティング: "/ws" というパスにアクセスが来たら handleWebSocket を呼ぶ
	// 【http.HandleFunc とは？】
	// 「このURLに来たら、この関数を実行してね」と登録する関数。
	// Webフレームワーク（Express.jsのapp.getなど）のルーティングと同じ概念。
	http.HandleFunc("/ws", handleWebSocket)

	// サーバー起動メッセージ
	// 【fmt.Println とは？】
	// 画面（ターミナル）にテキストを1行出力する関数。
	// Python の print()、JavaScript の console.log() に相当。
	fmt.Println("🚀 WebSocket サーバー起動: http://localhost" + port)
	fmt.Println("   WebSocket エンドポイント: ws://localhost" + port + "/ws")
	fmt.Println("   Ctrl+C で停止")

	// HTTPサーバーを起動して、接続を待ち受ける
	// 【http.ListenAndServe とは？】
	// 指定されたポートでHTTPサーバーを起動する関数。
	// この関数はブロッキング（サーバーが停止するまで戻ってこない）。
	//
	// 【log.Fatal とは？】
	// エラーメッセージを出力して、プログラムを終了する関数。
	// http.ListenAndServe がエラーを返した場合（ポートが使用中など）に実行される。
	log.Fatal(http.ListenAndServe(port, nil))
}

// =============================================================================
// handleWebSocket — WebSocket接続のハンドラー
// =============================================================================
//
// 【この関数の役割】
// ブラウザから /ws にアクセスがあった時に呼ばれます。
// HTTP接続をWebSocketにアップグレードし、読み取り・書き込みループを開始します。
//
// 【引数の説明】
// w http.ResponseWriter — レスポンスを書き込むためのオブジェクト
// r *http.Request       — リクエストの情報（URL、ヘッダーなど）
//
// 【* はポインタ】
// *http.Request の「*」はポインタ（メモリ上のアドレス）を意味します。
// 大きなデータをコピーせずに参照で渡すことで、メモリ効率が良くなります。
func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	// HTTP → WebSocket にアップグレード
	// 【Upgrade とは？】
	// HTTP接続を WebSocket接続に昇格させる処理。
	// 成功すると `conn` にWebSocket接続オブジェクトが返される。
	// 失敗すると `err` にエラー情報が入る。
	//
	// 【Go言語の多値戻り値】
	// Go では関数が複数の値を返せます。
	// conn, err := ... は「接続オブジェクト」と「エラー」の2つを受け取ります。
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		// 【エラーハンドリング】
		// Go にはtry-catchがありません。代わりに「エラーを返り値でチェック」します。
		// if err != nil { ... } が Go のエラーチェックの基本パターン。
		log.Println("WebSocket アップグレード失敗:", err)
		return
	}

	// 【defer とは？】
	// 「この関数が終わる時に必ず実行する」という予約。
	// try-finally の finally に相当。
	// WebSocket接続は使い終わったら必ず閉じる必要があるため、defer で確実にクローズ。
	defer conn.Close()

	log.Println("✅ 新しいクライアントが接続しました")

	// 【チャネル（channel）とは？】
	// Go の goroutine（並行処理）間でデータをやりとりする「パイプ」。
	// ここでは writePump を停止するための信号を送るために使います。
	//
	// make(chan struct{}) — 空の構造体のチャネルを作成
	// struct{} はメモリを消費しない型。「信号を送るだけ」の用途に最適。
	done := make(chan struct{})

	// 【goroutine（ゴルーチン）とは？】
	// 「go 関数名()」で、その関数を別スレッド（のようなもの）で並行実行する。
	// ここでは writePump を別の goroutine で動かして、
	// この関数（handleWebSocket）では readPump を実行する。
	//
	// なぜ分けるのか？
	// - readPump: クライアントからのメッセージを「待つ」（ブロッキング）
	// - writePump: 1秒ごとにデータを「送る」（タイマー駆動）
	// 両方を同時に動かすには、goroutine が必要。
	go writePump(conn, done)

	// readPump はこの goroutine で実行（ブロッキング）
	// クライアントが切断されるまでここで止まる
	readPump(conn, done)

	log.Println("❌ クライアントが切断しました")
}

// =============================================================================
// readPump — クライアントからのメッセージ受信ループ
// =============================================================================
//
// 【この関数の役割】
// WebSocket接続からメッセージを繰り返し読み取る「受信ループ」。
// クライアントが切断されるまで永久に動き続けます。
//
// 【引数】
// conn *websocket.Conn — WebSocket接続オブジェクト
// done chan struct{}    — writePumpを停止するための通知チャネル
func readPump(conn *websocket.Conn, done chan struct{}) {
	// 【defer とは？ (復習)】
	// この関数が終わる時（＝クライアント切断時）に close(done) を実行。
	// close(done) は done チャネルを閉じる。
	// writePump は done チャネルが閉じたことを検知して停止する。
	defer close(done)

	// 【for — 無限ループ】
	// Go の for { ... } は while(true) { ... } と同じ。
	// 明示的に break するか、return するまで繰り返す。
	for {
		// メッセージを読み取る
		// 【ReadMessage の戻り値】
		// messageType: メッセージの種類（テキスト or バイナリ）
		//   - websocket.TextMessage (1): テキストメッセージ
		//   - websocket.BinaryMessage (2): バイナリメッセージ
		// message: メッセージの内容（[]byte = バイトのスライス）
		// err: エラー（接続が切れた場合など）
		//
		// 【_ （アンダースコア）とは？】
		// 使わない戻り値を捨てるための特殊な変数名。
		// Go では使わない変数があるとコンパイルエラーになるため、
		// 「この値は使いません」と明示的に宣言する。
		_, message, err := conn.ReadMessage()
		if err != nil {
			// 接続が正常に閉じられた場合もここに来る
			// エラーの詳細をログに出力
			log.Println("読み取りエラー:", err)
			return // ループを抜けて関数を終了 → defer close(done) が実行される
		}

		// 受信したメッセージをログに表示
		// 【string(message) とは？】
		// []byte 型を string 型に変換。
		// メッセージはバイト列として受信されるので、文字列として表示するために変換。
		received := string(message)
		log.Println("📨 受信:", received)

		// メッセージに応じたレスポンスを作成
		response := processCommand(received)

		// レスポンスをクライアントに送信
		// 【WriteMessage の引数】
		// 第1引数: メッセージタイプ（TextMessage = テキスト）
		// 第2引数: メッセージ内容（[]byte に変換）
		err = conn.WriteMessage(websocket.TextMessage, []byte(response))
		if err != nil {
			log.Println("書き込みエラー:", err)
			return
		}
	}
}

// =============================================================================
// processCommand — 受信したコマンドに対するレスポンスを生成
// =============================================================================
//
// 【この関数の役割】
// クライアントから受信したテキストコマンドを解釈して、適切なレスポンスを返す。
// 将来的には、ここでロボットに実際のコマンドを送信する処理を行う。
//
// 【switch文とは？】
// if-else if-else の連鎖をスッキリ書ける構文。
// JavaScript や C の switch と同じだが、Go では break が不要（自動で抜ける）。
func processCommand(cmd string) string {
	switch cmd {
	case "forward":
		return "🤖 前進コマンド受信 → 速度: 0.5 m/s"
	case "backward":
		return "🤖 後退コマンド受信 → 速度: -0.5 m/s"
	case "left":
		return "🤖 左旋回コマンド受信 → 角速度: 0.3 rad/s"
	case "right":
		return "🤖 右旋回コマンド受信 → 角速度: -0.3 rad/s"
	case "stop":
		return "🤖 停止コマンド受信 → 速度: 0 m/s"
	default:
		// 上記のどれにも当てはまらない場合
		// 【fmt.Sprintf とは？】
		// 書式付き文字列を作成する関数（Printf の文字列版）。
		// %s はプレースホルダーで、引数の文字列に置き換えられる。
		return fmt.Sprintf("🤖 不明なコマンド: '%s'（forward/backward/left/right/stop が使えます）", cmd)
	}
}

// =============================================================================
// writePump — クライアントへの定期データ送信ループ
// =============================================================================
//
// 【この関数の役割】
// 1秒ごとにモック（偽の）センサーデータを作成して、クライアントに送信する。
// 実際のロボットでは、ここでセンサーから読み取ったデータを送信する。
//
// 【goroutine で実行される】
// この関数は handleWebSocket() から go writePump() で起動される。
// readPump() と並行して動作する。
//
// 【引数】
// conn *websocket.Conn — WebSocket接続
// done chan struct{}    — readPumpからの停止通知を受け取るチャネル
func writePump(conn *websocket.Conn, done chan struct{}) {
	// 【time.NewTicker とは？】
	// 指定した間隔で定期的に「チック」（信号）を発生させるタイマー。
	// ticker.C チャネルから定期的に値を受け取れる。
	// 例: sensorInterval = 1秒 → 1秒ごとに ticker.C に値が届く
	ticker := time.NewTicker(sensorInterval)

	// 【defer ticker.Stop()】
	// 関数が終わる時にタイマーを停止する。
	// リソースリーク（メモリやCPU時間の無駄遣い）を防ぐため。
	defer ticker.Stop()

	// 【select 文 — チャネルの多重待ち】
	// 複数のチャネルを同時に監視し、どれかにデータが届いたらそれを処理する。
	// ここでは2つのチャネルを監視:
	//   1. done: readPump からの停止通知（クライアントが切断された時）
	//   2. ticker.C: 定期的なタイマー通知（1秒ごと）
	//
	// 【for + select パターン】
	// Go の並行処理でよく使われる基本パターン。
	// 「何かイベントが起きるまで待って、起きたら対応する」を繰り返す。
	for {
		select {
		case <-done:
			// done チャネルが閉じられた（= readPump が終了した = クライアント切断）
			// 【<-done とは？】
			// チャネルからデータを受け取る操作。
			// close(done) されると、即座にゼロ値が返される（ブロックしない）。
			log.Println("writePump 停止（クライアント切断）")
			return

		case <-ticker.C:
			// 1秒経過 → センサーデータを送信
			data := generateMockSensorData()
			err := conn.WriteMessage(websocket.TextMessage, []byte(data))
			if err != nil {
				log.Println("送信エラー:", err)
				return
			}
		}
	}
}

// =============================================================================
// generateMockSensorData — モック（偽の）センサーデータを生成
// =============================================================================
//
// 【この関数の役割】
// 実際のロボットの代わりに、偽のセンサーデータを生成する。
// 将来的にはロボットのセンサーから実データを取得する処理に置き換える。
//
// 【%.1f とは？】
// fmt.Sprintf の書式指定子。
// %f は浮動小数点数（小数）を意味し、.1 は小数点以下1桁を表す。
// 例: 23.456 → "23.5"
func generateMockSensorData() string {
	// 温度: 20.0 〜 30.0 の範囲でランダム
	// 【rand.Float64() とは？】
	// 0.0 以上 1.0 未満のランダムな小数を返す関数。
	// 20.0 + rand.Float64()*10.0 で 20.0〜30.0 の範囲に変換。
	temperature := 20.0 + rand.Float64()*10.0

	// バッテリー残量: 50% 〜 100% の範囲でランダム
	battery := 50.0 + rand.Float64()*50.0

	// 速度: 0.0 〜 1.0 の範囲でランダム
	speed := rand.Float64()

	return fmt.Sprintf("📊 センサーデータ | 温度: %.1f°C | バッテリー: %.0f%% | 速度: %.2f m/s",
		temperature, battery, speed)
}
