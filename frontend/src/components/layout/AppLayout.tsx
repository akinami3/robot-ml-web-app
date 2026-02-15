/**
 * ============================================================
 * AppLayout.tsx - アプリケーション全体のレイアウトコンポーネント
 * ============================================================
 *
 * 【ファイルの概要】
 * このファイルは、アプリケーション全体の「骨格（レイアウト）」を定義します。
 * ウェブアプリを開いたとき、左側にサイドバー、右側にメインコンテンツが
 * 表示される構造を作っています。
 *
 * 【レイアウトコンポーネントとは？】
 * レイアウトコンポーネントは、ページ共通の見た目（ヘッダー、サイドバー、
 * フッターなど）を一箇所にまとめるためのコンポーネントです。
 * 各ページはこのレイアウトの「中身」として表示されます。
 *
 * 【このファイルの構造】
 * ┌──────────────────────────────────────┐
 * │ ┌────────┐ ┌─────────────────────┐   │
 * │ │        │ │ StatusBar           │   │
 * │ │Sidebar │ ├─────────────────────┤   │
 * │ │        │ │                     │   │
 * │ │        │ │ <Outlet /> ← ページ │   │
 * │ │        │ │                     │   │
 * │ └────────┘ └─────────────────────┘   │
 * └──────────────────────────────────────┘
 */

// -------------------------------------------------------
// インポート部分
// -------------------------------------------------------

/**
 * 【Outlet とは？】
 * React Router の特別なコンポーネントです。
 * 「ここにページの中身を表示してね」という目印（プレースホルダー）です。
 *
 * 例：URLが "/control" のとき → ManualControlPage が <Outlet /> の位置に表示される
 * 例：URLが "/sensors" のとき → SensorViewPage が <Outlet /> の位置に表示される
 *
 * つまり、レイアウト（サイドバーやステータスバー）はそのままで、
 * 中身だけが切り替わる仕組みです。これを「ネストされたルーティング」と呼びます。
 */
import { Outlet } from "react-router-dom";

/**
 * 【Sidebar】左側のナビゲーションメニューコンポーネント
 * 同じ layout フォルダにある Sidebar.tsx からインポートしています。
 * "./" は「同じフォルダ」を意味します。
 */
import { Sidebar } from "./Sidebar";

/**
 * 【StatusBar】上部のステータスバーコンポーネント
 * ロボットの接続状態やバッテリー残量を表示します。
 * "@/" は src フォルダのルートを指すエイリアス（ショートカット）です。
 * これにより "../../components/robot/StatusBar" のような長いパスを避けられます。
 */
import { StatusBar } from "@/components/robot/StatusBar";

/**
 * 【useWebSocket】WebSocket接続を管理するカスタムフック
 * WebSocket = サーバーとリアルタイムで双方向通信する技術です。
 * ロボットの状態をリアルタイムで受信するために使います。
 *
 * カスタムフック = "use" で始まる自作の関数で、
 * 状態管理やロジックを再利用可能な形にまとめたものです。
 */
import { useWebSocket } from "@/hooks/useWebSocket";

// -------------------------------------------------------
// コンポーネント定義
// -------------------------------------------------------

/**
 * 【AppLayout コンポーネント】
 * アプリケーション全体のレイアウトを定義する関数コンポーネントです。
 *
 * 【関数コンポーネントとは？】
 * React では、UIの部品を「コンポーネント」として定義します。
 * 関数コンポーネントは、JSX（HTMLに似た記法）を返す関数です。
 * 関数名は大文字で始めるルールがあります（PascalCase）。
 *
 * 【export とは？】
 * この関数を他のファイルからインポートできるようにする宣言です。
 * ルーター設定ファイルでこのコンポーネントを使うために必要です。
 */
