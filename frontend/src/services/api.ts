// =============================================================================
// api.ts — API通信サービス（バックエンドとの通信を一元管理）
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、フロントエンドからバックエンドサーバーへのHTTP通信を
// すべて一箇所にまとめて管理します。
//
// 【なぜこのファイルが必要？】
// - 各コンポーネントで直接 fetch() や axios を呼ぶと、同じ設定を何度も書くことになる
// - 認証トークンの付与を毎回書くのは面倒でミスが起きやすい
// - エラーハンドリング（401エラーでの自動トークンリフレッシュ）を一箇所に集約
// - APIエンドポイント（URL）を一覧にまとめて管理しやすくする
//
// 【使われている技術・パターン】
// - Axios: HTTP通信ライブラリ（fetchより便利な機能が多い）
// - Interceptor（インターセプター）: リクエスト/レスポンスの途中に処理を挟む仕組み
// - JWT自動リフレッシュ: accessTokenの期限切れを自動で処理する仕組み
// - APIグルーピング: 関連するエンドポイントをオブジェクトにまとめるパターン
// - ジェネリクス: api.post<AuthTokens>(...) のように、レスポンスの型を指定できる
//
// 【HTTPリクエストの基本（初心者向け）】
// - GET: データを取得する（一覧表示、詳細表示）
// - POST: データを送信・作成する（ログイン、新規登録）
// - PATCH: データを部分的に更新する
// - DELETE: データを削除する
// =============================================================================

// ---------------------------------------------------------------------------
// 【インポート】
// ---------------------------------------------------------------------------

// axios: HTTP通信ライブラリ
// ブラウザ標準の fetch() よりも多くの便利機能を提供する
// - 自動的なJSON変換（送信時も受信時も）
// - リクエスト/レスポンスのインターセプター
// - タイムアウト設定
// - リクエストのキャンセル
import axios from "axios";

// useAuthStore: 認証ストア（前のファイルで定義したもの）
// ここではコンポーネント外で使うので、useAuthStore.getState() で直接アクセスする
// （React Hooksはコンポーネント内でしか使えないが、getState()はどこでもOK）
import { useAuthStore } from "@/stores/authStore";

// 型のインポート: APIのレスポンスに型を付けるために使用
// これにより、api.get<Robot[]>("/robots") のレスポンスが Robot[] 型だとわかる
// → エディタの補完（オートコンプリート）が効くようになり、開発しやすい
import type {
  AuthTokens,        // 認証トークンペア（access_token, refresh_token）
  Robot,             // ロボット情報
  User,              // ユーザー情報
} from "@/types";

