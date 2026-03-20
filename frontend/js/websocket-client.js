// =============================================================================
// Step 4: WebSocket クライアントクラス
// =============================================================================
//
// 【Step 3 からの変更点】
// Step 3: app.js 内でグローバル変数 `ws` を直接管理
// Step 4: WebSocketClient クラスとしてカプセル化
//
// 【クラス（class）とは？】
// 関連するデータ（state）と操作（methods）をまとめた設計図。
// ES2015 (ES6) から JavaScript にもクラス構文が導入された。
//
// Go との比較:
//   Go:   type WebSocketClient struct { ... }  + メソッドレシーバー
//   JS:   class WebSocketClient { constructor() { ... } methods... }
//
// 【カプセル化（Encapsulation）のメリット】
// WebSocket の接続状態、再接続ロジック、カウンターなどを
// 1つのオブジェクトにまとめることで:
//   1. グローバル変数を減らせる
//   2. 複数のWebSocket接続を作ることも可能
//   3. テストしやすい
//
// =============================================================================

export class WebSocketClient {
  // ---------------------------------------------------------------------------
  // 【# プライベートフィールド】
  // # で始まるフィールドはクラスの外からアクセスできない。
  // Go の小文字フィールド（unexported）に相当。
  // ---------------------------------------------------------------------------
  #ws = null;
  #url;
  #sentCount = 0;
  #receivedCount = 0;
  #onMessage = null;
  #onStateChange = null;

  // ---------------------------------------------------------------------------
  // constructor — コンストラクタ（Go の New 関数に相当）
  // ---------------------------------------------------------------------------
  //
  // 【コールバック関数パターン】
  // onMessage や onStateChange は、イベント発生時に呼ばれる関数。
  // このパターンにより、WebSocketClient はUI操作を知らなくてよい。
  // 通信の責任だけを持ち、UIの更新は呼び出し側に任せる。
  //
  // options オブジェクト:
  //   { onMessage: fn, onStateChange: fn }
  constructor(url, options = {}) {
    this.#url = url;
    this.#onMessage = options.onMessage || null;
    this.#onStateChange = options.onStateChange || null;
  }

  // ---------------------------------------------------------------------------
  // connect — WebSocket 接続を確立
  // ---------------------------------------------------------------------------
  connect() {
    if (this.#ws && this.#ws.readyState === WebSocket.OPEN) {
      return; // 既に接続済み
    }

    this.#ws = new WebSocket(this.#url);

    this.#ws.onopen = () => {
      this.#notifyStateChange("connected");
    };

    this.#ws.onmessage = (event) => {
      this.#receivedCount++;
      if (this.#onMessage) {
        this.#onMessage(event.data);
      }
    };

    this.#ws.onclose = (event) => {
      this.#notifyStateChange("disconnected", event.code);
      this.#ws = null;
    };

    this.#ws.onerror = () => {
      this.#notifyStateChange("error");
    };
  }

  // ---------------------------------------------------------------------------
  // disconnect — 切断
  // ---------------------------------------------------------------------------
  disconnect() {
    if (this.#ws) {
      this.#ws.close(1000, "ユーザーが切断");
    }
  }

  // ---------------------------------------------------------------------------
  // send — メッセージ送信
  // ---------------------------------------------------------------------------
  send(data) {
    if (!this.#ws || this.#ws.readyState !== WebSocket.OPEN) return false;
    this.#ws.send(data);
    this.#sentCount++;
    return true;
  }

  // ---------------------------------------------------------------------------
  // ゲッター（getter）
  // ---------------------------------------------------------------------------
  //
  // 【getter とは？】
  // プロパティのようにアクセスできるメソッド。
  //   client.isConnected  → client.isConnected() ではなく () なしで呼べる
  // Go にはこの構文がない（メソッド呼び出しは常に () が必要）。
  get isConnected() {
    return this.#ws && this.#ws.readyState === WebSocket.OPEN;
  }

  get sentCount() {
    return this.#sentCount;
  }

  get receivedCount() {
    return this.#receivedCount;
  }

  // ---------------------------------------------------------------------------
  // プライベートメソッド
  // ---------------------------------------------------------------------------
  #notifyStateChange(state, detail = null) {
    if (this.#onStateChange) {
      this.#onStateChange(state, detail);
    }
  }
}
