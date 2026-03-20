# Step 9: React + TypeScript 移行 ⚛️

> **ブランチ**: `step/09-react-migration`
> **前のステップ**: `step/08-authentication`
> **次のステップ**: `step/10-realtime-dashboard`

---

## このステップで学ぶこと

1. **React の基礎** — JSX、コンポーネント、仮想 DOM
2. **TypeScript** — 型安全な JavaScript 開発
3. **Vite** — 高速な開発サーバーとビルドツール
4. **React Router v6** — クライアントサイドルーティング
5. **Zustand** — 軽量な状態管理ライブラリ
6. **Tailwind CSS** — ユーティリティファーストの CSS フレームワーク

---

## 概要

Step 1〜8 で作ってきた Vanilla JS / CSS フロントエンドを
**React 18 + TypeScript + Vite** で全面的に書き直すステップ。
16 個の Vanilla JS ファイルを削除し、React コンポーネントベースの
モダンなフロントエンドアーキテクチャに移行する。

---

## 学習ポイント

### Vanilla JS → React の対応表

| Vanilla JS | React |
|---|---|
| `document.getElementById()` | `useRef()` |
| `addEventListener('click', ...)` | `onClick={...}` |
| `element.innerHTML = ...` | JSX による宣言的 UI |
| グローバル変数 | `useState()` / Zustand ストア |
| `fetch()` 直接呼び出し | TanStack Query / Axios |
| URL ハッシュルーティング | React Router v6 |
| `<style>` / CSS ファイル | Tailwind CSS クラス |
| DOM 直接操作 | 仮想 DOM による差分更新 |

### React の主要コンセプト
- **コンポーネント**: UI を再利用可能な部品に分割
- **JSX**: HTML ライクな構文で UI を記述
- **Hooks**: `useState`, `useEffect`, `useCallback`, `useRef`
- **宣言的 UI**: 「この状態ならこの見た目」を記述（手続き的に DOM を操作しない）

### 状態管理
- **Zustand**: グローバルな認証状態（`authStore`）、ロボット状態（`robotStore`）
- **TanStack Query**: サーバーデータの取得・キャッシュ・再取得を自動管理
- **useState**: コンポーネントローカルの状態

### 開発ツール
- **Vite**: HMR（Hot Module Replacement）で保存即反映
- **TypeScript**: 型エラーをビルド時に検出
- **ESLint / Prettier**: コード品質の自動チェック

---

## ファイル構成

```
frontend/                        ← 全面書き換え
  src/
    main.tsx                     ← エントリーポイント（Provider 構成）
    App.tsx                      ← React Router ルーティング
    index.css                    ← Tailwind CSS インポート
    components/
      layout/
        AppLayout.tsx            ← サイドバー + メインコンテンツ
        Sidebar.tsx              ← ナビゲーションサイドバー
      ui/
        Button.tsx               ← ボタンコンポーネント
        Card.tsx                 ← カード UI
        Input.tsx                ← 入力フィールド
    pages/
      LoginPage.tsx              ← ログイン画面（React 版）
      SignupPage.tsx             ← サインアップ画面
      DashboardPage.tsx          ← ロボット一覧ダッシュボード
      SettingsPage.tsx           ← テーマ切替・安全設定
    services/
      api.ts                     ← Axios + インターセプター
    stores/
      authStore.ts               ← Zustand 認証ストア
      robotStore.ts              ← Zustand ロボット状態ストア
    types/
      index.ts                   ← TypeScript 型定義
    lib/
      utils.ts                   ← ユーティリティ関数
  package.json                   ← React, Vite, Tailwind 等
  vite.config.ts                 ← Vite 設定（プロキシ）
  tsconfig.json                  ← TypeScript 設定
  tailwind.config.js             ← Tailwind 設定
  postcss.config.js              ← PostCSS 設定
  index.html                     ← SPA エントリ（div#root）
```

---

## 起動方法

```bash
docker compose up --build
```

| サービス | URL | 説明 |
|----------|-----|------|
| frontend | http://localhost:3000 | Vite 開発サーバー（HMR） |
| backend | http://localhost:8000 | FastAPI |
| gateway | ws://localhost:8080 | WebSocket |
| postgres | 5432 | PostgreSQL |

### 開発時の便利機能

- ファイルを保存すると **即座にブラウザに反映**（HMR）
- TypeScript の型エラーはエディタ上でリアルタイムに表示
- React DevTools（ブラウザ拡張）でコンポーネントツリーを確認

---

## Step 8 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| フレームワーク | Vanilla JS → React 18 + TypeScript |
| ビルドツール | Nginx 静的配信 → Vite 開発サーバー |
| ルーティング | ハッシュルーター → React Router v6 |
| 状態管理 | グローバル変数 → Zustand |
| スタイリング | CSS ファイル → Tailwind CSS |
| API 通信 | fetch() → Axios + TanStack Query |
| ファイル数 | 40 files changed, +4,562 / -3,975 |

---

## 💡 このステップのポイント

Step 9 は **最もファイル変更が大きいステップ** です。
Vanilla JS から React への移行は「機能追加」ではなく「同じ機能の再実装」。
`git diff step/08-authentication..step/09-react-migration -- frontend/` で
変更内容を確認してみましょう。

---

## 🏋️ チャレンジ課題

1. **新しいページを追加**: `AboutPage.tsx` を作り、React Router にルートを追加
2. **コンポーネント分割**: DashboardPage のロボットカードを独立コンポーネントに分離
3. **Zustand ストア**: テーマ設定（ダーク/ライト）を永続化するストアを作成
4. **React DevTools**: ブラウザ拡張をインストールして、コンポーネントの再レンダリングを観察

---

## 次のステップへ

Step 10 では WebSocket をカスタムフックで React に統合し、**リアルタイムダッシュボード** を構築します:

```bash
git checkout step/10-realtime-dashboard
```
