/**
 * ============================================================
 * Sidebar.tsx - サイドバーナビゲーションコンポーネント
 * ============================================================
 *
 * 【ファイルの概要】
 * このファイルは、画面左側に表示されるサイドバー（ナビゲーションメニュー）を
 * 定義しています。ユーザーはここからアプリの各ページに移動できます。
 *
 * 【このコンポーネントの機能】
 * 1. ナビゲーションリンク（Dashboard、Control、Navigation など）の表示
 * 2. 折りたたみ（collapse）機能 — サイドバーを小さくできる
 * 3. ユーザーの権限（role）に基づいたメニューの表示/非表示
 * 4. 現在のページをハイライト表示
 * 5. ログアウト機能
 *
 * 【サイドバーの構造】
 * ┌──────────┐
 * │ ロゴ  [<] │  ← ヘッダー（折りたたみボタン付き）
 * ├──────────┤
 * │ Dashboard │  ← ナビゲーションリンク
 * │ Control   │
 * │ Navigation│
 * │ Sensors   │
 * │ Data      │
 * │ RAG Chat  │
 * │ Settings  │
 * ├──────────┤
 * │ ユーザー名 │  ← ユーザー情報とログアウト
 * │ [Logout]  │
 * └──────────┘
 */

// -------------------------------------------------------
// インポート部分
// -------------------------------------------------------

/**
 * 【NavLink とは？】
 * React Router が提供するナビゲーション用のリンクコンポーネントです。
 * 通常の <a> タグと違い、ページをリロードせずにURLを変更します（SPA的な遷移）。
 *
 * NavLink の特別な点：
 * - 現在のURLとリンク先が一致すると「isActive」が true になる
 * - これを使って、現在のページのリンクをハイライト表示できる
 * - 通常の <Link> コンポーネントにはこの機能がない
 */
import { NavLink } from "react-router-dom";

/**
 * 【lucide-react アイコン】
 * lucide-react は、軽量でカスタマイズしやすいアイコンライブラリです。
 * 各アイコンは React コンポーネントとしてインポートして使います。
 *
 * - LayoutDashboard → ダッシュボード（概要ページ）のアイコン
 * - Gamepad2       → ゲームパッド型のアイコン（手動制御ページ用）
 * - Navigation     → ナビゲーション（経路案内）のアイコン
 * - Activity       → 波形のアイコン（センサーデータ表示用）
 * - Database       → データベースのアイコン（データ管理用）
 * - MessageSquare  → 吹き出しのアイコン（RAGチャット用）
 * - Settings       → 歯車のアイコン（設定ページ用）
 * - LogOut         → ログアウトのアイコン
 * - Bot            → ロボットのアイコン（ロゴ表示用）
 * - ChevronLeft    → 左向き矢印のアイコン（折りたたみボタン用）
 */
import {
  LayoutDashboard,
  Gamepad2,
  Navigation,
  Activity,
  Database,
  MessageSquare,
  Settings,
  LogOut,
  Bot,
  ChevronLeft,
} from "lucide-react";

/**
 * 【useAuthStore】認証（ログイン）状態を管理するストア
 * Zustand というライブラリで作られた状態管理ストアです。
 * ユーザー情報、ログアウト関数、権限チェック関数などを提供します。
 *
 * 【ストアとは？】
 * アプリ全体で共有するデータの保管場所です。
 * どのコンポーネントからでもアクセスできます。
 */
import { useAuthStore } from "@/stores/authStore";

/**
 * 【cn ユーティリティ関数】
 * 複数のCSSクラス名を結合し、条件分岐にも対応するヘルパー関数です。
 * 内部では clsx と tailwind-merge を使っています。
 *
 * 使用例：
 *   cn("text-red", isActive && "font-bold")
 *   → isActive が true なら "text-red font-bold"
 *   → isActive が false なら "text-red"
 *
 * 【なぜ cn() が必要なのか？】
 * Tailwind CSS では、クラスの競合が発生することがあります。
 * 例：「text-red」と「text-blue」が両方指定された場合、
 * tailwind-merge が後のクラスを優先して競合を解決します。
 */
