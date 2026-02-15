// =============================================================================
// App.tsx — アプリケーションのルーティング定義（ページ構成の設計図）
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、アプリケーションのページ構成（どのURLでどのページを表示するか）
// を定義するメインコンポーネントです。
//
// 【ルーティングとは？（初心者向け）】
// ルーティング = URLに基づいてページを切り替える仕組み
// 例:
//   /login      → ログインページを表示
//   /control    → 手動操作ページを表示
//   /sensors    → センサー表示ページを表示
//
// 従来のWebサイトではページ遷移ごとにサーバーにリクエストしていたが、
// SPA（Single Page Application）では JavaScript でページ内容を切り替える。
// React Router がこの切り替えを担当する。
//
// 【このファイルの構造】
// 1. ProtectedRoute（認証ガード）: ログイン必須ページの保護
// 2. App コンポーネント: 全ルート（URL → ページ）の定義
//
// 【ルート構成の一覧】
// 認証不要:
//   /login   → LoginPage
//   /signup  → SignupPage
//
// 認証必要（AppLayout内に表示）:
//   /            → DashboardPage（トップページ）
//   /control     → ManualControlPage（ロボット手動操作）
//   /navigation  → NavigationPage（自律ナビゲーション）
//   /sensors     → SensorViewPage（センサー表示）
//   /data        → DataManagementPage（データ管理）
//   /rag         → RAGChatPage（AIチャット）
//   /settings    → SettingsPage（設定）
//   *（それ以外）→ / にリダイレクト
// =============================================================================

// ---------------------------------------------------------------------------
// 【インポート】
// ---------------------------------------------------------------------------

// Routes: 複数の Route を囲むコンテナ。URLとの一致を管理する
// Route: 1つのURL ↔ ページの対応を定義するコンポーネント
// Navigate: 別のURLにリダイレクト（転送）するコンポーネント
import { Routes, Route, Navigate } from "react-router-dom";

// AppLayout: アプリ全体の共通レイアウト（サイドバー、ヘッダーなど）
// ログイン後のページは全てこのレイアウト内に表示される
// 【@/ とは？】
// TypeScriptのパスエイリアス — src/ ディレクトリを指す省略記法
// @/components/layout/AppLayout = src/components/layout/AppLayout
// → 深いフォルダからでも ../../.. のような相対パスが不要になる
import { AppLayout } from "@/components/layout/AppLayout";

// --- 各ページコンポーネント（画面ごとに1つのコンポーネント） ---

// LoginPage: ログインページ（ユーザー名とパスワードの入力フォーム）
import { LoginPage } from "@/pages/LoginPage";

// SignupPage: 新規ユーザー登録ページ
import { SignupPage } from "@/pages/SignupPage";

// DashboardPage: ダッシュボード（ログイン後の最初のページ）
// ロボットの概要やステータスを一覧表示する
import { DashboardPage } from "@/pages/DashboardPage";

// ManualControlPage: ロボットの手動操作ページ
// ジョイスティックやキーボードでロボットを直接操作する
import { ManualControlPage } from "@/pages/ManualControlPage";

// NavigationPage: ロボットの自律ナビゲーション（自動走行）ページ
// 目的地を設定して自動的にロボットを移動させる
import { NavigationPage } from "@/pages/NavigationPage";

// SensorViewPage: センサーデータの表示ページ
// LiDAR、カメラ、IMUなどのセンサーデータをリアルタイム表示する
import { SensorViewPage } from "@/pages/SensorViewPage";

// DataManagementPage: データ管理ページ
// データセットの作成、編集、エクスポートなどを行う
import { DataManagementPage } from "@/pages/DataManagementPage";

// RAGChatPage: RAGチャットページ
// ドキュメントを元にAIと会話できるページ
import { RAGChatPage } from "@/pages/RAGChatPage";

// SettingsPage: 設定ページ
// ユーザー設定、ロボット設定などを管理する
import { SettingsPage } from "@/pages/SettingsPage";

// useAuthStore: 認証ストア（ログイン状態を管理）
// ProtectedRoute で「ログインしているか？」を確認するために使用
import { useAuthStore } from "@/stores/authStore";

