// =============================================================================
// Step 6: ロボット登録・編集フォーム
// =============================================================================
//
// 【HTML フォームとは？】
// ユーザーからの入力データを収集する UI 要素。
// <form>, <input>, <select>, <textarea> などを組み合わせて構成する。
//
// 【フォームの送信方法】
// 従来: <form action="/submit" method="POST"> → ページが遷移する
// 現代 (SPA): event.preventDefault() でデフォルト動作を止め、
//             JavaScript で fetch() を使って送信 → ページ遷移しない
//
// 【バリデーション（入力検証）】
// クライアントサイド: HTML の required, minlength, pattern 属性で簡易チェック
// サーバーサイド: Pydantic (FastAPI) で厳密なチェック
// → 両方必要！クライアントの検証はユーザー体験向上のため。
//   サーバーの検証はセキュリティのため（クライアントは信頼できない）。
//
// =============================================================================

import { createRobot, getRobot, updateRobot } from "../api.js";

// =============================================================================
// renderRobotFormPage — フォームの描画
// =============================================================================
export async function renderRobotFormPage(container, { param: robotId } = {}) {
  const isEdit = !!robotId;
  let existingRobot = null;

  // --- 編集モード: 既存データを取得 ---
  if (isEdit) {
    try {
      existingRobot = await getRobot(robotId);
    } catch (err) {
      container.innerHTML = `
        <div class="error-message">
          ⚠️ ロボットの取得に失敗しました: ${err.message}
          <br><a href="#/robots" class="btn btn-secondary">← 一覧に戻る</a>
        </div>
      `;
      return;
    }
  }

  // --- フォーム HTML ---
  //
  // 【各フォーム要素の説明】
  // <input type="text" required>: テキスト入力、必須
  // <select>: ドロップダウン選択
  // <textarea>: 複数行テキスト入力
  //
  // id 属性: JavaScript から getElementById で取得するため
  // name 属性: フォームデータのキー名（FormData API 用）
  // value 属性: 初期値（編集時に既存データを表示）
  //
  container.innerHTML = `
    <div class="page-header">
      <h2>${isEdit ? "✏️ ロボット編集" : "＋ ロボット登録"}</h2>
      <a href="#/robots" class="btn btn-secondary">← 一覧に戻る</a>
    </div>

    <form id="robotForm" class="robot-form">
      <div class="form-group">
        <label for="robotName">ロボット名 <span class="required">*</span></label>
        <input
          type="text"
          id="robotName"
          name="name"
          required
          minlength="1"
          maxlength="100"
          placeholder="例: TurtleBot3"
          value="${existingRobot ? escapeAttr(existingRobot.name) : ""}"
        />
        <small class="form-hint">1〜100文字で入力してください</small>
      </div>

      <div class="form-group">
        <label for="robotType">駆動タイプ</label>
        <select id="robotType" name="robot_type">
          <option value="differential" ${existingRobot?.robot_type === "differential" ? "selected" : ""}>
            差動二輪（Differential）
          </option>
          <option value="ackermann" ${existingRobot?.robot_type === "ackermann" ? "selected" : ""}>
            アッカーマン（Ackermann）
          </option>
          <option value="omni" ${existingRobot?.robot_type === "omni" ? "selected" : ""}>
            全方向移動（Omni）
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="robotDescription">説明</label>
        <textarea
          id="robotDescription"
          name="description"
          maxlength="500"
          rows="3"
          placeholder="ロボットの説明（任意）"
        >${existingRobot ? escapeHtml(existingRobot.description || "") : ""}</textarea>
        <small class="form-hint">最大500文字</small>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" id="submitBtn">
          ${isEdit ? "✏️ 更新する" : "＋ 登録する"}
        </button>
        <a href="#/robots" class="btn btn-secondary">キャンセル</a>
      </div>

      <div id="formMessage" class="form-message" style="display: none;"></div>
    </form>
  `;

  // --- フォーム送信処理 ---
  //
  // 【addEventListener("submit") のパターン】
  // 1. event.preventDefault() でフォームのデフォルト送信をキャンセル
  // 2. フォームの値を取得
  // 3. fetch() で API に送信
  // 4. 成功 → 一覧ページに遷移、失敗 → エラー表示
  //
  const form = document.getElementById("robotForm");
  const formMessage = document.getElementById("formMessage");
  const submitBtn = document.getElementById("submitBtn");

  form.addEventListener("submit", async (event) => {
    // --- デフォルトの送信動作を止める ---
    // これがないと、フォーム送信時にページがリロードされる。
    event.preventDefault();

    // --- ボタンを無効化（二重送信防止） ---
    submitBtn.disabled = true;
    submitBtn.textContent = "送信中...";

    const data = {
      name: document.getElementById("robotName").value.trim(),
      robot_type: document.getElementById("robotType").value,
      description: document.getElementById("robotDescription").value.trim(),
    };

    try {
      if (isEdit) {
        await updateRobot(robotId, data);
        showFormMessage(formMessage, "✅ ロボットを更新しました", "success");
      } else {
        await createRobot(data);
        showFormMessage(formMessage, "✅ ロボットを登録しました", "success");
      }

      // 成功後、1秒待ってから一覧へ戻る
      setTimeout(() => {
        window.location.hash = "#/robots";
      }, 1000);

    } catch (err) {
      showFormMessage(formMessage, `⚠️ エラー: ${err.message}`, "error");
      submitBtn.disabled = false;
      submitBtn.textContent = isEdit ? "✏️ 更新する" : "＋ 登録する";
    }
  });
}

// =============================================================================
// ヘルパー関数
// =============================================================================

function showFormMessage(el, text, type) {
  el.textContent = text;
  el.className = `form-message ${type}`;
  el.style.display = "block";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function escapeAttr(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