import { cn } from "@/lib/utils";

/**
 * 【useState】React の組み込みフック
 * コンポーネント内で「状態（state）」を管理するために使います。
 * 状態 = コンポーネントが「覚えておく」必要のあるデータのことです。
 * 状態が変わると、コンポーネントが自動的に再描画（再レンダリング）されます。
 */
import { useState } from "react";

// -------------------------------------------------------
// ナビゲーションアイテムの定義
// -------------------------------------------------------

/**
 * 【navItems 配列 - ナビゲーションメニューの定義】
 * サイドバーに表示するメニュー項目を配列（Array）で定義しています。
 * 各項目はオブジェクト（{ }）で、以下のプロパティを持ちます：
 *
 * - to:    リンク先のURL（パス）
 * - label: 表示されるテキスト
 * - icon:  表示されるアイコンコンポーネント
 * - role:  （オプション）このメニューを見るために必要な権限
 *
 * 【なぜ配列で定義するのか？】
 * メニュー項目を配列にすることで、.map() で一括描画できます。
 * 項目を追加・削除したいとき、この配列を変更するだけで済みます。
 * DRY原則（Don't Repeat Yourself）= 繰り返しを避ける設計パターンです。
 *
 * 【const とは？】
 * 再代入できない変数宣言です。配列の中身は変更可能ですが、
 * navItems 自体を別の値に置き換えることはできません。
 */
const navItems = [
  /** ダッシュボード — すべてのユーザーがアクセス可能（roleなし） */
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  /** 手動制御 — operator（操作者）以上の権限が必要 */
  { to: "/control", label: "Manual Control", icon: Gamepad2, role: "operator" },
  /** ナビゲーション — operator（操作者）以上の権限が必要 */
  { to: "/navigation", label: "Navigation", icon: Navigation, role: "operator" },
  /** センサー表示 — すべてのユーザーがアクセス可能 */
  { to: "/sensors", label: "Sensor View", icon: Activity },
  /** データ管理 — すべてのユーザーがアクセス可能 */
  { to: "/data", label: "Data Management", icon: Database },
  /** RAGチャット — すべてのユーザーがアクセス可能 */
  { to: "/rag", label: "RAG Chat", icon: MessageSquare },
  /** 設定 — すべてのユーザーがアクセス可能 */
  { to: "/settings", label: "Settings", icon: Settings },
];

// -------------------------------------------------------
// コンポーネント定義
// -------------------------------------------------------

/**
 * 【Sidebar コンポーネント】
 * アプリケーションの左側ナビゲーションメニューです。
 * 折りたたみ機能があり、アイコンのみの表示に切り替えられます。
 */
