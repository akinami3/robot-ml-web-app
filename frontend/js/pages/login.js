// =============================================================================
// Step 8: ログインページ
// =============================================================================
//
// 【認証フロー（フロントエンド側）】
// 1. ユーザーがフォームにユーザー名とパスワードを入力
// 2. POST /api/v1/auth/login にリクエスト
// 3. 成功 → Access Token + Refresh Token を受け取る
// 4. localStorage にトークンを保存
// 5. ロボット一覧ページにリダイレクト
//
// 【localStorage とは？】
// ブラウザに Key-Value データを永続保存する仕組み。
// セッション終了後もデータが残る（sessionStorage と違う）。
//
// 注意: localStorage は XSS 攻撃に脆弱。
// 本番では httpOnly Cookie を使うべき（Step 13 で扱う）。
// 学習用として Step 8 では localStorage を使用。
//
// =============================================================================

import { login } from "../api.js";

export async function renderLoginPage(container) {
  container.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <h2>🔐 ログイン</h2>
        <p class="auth-description">ユーザー名とパスワードを入力してください</p>

        <form id="loginForm" class="auth-form">
          <div class="form-group">
            <label for="username">ユーザー名</label>
            <input
              type="text"
              id="username"
              name="username"
              required
              autocomplete="username"
              placeholder="admin"
            />
          </div>

          <div class="form-group">
            <label for="password">パスワード</label>
            <input
              type="password"
              id="password"
              name="password"
              required
              autocomplete="current-password"
              placeholder="••••••••"
            />
          </div>

          <button type="submit" class="btn btn-primary btn-full" id="loginBtn">
            ログイン
          </button>

          <div id="loginError" class="form-message error" style="display: none;"></div>
        </form>

        <div class="auth-footer">
          <p>アカウントがない場合は <a href="#/signup">サインアップ</a></p>
          <p class="auth-hint">初期ユーザー: admin / admin123</p>
        </div>
      </div>
    </div>
  `;

  // --- フォーム送信処理 ---
  const form = document.getElementById("loginForm");
  const errorDiv = document.getElementById("loginError");
  const loginBtn = document.getElementById("loginBtn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorDiv.style.display = "none";
    loginBtn.disabled = true;
    loginBtn.textContent = "ログイン中...";

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      // --- API 呼び出し ---
      const data = await login(username, password);

      // --- トークンを localStorage に保存 ---
      //
      // 【localStorage の API】
      // setItem(key, value): 文字列を保存
      // getItem(key): 文字列を取得
      // removeItem(key): 削除
      //
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      // --- ログイン後のリダイレクト ---
      window.location.hash = "#/";

      // ナビゲーションの表示を更新
      window.dispatchEvent(new Event("auth-changed"));

    } catch (err) {
      errorDiv.textContent = `⚠️ ${err.message}`;
      errorDiv.style.display = "block";
      loginBtn.disabled = false;
      loginBtn.textContent = "ログイン";
    }
  });
}
