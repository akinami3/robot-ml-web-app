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
  Dataset,           // データセット情報
  RAGDocument,       // RAGにアップロードされたドキュメント
  RAGQueryResult,    // RAGクエリの結果
  RecordingSession,  // センサーデータの記録セッション
  Robot,             // ロボット情報
  SensorData,        // センサーデータ
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

// ─── Sensors ───────────────────────────────────────────────────────────────
// 【sensorApi】センサーデータのAPIエンドポイント
// ロボットのセンサーデータ（LiDAR、カメラ、IMUなど）を取得
// ────────────────────────────────────────────────────────────────────────

export const sensorApi = {
  // センサーデータをクエリ（条件検索）で取得
  // GET /api/v1/sensors/data?robot_id=xxx&sensor_type=lidar&limit=100
  // params: クエリパラメータ（URLの ? 以降に付加される条件）
  query: (params: {
    robot_id: string;       // 対象ロボットのID
    sensor_type?: string;   // センサーの種類（省略可能 — ?で示す）
    limit?: number;         // 取得件数の上限（省略可能）
  }) => api.get<SensorData[]>("/sensors/data", { params }),

  // 特定センサーの最新データを1件取得
  // GET /api/v1/sensors/data/latest?robot_id=xxx&sensor_type=lidar
  // SensorData | null: データがあればSensorData、なければnullを返す
  latest: (robot_id: string, sensor_type: string) =>
    api.get<SensorData | null>("/sensors/data/latest", {
      params: { robot_id, sensor_type },
    }),

  // 利用可能なセンサータイプ一覧を取得
  // GET /api/v1/sensors/types → [{ value: "lidar", name: "LiDAR" }, ...]
  // UIのドロップダウンメニューなどに使う
  types: () => api.get<Array<{ value: string; name: string }>>("/sensors/types"),
};

// ─── Datasets ──────────────────────────────────────────────────────────────
// 【datasetApi】データセット管理のAPIエンドポイント
// 機械学習用のデータセットを管理する（一覧、作成、エクスポート、削除）
// ────────────────────────────────────────────────────────────────────────

export const datasetApi = {
  // データセット一覧を取得
  // GET /api/v1/datasets → Dataset[]
  list: () => api.get<Dataset[]>("/datasets"),

  // 特定のデータセットの詳細を取得
  // GET /api/v1/datasets/ds-123 → Dataset
  get: (id: string) => api.get<Dataset>(`/datasets/${id}`),

  // 新しいデータセットを作成
  // POST /api/v1/datasets → Dataset
  // 複数のロボットやセンサータイプを指定してデータセットにまとめる
  // tags?: string[] — タグはオプション（省略可能）
  create: (data: {
    name: string;            // データセット名
    description: string;     // 説明
    robot_ids: string[];     // 対象ロボットIDのリスト
    sensor_types: string[];  // 対象センサータイプのリスト
    tags?: string[];         // タグ（省略可能）
  }) => api.post<Dataset>("/datasets", data),

  // データセットをファイルとしてエクスポート
  // POST /api/v1/datasets/ds-123/export → ファイル（CSV, JSONなど）
  // format: 出力形式（"csv", "json" 等）
  export: (id: string, format: string) =>
    api.post(`/datasets/${id}/export`, { format }),

  // データセットを削除
  // DELETE /api/v1/datasets/ds-123
  delete: (id: string) => api.delete(`/datasets/${id}`),
};

// ─── Recordings ────────────────────────────────────────────────────────────
// 【recordingApi】データ記録のAPIエンドポイント
// ロボットのセンサーデータをリアルタイムで記録する（データセット作成のため）
// 記録の開始・停止・一覧取得・詳細取得ができる
// ────────────────────────────────────────────────────────────────────────

export const recordingApi = {
  // 記録セッション一覧を取得
  // GET /api/v1/recordings → RecordingSession[]
  list: () => api.get<RecordingSession[]>("/recordings"),

  // 特定の記録セッションの詳細を取得
  // GET /api/v1/recordings/rec-123 → RecordingSession
  get: (id: string) => api.get<RecordingSession>(`/recordings/${id}`),

  // 記録を開始する
  // POST /api/v1/recordings → RecordingSession（開始された記録の情報）
  // robot_id: 記録対象のロボット
  // sensor_types: 記録するセンサーの種類（省略可能 — 省略時は全センサー）
  start: (data: {
    robot_id: string;
    sensor_types?: string[];
  }) => api.post<RecordingSession>("/recordings", data),

  // 記録を停止する
  // POST /api/v1/recordings/rec-123/stop → RecordingSession（停止後の情報）
  stop: (id: string) =>
    api.post<RecordingSession>(`/recordings/${id}/stop`),
};

// ─── RAG ───────────────────────────────────────────────────────────────────
// 【ragApi】RAG（検索拡張生成）のAPIエンドポイント
// RAG = Retrieval-Augmented Generation
// ドキュメントを検索して、AIがそれを元に回答を生成する仕組み
//
// 【RAGの仕組み（初心者向け）】
// 1. ユーザーがドキュメント（マニュアル等）をアップロード
// 2. ドキュメントがベクトル化されてデータベースに保存
// 3. ユーザーが質問すると、関連するドキュメント断片を検索
// 4. 検索結果をもとにAIが回答を生成
// ────────────────────────────────────────────────────────────────────────

export const ragApi = {
  // ドキュメントをアップロード
  // POST /api/v1/rag/documents → RAGDocument（アップロードされたドキュメント情報）
  //
  // 【FormDataとは？ — 初心者向け】
  // ファイルアップロード時に使うデータ形式
  // 通常のJSONではファイルのバイナリデータを送れないので、
  // FormData を使って「multipart/form-data」形式で送信する
  //
  // 【File型とは？】
  // ブラウザのファイル入力（<input type="file">）で選択されたファイルを表す型
  uploadDocument: (file: File) => {
    // FormData オブジェクトを作成して、ファイルを追加
    const form = new FormData();
    form.append("file", file); // "file" はサーバー側で受け取るときのフィールド名

    // ファイルアップロード時はContent-Typeを multipart/form-data に変更
    // （デフォルトの application/json ではファイルを送れない）
    return api.post<RAGDocument>("/rag/documents", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // アップロード済みドキュメントの一覧を取得
  // GET /api/v1/rag/documents → RAGDocument[]
  listDocuments: () => api.get<RAGDocument[]>("/rag/documents"),

  // ドキュメントを削除
  // DELETE /api/v1/rag/documents/doc-123
  deleteDocument: (id: string) => api.delete(`/rag/documents/${id}`),

  // RAGに質問する
  // POST /api/v1/rag/query → RAGQueryResult（回答と参照ドキュメント）
  // question: 質問文（例: "ロボットのバッテリー交換方法は？"）
  // top_k: 検索結果の上位何件を使うか（省略可能）
  //   より多くのドキュメントを参照するほど精度は上がるが、処理時間も増える
  query: (question: string, top_k?: number) =>
    api.post<RAGQueryResult>("/rag/query", { question, top_k }),
};

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
