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

// ---------------------------------------------------------------------------
// 【Step 11: センサーデータ API】 — Sensor Data Endpoints
// ---------------------------------------------------------------------------
//
// 💡 センサーデータ API は記録されたセンサーデータの読み取りに使う
// - WebSocket はリアルタイムデータ用（Step 10）
// - REST API は履歴データの検索・取得用（今回追加）
//
// 主なクエリパラメータ:
//   - robot_id: 特定のロボットのデータに絞り込み
//   - sensor_type: センサー種類で絞り込み（例: "lidar", "imu"）
//   - start/end: 時間範囲で絞り込み
//   - limit/offset: ページネーション
//
import type { RecordingSession, Dataset } from "@/types";

export const sensorApi = {
  // センサーデータの一覧取得（ページネーション対応）
  // GET /api/v1/sensors?robot_id=xxx&sensor_type=lidar&limit=100
  list: (params?: {
    robot_id?: string;
    sensor_type?: string;
    start?: string;
    end?: string;
    limit?: number;
    offset?: number;
  }) => api.get("/sensors", { params }),

  // 特定ロボットの最新センサーデータを取得
  // GET /api/v1/sensors/robot/robot-123/latest
  getLatest: (robotId: string, sensorType?: string) =>
    api.get(`/sensors/robot/${robotId}/latest`, {
      params: sensorType ? { sensor_type: sensorType } : undefined,
    }),

  // センサーデータの統計情報を取得
  // GET /api/v1/sensors/stats?robot_id=xxx
  // 用途: ダッシュボードでデータ量やセンサー状態を表示
  getStats: (robotId?: string) =>
    api.get("/sensors/stats", {
      params: robotId ? { robot_id: robotId } : undefined,
    }),
};

// ---------------------------------------------------------------------------
// 【Step 11: 記録セッション API】 — Recording Session Endpoints
// ---------------------------------------------------------------------------
//
// 💡 記録セッションの概念:
// 1. ユーザーが「記録開始」ボタンを押す → POST /recordings/start
// 2. バックエンドが RecordingWorker を通じて Redis Streams からデータを取得
// 3. データが TimescaleDB に保存される
// 4. ユーザーが「停止」ボタンを押す → POST /recordings/{id}/stop
// 5. セッションのデータをデータセットに変換可能
//
// 🔑 REST API の CRUD パターン:
// - Create: POST   /recordings/start  （記録開始）
// - Read:   GET    /recordings         （一覧取得）
// - Read:   GET    /recordings/{id}    （詳細取得）
// - Update: POST   /recordings/{id}/stop （停止 — 状態変更なので POST）
// - Delete: DELETE /recordings/{id}    （削除）
//
export const recordingApi = {
  // 記録セッション一覧を取得
  // GET /api/v1/recordings?robot_id=xxx&is_active=true
  list: (params?: { robot_id?: string; is_active?: boolean; limit?: number; offset?: number }) =>
    api.get<RecordingSession[]>("/recordings", { params }),

  // 特定の記録セッションの詳細を取得
  // GET /api/v1/recordings/session-123
  get: (id: string) =>
    api.get<RecordingSession>(`/recordings/${id}`),

  // 記録を開始する（新しいセッション作成）
  // POST /api/v1/recordings/start
  // body: { robot_id, config: { sensor_types, max_frequency_hz } }
  start: (data: {
    robot_id: string;
    config: {
      sensor_types: string[];
      max_frequency_hz: number;
      description?: string;
    };
  }) => api.post<RecordingSession>("/recordings/start", data),

  // 記録を停止する
  // POST /api/v1/recordings/{id}/stop
  // なぜ PATCH ではなく POST? → 「停止」はただの更新ではなく、
  // バックグラウンドワーカーの停止など副作用を伴うアクションだから
  stop: (id: string) =>
    api.post<RecordingSession>(`/recordings/${id}/stop`),

  // 記録セッションを削除
  // DELETE /api/v1/recordings/session-123
  delete: (id: string) =>
    api.delete(`/recordings/${id}`),
};