export function Sidebar() {
  /**
   * 【useState - 折りたたみ状態の管理】
   * useState(false) は初期値を false（展開状態）に設定します。
   *
   * 返り値は配列で、2つの要素があります：
   * - collapsed: 現在の状態値（true = 折りたたみ、false = 展開）
   * - setCollapsed: 状態を更新する関数
   *
   * 【分割代入（配列版）】
   * const [collapsed, setCollapsed] = useState(false);
   * これは配列の分割代入です。useState が返す配列の
   * 1番目を collapsed、2番目を setCollapsed という名前にしています。
   */
  const [collapsed, setCollapsed] = useState(false);

  /**
   * 【useAuthStore からの値の取得】
   * Zustand ストアから必要な値を取得しています。
   *
   * (s) => s.user は「セレクター関数」と呼ばれ、
   * ストア全体（s）からuser プロパティだけを取り出します。
   * これにより、user が変わったときだけ再レンダリングされます。
   * （ストアの他の値が変わっても再レンダリングされない → 性能最適化）
   */
  const user = useAuthStore((s) => s.user);       // 現在ログイン中のユーザー情報
  const logout = useAuthStore((s) => s.logout);    // ログアウト関数
  const hasRole = useAuthStore((s) => s.hasRole);  // 権限チェック関数

  return (
    /**
     * 【aside タグ】
     * HTML5 のセマンティックタグで、「メインコンテンツの横にある補助的な内容」
     * を示します。サイドバーナビゲーションに最適なタグです。
     * スクリーンリーダーが「これはサイドバーだ」と認識できます。
     *
     * 【cn() を使ったクラスの条件分岐】
     * cn() 関数で、collapsed の値に応じて幅を切り替えています：
     * - "flex h-full flex-col border-r bg-card transition-all duration-200"
     *   → 常に適用されるクラス
     *   → transition-all duration-200 はアニメーション設定（200ms で滑らかに変化）
     * - collapsed ? "w-16" : "w-56"
     *   → 折りたたみ時は幅16（4rem）、展開時は幅56（14rem）
     */
    <aside
      className={cn(
        "flex h-full flex-col border-r bg-card transition-all duration-200",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* ===== ヘッダー部分 ===== */}
      {/**
       * サイドバーの上部にロゴと折りたたみボタンを表示します。
       * - "h-14"        → 高さ 3.5rem（56px）
       * - "items-center" → 子要素を縦方向中央に配置
       * - "justify-between" → 子要素を左右の端に配置
       * - "border-b"    → 下に境界線を引く
       * - "px-3"        → 左右に余白 0.75rem（12px）
       */}
      <div className="flex h-14 items-center justify-between border-b px-3">
        {/**
         * 【条件付きレンダリング】
         * {!collapsed && (...)} は「collapsed が false のときだけ表示する」という意味です。
         * JavaScript の論理AND演算子（&&）を使った条件付きレンダリングのパターンです。
         * collapsed が true（折りたたみ状態）なら、ロゴとテキストは非表示になります。
         */}
        {!collapsed && (
          <div className="flex items-center gap-2">
            {/**
             * 【Bot アイコン】
             * ロボットの顔のアイコンです。
             * - "h-6 w-6" → 幅・高さ 1.5rem（24px）
             * - "text-primary" → テーマのプライマリカラーで表示
             */}
            <Bot className="h-6 w-6 text-primary" />
            <span className="font-semibold text-sm">Robot AI</span>
          </div>
        )}

        {/**
         * 【折りたたみボタン】
         * クリックすると、サイドバーの幅が切り替わります。
         *
         * onClick={() => setCollapsed((c) => !c)}
         * → setCollapsed に「現在の値を反転する関数」を渡しています。
         * → (c) => !c は「現在の値 c の反対（true↔false）」を返す関数です。
         * → これを「関数型の更新」と呼びます。前の値を基に新しい値を計算するときに使います。
         *
         * 【aria-label とは？】
         * スクリーンリーダー用のラベルです。
         * ボタンにテキスト（label）がない場合、視覚障害者のユーザーは
         * ボタンの用途がわかりません。aria-label で説明を追加します。
         * これを「アクセシビリティ（a11y）」対応と呼びます。
         */}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="rounded-md p-1.5 hover:bg-accent"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {/**
           * 【ChevronLeft アイコン + 回転アニメーション】
           * 折りたたみ時にアイコンを180度回転させます。
           * - "transition-transform" → transform（回転・拡大など）のアニメーション
           * - collapsed && "rotate-180" → 折りたたみ時に180度回転
           *   → 左矢印が右矢印に変わり、「展開できること」を視覚的に伝えます
           */}
          <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* ===== ナビゲーションリンク部分 ===== */}
      {/**
       * 【nav タグ】
       * HTML5 のセマンティックタグで、ナビゲーション用のリンク群を示します。
       * スクリーンリーダーが「これはナビゲーションだ」と認識できます。
       *
       * - "flex-1"     → 残りのスペースをすべて占める
       * - "space-y-1"  → 子要素の間に余白 0.25rem（4px）を入れる
       * - "p-2"        → 内側に余白 0.5rem（8px）
       */}
      <nav className="flex-1 space-y-1 p-2">
        {/**
         * 【配列の .filter() と .map()】
         *
         * .filter() → 条件に合う要素だけを残す配列メソッド
         *   !item.role → role が未定義（すべてのユーザーに表示）
         *   hasRole(item.role) → ユーザーがその権限を持っているか確認
         *
         * .map() → 配列の各要素を別の値に変換する配列メソッド
         *   ここでは各 navItem を NavLink コンポーネントに変換しています
         *
         * 【as "admin" | "operator" | "viewer"】
         * TypeScript の型アサーションです。item.role が string 型だが、
         * hasRole 関数は特定の文字列リテラル型を期待するため、
         * 「これは admin, operator, viewer のいずれかだよ」と伝えています。
         */}
        {navItems
          .filter((item) => !item.role || hasRole(item.role as "admin" | "operator" | "viewer"))
          .map((item) => (
            /**
             * 【NavLink コンポーネント】
             * React Router のナビゲーションリンクです。
             *
             * key={item.to} → React が各要素を識別するための一意な値。
             *   .map() で要素を生成するとき、key は必須です。
             *   React がどの要素が追加/削除/変更されたか効率的に判断できます。
             *
             * to={item.to} → リンク先のURL
             *
             * end={item.to === "/"} → "/" のときだけ「完全一致」チェック。
             *   これがないと、"/control" に移動しても "/"（Dashboard）も
             *   アクティブと判定されてしまいます（"/" は全URLに含まれるため）。
             *
             * className={({ isActive }) => ...}
             *   → NavLink は className に関数を渡せる特別な機能があります。
             *   → isActive は現在のURLとリンク先が一致するかどうかの boolean 値です。
             *   → これを使って、アクティブなリンクの色を変えています。
             */
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  // 【常に適用されるスタイル】
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  // 【条件付きスタイル - 三項演算子】
                  // condition ? valueIfTrue : valueIfFalse
                  isActive
                    ? "bg-primary/10 text-primary"  // アクティブ時：背景を薄い青、文字を青に
                    : "text-muted-foreground hover:bg-accent hover:text-foreground" // 非アクティブ時
                )
              }
            >
              {/**
               * 【動的コンポーネント】
               * <item.icon /> は変数に格納されたコンポーネントを描画する書き方です。
               * item.icon は LayoutDashboard や Gamepad2 などのコンポーネント参照です。
               *
               * - "shrink-0" → Flexbox で縮小されないようにする（アイコンのサイズを維持）
               */}
              <item.icon className="h-4 w-4 shrink-0" />
              {/**
               * 折りたたみ状態でなければラベルテキストを表示します。
               * 折りたたみ時はアイコンだけが表示されます。
               */}
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
      </nav>

      {/* ===== ユーザー情報とログアウト部分 ===== */}
      {/**
       * サイドバーの下部に、ログイン中のユーザー情報とログアウトボタンを表示します。
       * - "border-t" → 上に境界線を引いて区切る
       */}
      <div className="border-t p-2">
        {/**
         * 【二重条件チェック】
         * !collapsed && user && (...) は2つの条件を同時にチェックしています：
         * 1. 折りたたみ状態でない（テキストを表示するスペースがある）
         * 2. ユーザー情報が存在する（ログイン済み）
         * 両方 true のときだけユーザー情報を表示します。
         */}
        {!collapsed && user && (
          <div className="mb-2 px-3 text-xs text-muted-foreground">
            {/**
             * ユーザー名を少し目立つフォント（font-medium）で表示し、
             * その下にロール（role: admin/operator/viewer）を
             * capitalize（先頭大文字）で表示します。
             */}
            <p className="font-medium text-foreground">{user.username}</p>
            <p className="capitalize">{user.role}</p>
          </div>
        )}

        {/**
         * 【ログアウトボタン】
         * onClick={logout} でストアの logout 関数を直接呼び出します。
         * 認証トークンの削除やログイン画面へのリダイレクトが行われます。
         *
         * "w-full" → ボタンの幅を親要素いっぱいにする
         */}
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
