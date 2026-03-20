// =============================================================================
// Step 8: API クライアント — 認証対応版
// =============================================================================
//
// 【Step 7 からの変更点】
// 1. Authorization ヘッダーの自動付与（Bearer トークン）
// 2. login() / signup() / refreshToken() 関数の追加
// 3. 401 レスポンス時のトークン自動リフレッシュ
// 4. ログアウト処理（トークン削除 + リダイレクト）
//
// 【Bearer トークンとは？】
// HTTP リクエストのヘッダーに含めるアクセストークン。
//
//   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
//
// "Bearer" は「この文字列の持ち主（bearer）を認証する」という意味。
// OAuth 2.0 で標準化された方式（RFC 6750）。
//
// 【トークンリフレッシュのフロー】
// 1. API リクエスト → 401 Unauthorized が返る
// 2. Refresh Token を使って新しい Access Token を取得
// 3. 新しいトークンで元のリクエストをリトライ
// 4. リフレッシュも失敗 → ログアウト（ログインページへ）
//
// このパターンは「サイレントリフレッシュ」と呼ばれ、
// ユーザーに再ログインを強制しないUXを実現する。
//
// =============================================================================

// =============================================================================
// API ベース URL
// =============================================================================
const API_BASE_URL = `http://${window.location.hostname || "localhost"}:8000/api/v1`;

// =============================================================================
// トークン管理ヘルパー
// =============================================================================
//
// 【localStorage の使い方】
// Key-Value 形式でブラウザにデータを永続保存する。
//
//   localStorage.setItem("key", "value")  // 保存
//   localStorage.getItem("key")           // 取得（なければ null）
//   localStorage.removeItem("key")        // 削除
//
// 注意: localStorage は XSS（クロスサイトスクリプティング）に脆弱。
// 悪意のあるスクリプトが localStorage を読み取れてしまう。
// 本番環境では httpOnly Cookie を使うべき（Step 13 で扱う）。
//

/**
 * 保存された Access Token を取得
 * @returns {string|null}
 */
export function getAccessToken() {
  return localStorage.getItem("access_token");
}

/**
 * 保存された Refresh Token を取得
 * @returns {string|null}
 */
export function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}

/**
 * トークンペアを保存
 */
export function saveTokens(accessToken, refreshToken) {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}

/**
 * トークンを削除してログアウト
 */
export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

/**
 * ログイン状態の判定
 *
 * 【JWT の構造】
 * Header.Payload.Signature の3パートで構成。
 * Payload をデコードすれば exp（有効期限）が読める。
 *
 * ただし、ここではトークンの「存在有無」のみで判定。
 * 有効期限のチェックはサーバー側で行う。
 */
export function isLoggedIn() {
  return !!getAccessToken();
}

/**
 * JWT ペイロードをデコードして現在のユーザー情報を取得
 *
 * 【JWT のデコード】
 * JWT は Base64 エンコードされた JSON。
 * atob() でデコードすれば中身が読める。
 *
 * 注意: これは「検証」ではなく「デコード」。
 * 署名の検証はサーバー側でしか行えない（秘密鍵が必要だから）。
 */
export function getCurrentUser() {
  const token = getAccessToken();
  if (!token) return null;

  try {
    // JWT の2番目のパート（Payload）を取得
    const payload = token.split(".")[1];
    // Base64 デコード → JSON パース
    const decoded = JSON.parse(atob(payload));
    return {
      id: decoded.sub,
      username: decoded.name,
      role: decoded.role,
    };
  } catch {
    return null;
  }
}

// =============================================================================
// 認証不要の API リクエスト（ログイン・サインアップ用）
// =============================================================================

async function apiRequestNoAuth(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  const config = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      errorDetail = errorBody.detail || errorDetail;
    } catch {
      // JSON パースに失敗
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// =============================================================================
// 認証付き API リクエスト（メイン）
// =============================================================================
//
// 【401 レスポンスの自動処理】
// 1. Access Token 付きでリクエスト
// 2. 401 が返ったら → Refresh Token で新トークンを取得
// 3. 新 Access Token で元のリクエストをリトライ
// 4. リフレッシュも失敗 → ログアウト
//
// isRetry フラグで無限ループ（リフレッシュ → 401 → リフレッシュ...）を防止。
//
async function apiRequest(path, options = {}, isRetry = false) {
  const url = `${API_BASE_URL}${path}`;

  // --- Authorization ヘッダーの付与 ---
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(url, config);

  // --- 401 Unauthorized: トークンリフレッシュを試行 ---
  if (response.status === 401 && !isRetry) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // リフレッシュ成功 → 元のリクエストをリトライ
      return apiRequest(path, options, true);
    } else {
      // リフレッシュ失敗 → ログアウト
      logout();
      throw new Error("セッションが期限切れです。再度ログインしてください。");
    }
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      errorDetail = errorBody.detail || errorDetail;
    } catch {
      // JSON パースに失敗
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// =============================================================================
// トークンリフレッシュ
// =============================================================================
//
// 【リフレッシュトークンの役割】
// Access Token の有効期限は短い（30分）→ セキュリティ上安全
// でも30分ごとにログインし直すのは不便。
// → Refresh Token（有効期限7日）で新しい Access Token を取得。
//
// Access Token: 認証用。短命。リクエストごとに送信。盗まれても被害が限定的。
// Refresh Token: 更新用。長命。トークン更新時のみ送信。
//
async function tryRefreshToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const data = await apiRequestNoAuth("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// =============================================================================
// ログアウト
// =============================================================================
export function logout() {
  clearTokens();
  window.location.hash = "#/login";
  window.dispatchEvent(new Event("auth-changed"));
}

// =============================================================================
// 認証 API 関数
// =============================================================================

/**
 * ログイン
 * POST /api/v1/auth/login
 *
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{access_token, refresh_token, token_type}>}
 */
export async function login(username, password) {
  const data = await apiRequestNoAuth("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  // トークンを保存
  saveTokens(data.access_token, data.refresh_token);
  window.dispatchEvent(new Event("auth-changed"));

  return data;
}

/**
 * サインアップ
 * POST /api/v1/auth/signup
 *
 * @param {string} username
 * @param {string} email
 * @param {string} password
 * @returns {Promise<Object>} UserResponse
 */
export async function signup(username, email, password) {
  return apiRequestNoAuth("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
}

// =============================================================================
// Robot API — CRUD 関数（認証ヘッダーが自動付与される）
// =============================================================================
//
// 【Step 7 からの変更】
// apiRequest() が Authorization ヘッダーを自動挿入するため、
// 呼び出し側のコードは変わらない。
// → これが「ラッパー関数」のメリット。1箇所の変更で全 API に反映される。
//

/**
 * ロボット一覧を取得する
 * GET /api/v1/robots
 */
export async function listRobots() {
  return apiRequest("/robots");
}

/**
 * 特定のロボットを取得する
 * GET /api/v1/robots/{id}
 */
export async function getRobot(robotId) {
  return apiRequest(`/robots/${robotId}`);
}

/**
 * 新しいロボットを登録する
 * POST /api/v1/robots（operator 以上の権限が必要）
 */
export async function createRobot(data) {
  return apiRequest("/robots", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * ロボット情報を更新する
 * PATCH /api/v1/robots/{id}（operator 以上の権限が必要）
 */
export async function updateRobot(robotId, data) {
  return apiRequest(`/robots/${robotId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * ロボットを削除する
 * DELETE /api/v1/robots/{id}（admin 権限が必要）
 */
export async function deleteRobot(robotId) {
  return apiRequest(`/robots/${robotId}`, {
    method: "DELETE",
  });
}
