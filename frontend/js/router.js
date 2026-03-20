// =============================================================================
// Step 6: ハッシュルーター — SPA 風ページ切り替え
// =============================================================================
//
// 【SPA (Single Page Application) とは？】
// ブラウザで1つの HTML ファイルを読み込み、
// JavaScript でページ全体を描き替えることで、
// ページ遷移（画面切り替え）を実現するアーキテクチャ。
//
// 従来のウェブサイト:
//   /robots → robots.html を取得
//   /control → control.html を取得
//   → ページ移動のたびにサーバーから新しい HTML を取得（全画面リロード）
//
// SPA:
//   初回: index.html を1回読み込み
//   以降: JavaScript で DOM を書き換えてページ切り替え
//   → 高速、スムーズなユーザー体験
//
// 【ハッシュルーティングとは？】
// URL のハッシュ（#）部分を使ってページを識別する方式。
//   http://localhost:3000/#/               → ダッシュボード
//   http://localhost:3000/#/robots         → ロボット一覧
//   http://localhost:3000/#/robots/new     → ロボット登録
//   http://localhost:3000/#/control        → リアルタイム制御（Step 5 の画面）
//
// 【ハッシュの特徴】
// ブラウザは # 以降をサーバーに送信しない。
// つまりサーバーは常に index.html を返し、
// クライアント（JavaScript）が # を解釈してページを切り替える。
//
// 【なぜ Step 9 の React Router ではなくハッシュルーター？】
// React Router はライブラリ依存。Step 6-8 は Vanilla JS なので、
// 自前でルーティングを実装して、ルーティングの仕組みを理解する。
//
// =============================================================================

// =============================================================================
// Router クラス
// =============================================================================

export class Router {
  // ---------------------------------------------------------------------------
  // 【routes: Map<string, Function>】
  // URL パスと、そのページを描画する関数の対応表。
  // routes.set("/robots", renderRobotListPage)
  // routes.set("/control", renderControlPage)
  // ---------------------------------------------------------------------------
  #routes = new Map();
  #container = null;
  #notFoundHandler = null;

  /**
   * @param {string} containerId - ページを描画する先の DOM 要素 ID
   */
  constructor(containerId) {
    this.#container = document.getElementById(containerId);

    // --- hashchange イベントの購読 ---
    // ユーザーが URL のハッシュを変更（リンククリック、ブラウザ戻る）するたびに発火。
    // .bind(this) で this を Router インスタンスに固定する。
    //
    // 【.bind(this) が必要な理由】
    // addEventListener のコールバック内では this がグローバル (window) になる。
    // .bind(this) で Router インスタンスに固定しないと、
    // this.#routes にアクセスできなくなる。
    window.addEventListener("hashchange", this.#onHashChange.bind(this));
  }

  // ---------------------------------------------------------------------------
  // addRoute — ルートの登録
  // ---------------------------------------------------------------------------
  //
  // path: "/robots", "/control" などのパス（# は含めない）
  // handler: そのパスにマッチしたときに呼ばれる関数
  //   handler(container) の形式で、container に HTML を描画する
  //
  addRoute(path, handler) {
    this.#routes.set(path, handler);
    return this; // メソッドチェーン: router.addRoute(...).addRoute(...)
  }

  // ---------------------------------------------------------------------------
  // setNotFound — 404 ページのハンドラー
  // ---------------------------------------------------------------------------
  setNotFound(handler) {
    this.#notFoundHandler = handler;
    return this;
  }

  // ---------------------------------------------------------------------------
  // start — ルーターの起動（初期ページの描画）
  // ---------------------------------------------------------------------------
  start() {
    this.#onHashChange();
  }

  // ---------------------------------------------------------------------------
  // navigate — プログラム的にページ遷移
  // ---------------------------------------------------------------------------
  //
  // 【history の変更】
  // window.location.hash を変更すると、hashchange イベントが発火し、
  // #onHashChange が呼ばれてページが切り替わる。
  //
  navigate(path) {
    window.location.hash = `#${path}`;
  }

  // ---------------------------------------------------------------------------
  // #onHashChange — ハッシュ変更時の処理（プライベート）
  // ---------------------------------------------------------------------------
  //
  // 【パスの解析】
  // window.location.hash は "#/robots" のような文字列。
  // "#" を除いてパスを取得し、ルートテーブルから対応するハンドラーを検索する。
  //
  // 【パスパラメータ】
  // "/robots/edit/abc-123" のように動的パスも扱う。
  // 完全一致 → 前方一致 の順にマッチを試みる。
  //
  #onHashChange() {
    // "#/robots" → "/robots"
    const hash = window.location.hash.slice(1) || "/";
    const path = hash.startsWith("/") ? hash : `/${hash}`;

    // 完全一致を試みる
    if (this.#routes.has(path)) {
      this.#routes.get(path)(this.#container, {});
      this.#updateNav(path);
      return;
    }

    // パスパラメータ付きのマッチを試みる
    // 例: 登録済み "/robots/edit" と現在の "/robots/edit/abc-123"
    for (const [routePath, handler] of this.#routes) {
      if (path.startsWith(routePath + "/")) {
        const param = path.slice(routePath.length + 1);
        handler(this.#container, { param });
        this.#updateNav(routePath);
        return;
      }
    }

    // 404: どのルートにもマッチしない場合
    if (this.#notFoundHandler) {
      this.#notFoundHandler(this.#container, { path });
    }
  }

  // ---------------------------------------------------------------------------
  // #updateNav — ナビゲーションの active 状態を更新
  // ---------------------------------------------------------------------------
  #updateNav(currentPath) {
    document.querySelectorAll("[data-route]").forEach((el) => {
      const route = el.getAttribute("data-route");
      el.classList.toggle("active", currentPath.startsWith(route));
    });
  }
}