export function AppLayout() {
  /**
   * 【useWebSocket フックの使用】
   * useWebSocket() を呼び出すと、WebSocket接続に関する情報が返されます。
   *
   * 【分割代入（Destructuring）】
   * const { isConnected, reconnectCount } = useWebSocket();
   * これは「分割代入」という書き方で、オブジェクトから必要なプロパティだけを
   * 取り出して変数にしています。以下と同じ意味です：
   *   const result = useWebSocket();
   *   const isConnected = result.isConnected;
   *   const reconnectCount = result.reconnectCount;
   *
   * - isConnected: サーバーに接続されているか（true/false）
   * - reconnectCount: 再接続を試みた回数（0なら一度も切断されていない）
   */
  const { isConnected, reconnectCount } = useWebSocket();

  /**
   * 【JSX の return 文】
   * コンポーネントが画面に表示する内容を返します。
   * JSX は HTML に似ていますが、JavaScript の中で使えるように拡張された記法です。
   */
  return (
    /**
     * 【最外側の div - 画面全体のコンテナ】
     *
     * className に Tailwind CSS のクラスを指定しています。
     * 【Tailwind CSS とは？】
     * クラス名を組み合わせてスタイルを適用するCSSフレームワークです。
     * 従来のCSSファイルを書く代わりに、クラス名だけでデザインできます。
     *
     * 各クラスの意味：
     * - "flex"            → Flexbox レイアウトを使用（子要素を横並びにする）
     * - "h-screen"        → 高さを画面いっぱい（100vh）にする
     * - "w-screen"        → 幅を画面いっぱい（100vw）にする
     * - "overflow-hidden" → はみ出した内容を隠す（スクロールバーを防ぐ）
     * - "bg-background"   → 背景色をテーマの背景色にする
     * - "text-foreground" → 文字色をテーマの前景色にする
     *
     * 【なぜ flex を使うのか？】
     * Sidebar（左）と メインコンテンツ（右）を横に並べるためです。
     * flex は CSS の強力なレイアウト手法で、要素の配置を柔軟に制御できます。
     */
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/**
       * 【Sidebar コンポーネント】
       * 左側のナビゲーションメニューを表示します。
       * コンポーネントは HTML タグのように <Sidebar /> と書いて使います。
       * "/" は「自己閉じタグ」で、中身（children）がないことを示します。
       */}
      <Sidebar />

      {/**
       * 【右側のコンテナ】
       * StatusBar とメインコンテンツを縦に並べるための div です。
       *
       * - "flex"            → Flexbox を使用
       * - "flex-1"          → 残りのスペースをすべて占める（Sidebarの横幅を引いた分）
       * - "flex-col"        → 子要素を縦方向に並べる（デフォルトは横方向）
       * - "overflow-hidden" → はみ出した内容を隠す
       */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/**
         * 【StatusBar コンポーネント】
         * 接続状態やロボット情報を表示するバーです。
         *
         * 【Props（プロパティ）とは？】
         * コンポーネントに渡すデータのことです。HTMLの属性に似ています。
         * ここでは isConnected と reconnectCount を StatusBar に渡しています。
         * StatusBar はこの値を使って表示内容を変えます。
         */}
        <StatusBar isConnected={isConnected} reconnectCount={reconnectCount} />

        {/**
         * 【main タグ - メインコンテンツエリア】
         * HTML5 の <main> タグは「ページの主要な内容」を示すセマンティックタグです。
         * スクリーンリーダー（視覚障害者向けの読み上げソフト）が
         * メインコンテンツを認識しやすくなります。
         *
         * - "flex-1"        → 残りの縦スペースをすべて占める
         * - "overflow-auto" → 内容がはみ出したらスクロールバーを表示
         * - "p-6"           → 内側に余白（padding）を 1.5rem（24px）設定
         */}
        <main className="flex-1 overflow-auto p-6">
          {/**
           * 【Outlet コンポーネント - ページの表示場所】
           * React Router の <Outlet /> は、現在のURLに対応するページコンポーネントを
           * ここに表示します。
           *
           * 例えば：
           *   URL が "/"        → DashboardPage がここに表示される
           *   URL が "/control" → ManualControlPage がここに表示される
           *   URL が "/sensors" → SensorViewPage がここに表示される
           *
           * レイアウト（Sidebar、StatusBar）は変わらず、
           * この <Outlet /> の中身だけが切り替わります。
           * これがSPA（Single Page Application）の動作原理です。
           */}
          <Outlet />
        </main>
      </div>
    </div>
  );
}