// ---------------------------------------------------------------------------
// 【ProtectedRoute コンポーネント】— 認証ガード（ログイン必須ページの保護）
// ---------------------------------------------------------------------------
//
// 【このコンポーネントの目的】
// ログインしていないユーザーが、ダッシュボードなどの保護されたページに
// アクセスするのを防ぐ。未ログインユーザーはログインページに転送される。
//
// 【使い方のイメージ】
// <ProtectedRoute>
//   <秘密のページ />
// </ProtectedRoute>
// → ログイン済み: <秘密のページ /> が表示される
// → 未ログイン: /login に転送される
//
// 【引数（props）の説明】
// { children }: React.ReactNode
// - children: このコンポーネントの開始タグと終了タグの間に書かれた要素
// - React.ReactNode: Reactで描画できるもの全て（コンポーネント、文字列、数値等）
// - 分割代入（デストラクチャリング）でpropsから children だけを取り出している
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // useAuthStore のセレクター関数: ストアから accessToken だけを取得
  // (s) => s.accessToken は、ストアの状態 s から accessToken プロパティを取り出す
  //
  // 【なぜセレクター関数を使うのか？】
  // const store = useAuthStore() で全状態を取得することもできるが、
  // (s) => s.accessToken のように必要な値だけを選ぶ（セレクト）ことで、
  // 他の値が変わったときに不要な再レンダリングが発生するのを防げる
  // → パフォーマンスの最適化
  const accessToken = useAuthStore((s) => s.accessToken);

  // accessToken がない（未ログイン）場合: /login にリダイレクト
  // replace: ブラウザの履歴を置換（戻るボタンで保護ページに戻れないようにする）
  if (!accessToken) return <Navigate to="/login" replace />;

  // accessToken がある（ログイン済み）場合: 子コンポーネントを表示
  // <> と </> は「フラグメント」— 余分なDOM要素を追加せずに要素をグルーピング
  return <>{children}</>;
}

// ---------------------------------------------------------------------------
// 【App コンポーネント】— アプリケーションのルート定義
// ---------------------------------------------------------------------------
//
// 【export default とは？】
// このファイルの「メインの export」として指定する
// インポート側は import App from "./App" のように中括弧なしで受け取れる
// （一方、export const は import { 名前 } from ... のように中括弧が必要）
//
// 【ネストされたルート構造（入れ子ルート）とは？】
// <Route element={<AppLayout />}>       ← 親ルート（レイアウト）
//   <Route index element={<Page />} />  ← 子ルート（ページ内容）
// </Route>
//
// AppLayout はサイドバーやヘッダーを含む共通レイアウト
// その中に <Outlet /> という「子ルートの表示場所」がある
// 子ルートのコンポーネントが <Outlet /> の位置に表示される
export default function App() {
  return (
    // Routes: すべてのRoute定義を囲むコンテナ
    // 現在のURLに一致するRouteだけが描画される
    <Routes>
      {/* ────────────────────────────────────────────────────────── */}
      {/* 認証不要のルート（ログイン前でもアクセス可能） */}
      {/* ────────────────────────────────────────────────────────── */}

      {/* ログインページ: /login */}
      {/* path: URLパス, element: 表示するコンポーネント */}
      <Route path="/login" element={<LoginPage />} />

      {/* サインアップ（新規登録）ページ: /signup */}
      <Route path="/signup" element={<SignupPage />} />

      {/* ────────────────────────────────────────────────────────── */}
      {/* 認証必要のルート（ログイン済みユーザーのみアクセス可能） */}
      {/* ────────────────────────────────────────────────────────── */}

      {/* 親ルート: ProtectedRoute + AppLayout */}
      {/* この Route には path がない = すべての子ルートのURLに適用される */}
      {/* element に ProtectedRoute と AppLayout の両方を設定: */}
      {/*   1. ProtectedRoute → ログイン済みかチェック */}
      {/*   2. AppLayout → 共通レイアウト（サイドバー等）を適用 */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {/* ───── 子ルート（AppLayoutの <Outlet /> 内に表示される） ───── */}

        {/* index: ルート（/）にマッチする特別な子ルート */}
        {/* ユーザーがアプリのトップ（/）にアクセスするとダッシュボードを表示 */}
        <Route index element={<DashboardPage />} />

        {/* ロボット手動操作: /control */}
        <Route path="control" element={<ManualControlPage />} />

        {/* 自律ナビゲーション: /navigation */}
        <Route path="navigation" element={<NavigationPage />} />

        {/* センサーデータ表示: /sensors */}
        <Route path="sensors" element={<SensorViewPage />} />

        {/* データ管理: /data */}
        <Route path="data" element={<DataManagementPage />} />

        {/* RAGチャット: /rag */}
        <Route path="rag" element={<RAGChatPage />} />

        {/* 設定: /settings */}
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* ────────────────────────────────────────────────────────── */}
      {/* キャッチオール（どのルートにも一致しないURL） */}
      {/* ────────────────────────────────────────────────────────── */}
      {/* path="*" は「上のどのパスにも一致しなかったすべてのURL」にマッチ */}
      {/* 存在しないページにアクセスした場合、トップ（/）にリダイレクト */}
      {/* replace: ブラウザ履歴を置換（不正なURLが履歴に残らないように） */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
