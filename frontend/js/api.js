// =============================================================================
// Step 6: API クライアント — fetch() によるバックエンド通信
// =============================================================================
//
// 【Step 5 までとの違い】
// Step 5 まで: フロントエンド → Gateway (WebSocket) のみ
// Step 6 から: フロントエンド → Backend (REST API) も追加
//
// このファイルはバックエンドの REST API と通信するための関数群。
// WebSocket (リアルタイム通信) とは別に、
// ロボットの CRUD 操作は普通の HTTP リクエストで行う。
//
// 【fetch() API とは？】
// ブラウザ組み込みの HTTP クライアント。
// XMLHttpRequest の後継で、Promise ベースの API。
//
// fetch() の基本構文:
//   const response = await fetch(url, options);
//   const data = await response.json();
//
// 【async/await とは？】
// 非同期処理を同期処理のように書ける構文。
//   async: この関数は非同期ですと宣言
//   await: Promise の結果が返るまで待つ
//
// 内部的には Promise を使っているが、
// .then().then().catch() のチェーンよりも読みやすい。
//
// =============================================================================

// =============================================================================
// API ベース URL
// =============================================================================
//
// 【なぜ環境変数的に管理する？】
// 開発環境: http://localhost:8000（直接バックエンドに接続）
// 本番環境: /api/v1（Nginx のリバースプロキシ経由）
//
// Step 6 では開発環境のみ対応。
// Step 13（プロダクション）で Nginx 経由に切り替える。
//
const API_BASE_URL = `http://${window.location.hostname || "localhost"}:8000/api/v1`;

// =============================================================================
// 共通の fetch ラッパー
// =============================================================================
//
// 【なぜラッパーを作る？】
// fetch() 呼び出しには毎回同じヘッダーやエラーハンドリングが必要。
// それを共通化して DRY（Don't Repeat Yourself）にする。
//
// Step 8 で認証ヘッダー（Authorization: Bearer <token>）を追加するときも、
// ここを1箇所変更するだけで全 API リクエストに反映される。
//
// 【レスポンスの ok チェック】
// fetch() は HTTP エラー（404, 500 など）でも reject しない！
// response.ok で成功レスポンス (200-299) かどうかを手動でチェックする必要がある。
// これは初心者が最もハマりやすいポイント。
//
async function apiRequest(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  const defaultHeaders = {
    "Content-Type": "application/json",
  };

  const config = {
    headers: { ...defaultHeaders, ...options.headers },
    ...options,
  };

  // --- fetch() の呼び出し ---
  // fetch() は Promise を返す。await で結果（Response オブジェクト）を待つ。
  const response = await fetch(url, config);

  // --- エラーチェック ---
  if (!response.ok) {
    // レスポンスボディにエラー詳細が含まれている場合がある
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      errorDetail = errorBody.detail || errorDetail;
    } catch {
      // JSON パースに失敗した場合は status だけ
    }
    throw new Error(errorDetail);
  }

  // --- レスポンスの JSON パース ---
  // response.json() も Promise を返すので await する。
  return response.json();
}


// =============================================================================
// Robot API — CRUD 関数
// =============================================================================
//
// 【関数名の規則】
// list ~ : 一覧取得 (GET /resources)
// get ~   : 1件取得 (GET /resources/{id})
// create ~: 新規作成 (POST /resources)
// update ~: 更新     (PATCH /resources/{id})
// delete ~: 削除     (DELETE /resources/{id})
//

/**
 * ロボット一覧を取得する
 * GET /api/v1/robots
 *
 * @returns {Promise<{robots: Array, total: number}>}
 */
export async function listRobots() {
  return apiRequest("/robots");
}

/**
 * 特定のロボットを取得する
 * GET /api/v1/robots/{id}
 *
 * @param {string} robotId - UUID
 * @returns {Promise<Object>} RobotResponse
 */
export async function getRobot(robotId) {
  return apiRequest(`/robots/${robotId}`);
}

/**
 * 新しいロボットを登録する
 * POST /api/v1/robots
 *
 * @param {Object} data - { name, robot_type?, description? }
 * @returns {Promise<Object>} 作成された RobotResponse
 */
export async function createRobot(data) {
  return apiRequest("/robots", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * ロボット情報を更新する
 * PATCH /api/v1/robots/{id}
 *
 * @param {string} robotId - UUID
 * @param {Object} data - 更新するフィールド
 * @returns {Promise<Object>} 更新された RobotResponse
 */
export async function updateRobot(robotId, data) {
  return apiRequest(`/robots/${robotId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * ロボットを削除する
 * DELETE /api/v1/robots/{id}
 *
 * @param {string} robotId - UUID
 * @returns {Promise<{message: string}>}
 */
export async function deleteRobot(robotId) {
  return apiRequest(`/robots/${robotId}`, {
    method: "DELETE",
  });
}
