// =============================================================================
// Step 8: サインアップページ
// =============================================================================
//
// 【サインアップのフロー】
// 1. ユーザー名、メールアドレス、パスワードを入力
// 2. POST /api/v1/auth/signup にリクエスト
// 3. 成功 → ログインページにリダイレクト
// 4. 失敗 → エラーメッセージを表示
//
// 【バリデーション】
// フロントエンドバリデーション: 入力の形式チェック（UX向上）
// バックエンドバリデーション: 重複チェック等の本質的な検証（セキュリティ）
// 両方必要！フロントだけでは改ざん可能（DevTools で回避できる）。
//
// =============================================================================

import { signup } from "../api.js";

export async function renderSignupPage(container) {
  container.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <h2>📝 サインアップ</h2>
        <p class="auth-description">新しいアカウントを作成します</p>

        <form id="signupForm" class="auth-form">
          <div class="form-group">
            <label for="username">ユーザー名（3〜50文字）</label>
            <input
              type="text"
              id="username"
              name="username"
              required
              minlength="3"
              maxlength="50"
              autocomplete="username"
              placeholder="taro_yamada"
            />
          </div>

          <div class="form-group">
            <label for="email">メールアドレス</label>
            <input
              type="email"
              id="email"
              name="email"
              required
              autocomplete="email"
              placeholder="taro@example.com"
            />
          </div>

          <div class="form-group">
            <label for="password">パスワード（8文字以上）</label>
            <input
              type="password"
              id="password"
              name="password"
              required
              minlength="8"
              autocomplete="new-password"
              placeholder="••••••••"
            />
          </div>

          <div class="form-group">
            <label for="passwordConfirm">パスワード（確認）</label>
            <input
              type="password"
              id="passwordConfirm"
              name="passwordConfirm"
              required
              minlength="8"
              autocomplete="new-password"
              placeholder="••••••••"
            />
          </div>

          <button type="submit" class="btn btn-primary btn-full" id="signupBtn">
            アカウント作成
          </button>

          <div id="signupError" class="form-message error" style="display: none;"></div>
          <div id="signupSuccess" class="form-message success" style="display: none;"></div>
        </form>

        <div class="auth-footer">
          <p>すでにアカウントがある場合は <a href="#/login">ログイン</a></p>
        </div>
      </div>
    </div>
  `;

  const form = document.getElementById("signupForm");
  const errorDiv = document.getElementById("signupError");
  const successDiv = document.getElementById("signupSuccess");
  const signupBtn = document.getElementById("signupBtn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorDiv.style.display = "none";
    successDiv.style.display = "none";

    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const passwordConfirm = document.getElementById("passwordConfirm").value;

    // --- フロントエンドバリデーション ---
    //
    // UX 向上のためのチェック（サーバー側でも同じチェックが行われる）
    //
    if (password !== passwordConfirm) {
      errorDiv.textContent = "⚠️ パスワードが一致しません";
      errorDiv.style.display = "block";
      return;
    }

    if (password.length < 8) {
      errorDiv.textContent = "⚠️ パスワードは8文字以上にしてください";
      errorDiv.style.display = "block";
      return;
    }

    signupBtn.disabled = true;
    signupBtn.textContent = "作成中...";

    try {
      await signup(username, email, password);

      // --- 成功メッセージを表示 → 自動リダイレクト ---
      successDiv.textContent = "✅ アカウントが作成されました。ログインページに移動します...";
      successDiv.style.display = "block";

      setTimeout(() => {
        window.location.hash = "#/login";
      }, 1500);

    } catch (err) {
      errorDiv.textContent = `⚠️ ${err.message}`;
      errorDiv.style.display = "block";
      signupBtn.disabled = false;
      signupBtn.textContent = "アカウント作成";
    }
  });
}
