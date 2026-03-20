// =============================================================================
// Step 6: ロボット一覧ページ
// =============================================================================
//
// 【fetch() を使った API 呼び出し】
// ブラウザ内蔵の fetch() API で、バックエンド (FastAPI) と通信する。
// WebSocket (Gateway) とは別の、通常の HTTP リクエスト。
//
// 用途の使い分け:
//   fetch() (HTTP):  CRUD 操作（データの読み書き、一回きりの操作）
//   WebSocket:       リアルタイム通信（センサーデータ、制御コマンド）
//
// 【async/await パターン】
// 1. async function で宣言
// 2. await fetch() でリクエストを送信、レスポンスを待つ
// 3. try/catch でネットワークエラーやサーバーエラーをハンドリング
//
// =============================================================================

import { listRobots, deleteRobot } from "../api.js";

// =============================================================================
// ステータスの表示情報マップ
// =============================================================================
const STATUS_MAP = {
  offline: { label: "待機中", icon: "🔴", class: "status-offline" },
  online: { label: "オンライン", icon: "🟢", class: "status-online" },
  active: { label: "稼働中", icon: "🟡", class: "status-active" },
  error: { label: "エラー", icon: "🔴", class: "status-error" },
  maintenance: { label: "メンテ", icon: "🔧", class: "status-maintenance" },
};

const TYPE_LABELS = {
  differential: "差動二輪",
  ackermann: "アッカーマン",
  omni: "全方向",
};

// =============================================================================
// renderRobotListPage — ロボット一覧ページの描画
// =============================================================================
//
// 【ページ描画のパターン】
// 1. スケルトン（ローディング UI）を先に描画
// 2. API を呼び出してデータを取得
// 3. データでスケルトンを置き換え
//
// 先にスケルトンを見せることで、ユーザーは「読み込み中」と理解できる。
// 何も表示しないとフリーズしたように見える。
//
export async function renderRobotListPage(container) {
  // --- ローディング表示 ---
  container.innerHTML = `
    <div class="page-header">
      <h2>🤖 ロボット一覧</h2>
      <a href="#/robots/new" class="btn btn-primary">＋ 新規登録</a>
    </div>
    <div class="loading">読み込み中...</div>
  `;

  try {
    // --- API 呼び出し ---
    const data = await listRobots();

    // --- テーブル描画 ---
    if (data.robots.length === 0) {
      container.innerHTML = `
        <div class="page-header">
          <h2>🤖 ロボット一覧</h2>
          <a href="#/robots/new" class="btn btn-primary">＋ 新規登録</a>
        </div>
        <div class="empty-state">
          <p>登録されたロボットはありません。</p>
          <a href="#/robots/new" class="btn btn-primary">最初のロボットを登録</a>
        </div>
      `;
      return;
    }

    // --- テーブル HTML の構築 ---
    //
    // 【innerHTML vs createElement】
    // innerHTML: HTML 文字列を直接書き込む。簡潔だがXSSリスクあり。
    // createElement: DOM API でノードを作る。安全だが冗長。
    //
    // Step 6（教育用）では innerHTML を使用。
    // Step 9 (React) では JSX が内部で createElement を使う。
    //
    // XSS（クロスサイトスクリプティング）への対策:
    // ユーザー入力を直接 innerHTML に入れると、
    // <script>alert('XSS')</script> のような悪意のあるコードが実行される。
    // → escapeHtml() で特殊文字をエスケープする。
    //
    const robotRows = data.robots.map((robot) => {
      const status = STATUS_MAP[robot.status] || STATUS_MAP.offline;
      const typeName = TYPE_LABELS[robot.robot_type] || robot.robot_type;
      const created = new Date(robot.created_at).toLocaleDateString("ja-JP");

      return `
        <tr>
          <td>
            <div class="robot-name">${escapeHtml(robot.name)}</div>
            <div class="robot-desc">${escapeHtml(robot.description || "")}</div>
          </td>
          <td><span class="badge">${typeName}</span></td>
          <td><span class="${status.class}">${status.icon} ${status.label}</span></td>
          <td>${created}</td>
          <td class="actions">
            <a href="#/robots/edit/${robot.id}" class="btn btn-sm btn-secondary">✏️ 編集</a>
            <button class="btn btn-sm btn-danger" data-delete-id="${robot.id}" data-name="${escapeHtml(robot.name)}">
              🗑️ 削除
            </button>
          </td>
        </tr>
      `;
    }).join("");

    container.innerHTML = `
      <div class="page-header">
        <h2>🤖 ロボット一覧</h2>
        <div>
          <span class="total-count">${data.total} 台登録</span>
          <a href="#/robots/new" class="btn btn-primary">＋ 新規登録</a>
        </div>
      </div>
      <div class="table-container">
        <table class="robot-table">
          <thead>
            <tr>
              <th>ロボット</th>
              <th>駆動タイプ</th>
              <th>状態</th>
              <th>登録日</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            ${robotRows}
          </tbody>
        </table>
      </div>
    `;

    // --- 削除ボタンにイベントリスナーを追加 ---
    //
    // 【イベント委譲（Event Delegation）】
    // 各ボタンに addEventListener するのではなく、
    // 親要素で一括してイベントをキャッチすることもできるが、
    // ここでは分かりやすさ重視で各ボタンに設定。
    //
    container.querySelectorAll("[data-delete-id]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const robotId = btn.getAttribute("data-delete-id");
        const robotName = btn.getAttribute("data-name");

        // 【confirm() ダイアログ】
        // ブラウザ標準の確認ダイアログ。
        // 本番アプリでは独自のモーダルを使うが、Step 6 では簡易版で。
        if (!confirm(`「${robotName}」を削除しますか？`)) return;

        try {
          await deleteRobot(robotId);
          // 削除成功 → 一覧を再描画
          renderRobotListPage(container);
        } catch (err) {
          alert(`削除に失敗しました: ${err.message}`);
        }
      });
    });

  } catch (err) {
    // --- エラー表示 ---
    container.innerHTML = `
      <div class="page-header">
        <h2>🤖 ロボット一覧</h2>
        <a href="#/robots/new" class="btn btn-primary">＋ 新規登録</a>
      </div>
      <div class="error-message">
        ⚠️ ロボット一覧の取得に失敗しました。<br>
        <small>${escapeHtml(err.message)}</small><br>
        <small>バックエンド (localhost:8000) が起動しているか確認してください。</small>
      </div>
    `;
  }
}

// =============================================================================
// escapeHtml — XSS 対策
// =============================================================================
//
// 【なぜ必要？】
// ユーザーがロボット名に `<script>alert('xss')</script>` と入力した場合、
// エスケープしないと innerHTML に埋め込んだ時にスクリプトが実行される。
//
// React を使えば（Step 9 以降）、JSX が自動でエスケープするため不要になる。
//
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
