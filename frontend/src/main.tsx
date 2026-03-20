// =============================================================================
// main.tsx — アプリケーションのエントリーポイント（起動地点）
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、Reactアプリケーションが最初に実行されるファイルです。
// HTMLの <div id="root"> に React アプリ全体を埋め込む処理を行います。
//
// 【なぜこのファイルが必要？】
// Reactアプリは最終的にHTMLページ上で動きます。
// このファイルが、ReactのコンポーネントツリーをHTMLのDOM要素に接続（マウント）します。
// いわば「Reactの世界」と「ブラウザの世界」をつなぐ橋渡し役です。
//
// 【処理の流れ】
// 1. index.html の <div id="root"> を取得
// 2. その中にReactコンポーネント（App）を描画
// 3. 各プロバイダー（Provider）が子コンポーネントに機能を提供
//
// 【.tsx ファイルとは？】
// TypeScript + JSX の略。
// JSX = JavaScript内にHTMLのようなタグ（<App />など）を書ける構文
// TypeScript = JavaScriptに型（string, numberなど）を追加した言語
// =============================================================================

// ---------------------------------------------------------------------------
// 【インポート】
// ---------------------------------------------------------------------------

// React: Reactライブラリ本体
// React.StrictMode で使うためにインポート
import React from "react";

// ReactDOM: ReactをブラウザのDOMに描画するためのライブラリ
// createRoot: React 18 で導入された新しいレンダリングAPI
// （旧: ReactDOM.render() → 新: ReactDOM.createRoot().render()）
import ReactDOM from "react-dom/client";

// BrowserRouter: React Routerのルーター（ページ遷移管理）
// ブラウザのURL（/login, /dashboard など）に基づいてページを切り替える
// SPAでのページ遷移を実現する
//
// 【SPA（Single Page Application）とは？】
// ページ全体をリロードせず、必要な部分だけを切り替えて表示するWebアプリ
// React Routerが URLの変更を監視し、対応するコンポーネントを表示する
import { BrowserRouter } from "react-router-dom";

// QueryClient, QueryClientProvider: TanStack Query（旧React Query）
// サーバーデータの取得・キャッシュ・更新を効率的に管理するライブラリ
//
// 【TanStack Queryの役割（初心者向け）】
// - API呼び出しの結果を自動的にキャッシュ（一時保存）
// - ローディング状態やエラー状態を自動管理
// - データの自動再取得（バックグラウンドでの更新）
// - 重複リクエストの自動排除
//
// 【QueryClient vs useAuthStore の違い】
// - useAuthStore（Zustand）: クライアント側の状態（ログイン情報など）
// - QueryClient（TanStack Query）: サーバー側のデータ（API取得結果）
// この2つを使い分けるのがモダンReactの一般的なパターン
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Toaster: トースト通知（画面の隅に表示される短いメッセージ）のコンポーネント
// 例: 「ログイン成功！」「エラーが発生しました」を画面右上に一時表示
//
// 【react-hot-toastの使い方】
// 1. ここで <Toaster /> を配置（表示場所の設定）
// 2. 各コンポーネントで toast.success("成功！") のように呼び出す
import { Toaster } from "react-hot-toast";

// App: アプリケーションのメインコンポーネント（ルーティングを定義）
// ./App は同じディレクトリの App.tsx を指す
import App from "./App";

// index.css: アプリ全体に適用されるグローバルCSSスタイル
// Tailwind CSSのベーススタイルなどが含まれている
import "./index.css";

// ---------------------------------------------------------------------------
// 【QueryClientの設定】
// ---------------------------------------------------------------------------
// QueryClient: TanStack Queryの中核。キャッシュやデフォルト設定を管理する。
// アプリ全体で1つだけ作成し、QueryClientProvider を通じて全コンポーネントに共有する
//
// 【new とは？】
// クラスの新しいインスタンス（実体）を作成するキーワード
// QueryClient という設計図から、実際に使えるオブジェクトを生成している
const queryClient = new QueryClient({
  // defaultOptions: すべてのクエリ（データ取得）に適用されるデフォルト設定
  defaultOptions: {
    queries: {
      // retry: 1 — API呼び出しが失敗した場合、1回だけ再試行する
      // デフォルトは3回だが、ロボット制御では早くエラーを検知したいので1回に
      retry: 1,

      // refetchOnWindowFocus: false — ブラウザのタブを切り替えて戻ったとき、
      // 自動的にデータを再取得しない
      // デフォルトはtrue（切り替え時に再取得）だが、
      // ロボット操作中に不要な再取得が起きると混乱するのでオフに
      refetchOnWindowFocus: false,

      // staleTime: 5000 — データが「古い」と見なされるまでの時間（ミリ秒）
      // 5000ms = 5秒間はキャッシュされたデータを「新鮮」として扱う
      // この間は同じデータを再取得せず、キャッシュから返す
      // → 不要なAPIリクエストを減らしてパフォーマンスを向上
      staleTime: 5000,
    },
  },
});

// ---------------------------------------------------------------------------
// 【アプリケーションのレンダリング（描画）】
// ---------------------------------------------------------------------------
//
// 【この処理の説明】
// 1. document.getElementById("root") → HTMLの <div id="root"> 要素を取得
// 2. ReactDOM.createRoot() → その要素にReactのルート（根）を作成
// 3. .render() → Reactコンポーネントツリーを描画開始
//
// 【! （Non-null assertion）とは？】
// document.getElementById("root")! の「!」は
// 「この値は絶対にnullではない」とTypeScriptに伝える記号
// getElementById は要素が見つからないとnullを返すが、
// index.html に <div id="root"> は必ず存在するので、! で安全を宣言
//
// 【コンポーネントのネスト構造（外側 → 内側）】
// React.StrictMode     → 開発中の問題を早期発見
//   QueryClientProvider → TanStack Queryの機能を全体に提供
//     BrowserRouter     → ルーティング（URL管理）を全体に提供
//       App             → アプリ本体（ルート定義）
//       Toaster         → トースト通知の表示領域
//
// 【Providerパターンとは？（初心者向け）】
// <XxxProvider> で囲まれた子コンポーネントは、Xxxの機能を使えるようになる
// これをReactの「Context」または「Providerパターン」と呼ぶ
// 例: <QueryClientProvider> の中のコンポーネントは useQuery() が使える
ReactDOM.createRoot(document.getElementById("root")!).render(
  // ---------------------------------------------------------------------------
  // 【React.StrictMode】開発モード専用のチェック機能
  // ---------------------------------------------------------------------------
  // 本番ビルドでは自動的に無効化される（パフォーマンスに影響しない）
  // 開発中に以下をチェック:
  // - 安全でないライフサイクルメソッドの使用
  // - コンポーネントが2回レンダリングされる（副作用の検出）
  // - 非推奨APIの使用
  <React.StrictMode>
    {/* QueryClientProvider: TanStack Queryの機能を全コンポーネントに提供 */}
    {/* client={queryClient} で上で作成した設定済みインスタンスを渡す */}
    <QueryClientProvider client={queryClient}>
      {/* BrowserRouter: URLベースのルーティングを有効化 */}
      {/* この中の <Route> コンポーネントがURLに応じてページを切り替える */}
      <BrowserRouter>
        {/* App: アプリケーションのメインコンポーネント */}
        {/* ここにルート定義（どのURLでどのページを表示するか）が含まれる */}
        <App />

        {/* Toaster: トースト通知を画面右上に表示するエリア */}
        {/* position="top-right" で画面右上に表示される */}
        {/* 各コンポーネントから toast.success() / toast.error() で表示 */}
        <Toaster position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