// ---------------------------------------------------------------------------
// 【Axiosインスタンスの作成】
// ---------------------------------------------------------------------------
// axios.create() でカスタム設定を持つAxiosインスタンスを作成する
// デフォルトの axios を直接使う代わりに、このインスタンスを使うことで
// baseURLやheadersの設定を毎回書く必要がなくなる
//
// 例: api.get("/robots") は実際には GET /api/v1/robots にリクエストを送る
const api = axios.create({
  // baseURL: すべてのリクエストURLのプレフィックス（接頭辞）
  // api.get("/robots") → "/api/v1" + "/robots" のURLにリクエスト
  baseURL: "/api/v1",

  // headers: すべてのリクエストに付与されるデフォルトHTTPヘッダー
  // "Content-Type": "application/json" → 送信データがJSON形式であることを伝える
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// 【リクエストインターセプター】— APIリクエスト送信前に自動実行される処理
// ---------------------------------------------------------------------------
// インターセプター = 「横取りする人」
// リクエストがサーバーに送られる前に、自動的にJWTトークンをヘッダーに追加する
//
// 【なぜ必要？】
// 認証が必要なAPI（ロボット操作、データ取得など）では、
// 「自分はログイン済みのユーザーです」とサーバーに伝える必要がある。
// 毎回手動でトークンを付けるのは面倒なので、インターセプターで自動化する。
//
// 【処理の流れ】
// 1. コンポーネントが api.get("/robots") を呼ぶ
// 2. ★ インターセプターが実行される（ここの処理）
// 3. トークンが付与されたリクエストがサーバーに送信される

// Request interceptor - attach token
// （リクエストインターセプター — トークンを付与する）
api.interceptors.request.use((config) => {
  // useAuthStore.getState() でストアの現在の状態を直接取得
  // （コンポーネント外なのでフック形式では使えないため .getState() を使用）
  const token = useAuthStore.getState().accessToken;

  // トークンが存在する場合のみ、Authorizationヘッダーを追加
  // "Bearer" は JWT認証で使われる標準的なプレフィックス（認証スキーム）
  // → Authorization: Bearer eyJhbGciOi... のような形式になる
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // config を返すことで、変更されたリクエスト設定が実際のリクエストに反映される
  return config;
});

// ---------------------------------------------------------------------------
// 【レスポンスインターセプター】— APIレスポンス受信後に自動実行される処理
// ---------------------------------------------------------------------------
// サーバーからのレスポンスを受け取った後、エラー処理を自動的に行う
//
// 【401エラーの自動リフレッシュとは？】
// 1. accessToken の有効期限が切れると、サーバーは 401 (Unauthorized) エラーを返す
// 2. このインターセプターが 401 を検知
// 3. refreshToken を使って新しい accessToken を自動取得
// 4. 元のリクエストを新しいトークンで再送信
// 5. ユーザーは何も気づかずに操作を続けられる！
//
// 【引数の説明】
// 第1引数: 成功時の処理（ステータスコード 200-299 — そのまま返す）
// 第2引数: エラー時の処理（401の場合にリフレッシュを試みる）

// Response interceptor - handle 401
// （レスポンスインターセプター — 401エラーを処理する）
api.interceptors.response.use(
  // 成功時: レスポンスをそのまま返す（何も処理しない）
  (response) => response,

  // エラー時の処理
  // async: この関数内で await（非同期処理の完了待ち）を使うため必要
  async (error) => {
    // 【ステータスコード 401 = Unauthorized（認証失敗）の場合】
    // error.response?.status:「?.」はオプショナルチェイニング
    // → error.response が null/undefined でもエラーにならず、undefined を返す
    if (error.response?.status === 401) {
      // ストアの現在の状態を取得
      const store = useAuthStore.getState();

      // リフレッシュトークンが存在する場合、新しいアクセストークンを取得試行
      if (store.refreshToken) {
        try {
          // リフレッシュトークンを使って、新しいトークンペアをサーバーに要求
          // 注意: ここでは api ではなく素の axios.post を使っている
          // → api を使うとインターセプターが再度動いてしまうため
          const res = await axios.post("/api/v1/auth/refresh", {
            refresh_token: store.refreshToken,
          });

          // 新しいトークンペアをストアに保存（localStorageにも自動保存される）
          store.setTokens(res.data);

          // 元のリクエストのAuthorizationヘッダーを新しいトークンに更新
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;

          // 元のリクエストを新しいトークンで再送信
          // api.request() は Axiosの設定オブジェクトを渡してリクエストを実行するメソッド
          return api.request(error.config);
        } catch {
          // リフレッシュも失敗した場合 = トークンが完全に無効
          // ログアウトしてログイン画面へ誘導
          store.logout();
        }
      } else {
        // リフレッシュトークンがない場合もログアウト
        store.logout();
      }
    }

    // 401以外のエラー、またはリフレッシュ失敗時は、エラーをそのまま返す
    // Promise.reject() でエラーを呼び出し元に伝播させる
    // → 呼び出し元の catch ブロックや .catch() でエラーハンドリングできる
    return Promise.reject(error);
  }
);

// ─── Auth ──────────────────────────────────────────────────────────────────
// 【authApi】認証関連のAPIエンドポイント
// ログイン、新規登録、ユーザー情報取得
//
// 【ジェネリクス <AuthTokens> とは？（初心者向け）】
// api.post<AuthTokens>("/auth/login", ...) の <AuthTokens> は、
// 「このAPIのレスポンスは AuthTokens 型です」と宣言している
// → response.data が AuthTokens 型として扱われ、型チェックや補完が効く
// ─────────────────────────────────────────────────────────────────────────

export const authApi = {
  // ログイン: ユーザー名とパスワードを送信して認証トークンを取得
  // POST /api/v1/auth/login → AuthTokens（access_tokenとrefresh_token）
  login: (username: string, password: string) =>
    api.post<AuthTokens>("/auth/login", { username, password }),

  // 新規ユーザー登録
  // POST /api/v1/auth/register → User（作成されたユーザー情報）
  // data の型を明示して、必要なフィールドがわかるようにしている
  register: (data: { username: string; email: string; password: string }) =>
    api.post<User>("/auth/register", data),

  // 現在のユーザー情報を取得
  // GET /api/v1/auth/me → User（id, username, email, role）
  // Authorizationヘッダーのトークンから「誰か」を判定してサーバーが返す
  me: () => api.get<User>("/auth/me"),
};

// ─── Robots ────────────────────────────────────────────────────────────────
// 【robotApi】ロボット管理のAPIエンドポイント
// ロボットの一覧取得、詳細取得、作成、更新、削除（CRUD操作）
//
// 【CRUDとは？】
// Create（作成）、Read（読取）、Update（更新）、Delete（削除）の頭文字
// ほとんどのデータ管理はこの4つの操作で構成される
// ────────────────────────────────────────────────────────────────────────

export const robotApi = {
  // ロボット一覧を取得
  // GET /api/v1/robots → Robot[]（ロボットの配列）
  list: () => api.get<Robot[]>("/robots"),

  // 特定のロボットの詳細情報を取得
  // GET /api/v1/robots/robot-123 → Robot
  // テンプレートリテラル（`バッククォート`）で動的にURLを構築
  get: (id: string) => api.get<Robot>(`/robots/${id}`),

  // 新しいロボットを作成
  // POST /api/v1/robots → Robot（作成されたロボット情報）
  create: (data: { name: string; adapter_type: string }) =>
    api.post<Robot>("/robots", data),

  // ロボット情報を部分更新
  // PATCH /api/v1/robots/robot-123 → Robot（更新後のロボット情報）
  // PATCH は PUT と違い、変更するフィールドだけ送ればOK
  // Partial<Robot>: Robotの一部のプロパティだけ指定可能
  update: (id: string, data: Partial<Robot>) =>
    api.patch<Robot>(`/robots/${id}`, data),

  // ロボットを削除
  // DELETE /api/v1/robots/robot-123 → 削除完了
  delete: (id: string) => api.delete(`/robots/${id}`),
};

// ─── 今後のステップで追加される API ─────────────────────────────────────────
//
// Step 10 以降で以下の API クライアントが追加されます:
//   - sensorApi    → Step 10: Realtime Dashboard
//   - datasetApi   → Step 11: Data Management
//   - recordingApi → Step 11: Data Management
//   - ragApi       → Step 12: RAG Chat

// ---------------------------------------------------------------------------
// 【デフォルトエクスポート】
// ---------------------------------------------------------------------------
// 設定済みのAxiosインスタンスをデフォルトエクスポート
// 使い方: import api from "@/services/api";
//         api.get("/some-endpoint");
//
// 上のエンドポイントグループは名前付きエクスポート:
// 使い方: import { authApi, robotApi } from "@/services/api";
export default api;