// ---------------------------------------------------------------------------
// 【Step 11: データセット API】 — Dataset Endpoints
// ---------------------------------------------------------------------------
//
// 💡 データセット（Dataset）は機械学習の「トレーニングデータ」の単位
// - 記録セッションのデータをまとめて1つのデータセットにする
// - CSV/JSON 形式でエクスポートして Python で利用可能
// - タグやメタデータで分類・検索できる
//
// 🔑 標準的な RESTful CRUD:
//   C → POST   /datasets
//   R → GET    /datasets, GET /datasets/{id}
//   U → PATCH  /datasets/{id}
//   D → DELETE /datasets/{id}
//   + Export: POST /datasets/{id}/export（特殊アクション）
//
export const datasetApi = {
  // データセット一覧を取得
  // GET /api/v1/datasets?status=ready&tags=indoor
  list: (params?: {
    status?: string;
    tags?: string;
    limit?: number;
    offset?: number;
  }) => api.get<Dataset[]>("/datasets", { params }),

  // 特定のデータセットの詳細を取得
  // GET /api/v1/datasets/dataset-456
  get: (id: string) =>
    api.get<Dataset>(`/datasets/${id}`),

  // 新しいデータセットを作成
  // POST /api/v1/datasets
  create: (data: {
    name: string;
    description?: string;
    sensor_types?: string[];
    robot_ids?: string[];
    tags?: string[];
  }) => api.post<Dataset>("/datasets", data),

  // データセット情報を部分更新
  // PATCH /api/v1/datasets/dataset-456
  update: (id: string, data: Partial<Dataset>) =>
    api.patch<Dataset>(`/datasets/${id}`, data),

  // データセットを削除
  // DELETE /api/v1/datasets/dataset-456
  delete: (id: string) =>
    api.delete(`/datasets/${id}`),

  // データセットをエクスポート（CSV/JSON形式）
  // POST /api/v1/datasets/dataset-456/export
  // 💡 なぜ POST? GET でも取得可能だが、大量データの処理は
  // バックグラウンドジョブとして開始するため POST が適切
  export: (id: string, format: "csv" | "json" = "json") =>
    api.post(`/datasets/${id}/export`, { format }),
};

// ─── 今後のステップで追加される API ─────────────────────────────────────────
//
// Step 13 以降で以下の API クライアントが追加されます:
//   - auditApi → Step 13: Audit Logs

// ---------------------------------------------------------------------------
// 【Step 12: RAG API】 — Retrieval-Augmented Generation
// ---------------------------------------------------------------------------
//
// 💡 RAG（検索拡張生成）とは？
// 1. ドキュメント（PDF, TXT, MD）をアップロード
// 2. テキストをチャンク（断片）に分割 → ベクトル化 → DB に保存
// 3. ユーザーが質問すると、類似ドキュメントを検索 → LLM が回答を生成
//
// 主な操作:
// - ドキュメントのアップロード（multipart/form-data）
// - ドキュメント一覧の取得
// - ドキュメントの削除
// - 質問 → 回答（通常 + SSE ストリーミング）
//
// 💡 SSE（Server-Sent Events）とは？
// サーバーからクライアントへ一方向のストリーミング通信を行うプロトコル。
// LLM の回答をトークン（単語）ごとにリアルタイムで受信できる。
// WebSocket と違い、HTTP の上で動作するためシンプル。
//
import type { RAGDocument, RAGQueryResult } from "@/types";

export const ragApi = {
  // ドキュメント一覧を取得
  // GET /api/v1/rag/documents
  listDocuments: () =>
    api.get<RAGDocument[]>("/rag/documents"),

  // ドキュメントをアップロード（multipart/form-data）
  // POST /api/v1/rag/documents
  //
  // 💡 FormData を使う理由:
  // ファイルアップロードは JSON では送れない。
  // multipart/form-data 形式にすることで、バイナリファイル + メタデータを同時に送信。
  // Axios はヘッダーの Content-Type を自動設定してくれる。
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<RAGDocument>("/rag/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // ドキュメントを削除
  // DELETE /api/v1/rag/documents/{id}
  deleteDocument: (id: string) =>
    api.delete(`/rag/documents/${id}`),

  // 質問して回答を取得（非ストリーミング）
  // POST /api/v1/rag/query
  query: (question: string, topK: number = 5, minSimilarity: number = 0.3) =>
    api.post<RAGQueryResult>("/rag/query", {
      question,
      top_k: topK,
      min_similarity: minSimilarity,
    }),

  // SSE ストリーミングの URL を生成（fetch API で直接取得する用）
  // POST /api/v1/rag/query/stream
  //
  // 💡 このメソッドは URL を返すだけ。実際の SSE 接続は
  // RAGChatPage.tsx 内で EventSource API を使って行う。
  getStreamUrl: () => {
    const baseUrl = api.defaults.baseURL || "/api/v1";
    return `${baseUrl}/rag/query/stream`;
  },
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
