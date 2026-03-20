// =============================================================================
// Step 2: 構造化メッセージ — protocol.js（メッセージの組み立て・解析）
// =============================================================================
//
// 【このファイルの概要】
// WebSocket で送受信する JSON メッセージの組み立てと解析を行うモジュール。
// Go 側の protocol パッケージ（messages.go, codec.go）と対になる JavaScript 版。
//
// 【ES Modules とは？】
// JavaScript でコードをファイルに分割し、必要な部分だけ取り込む仕組み。
// - export: 他のファイルに公開する（このファイルで使う）
// - import: 他のファイルから取り込む（app.js で使う）
//
// <script type="module"> で読み込むと ES Modules が有効になる。
// 通常の <script> では export/import が使えない。
//
// 【なぜファイルを分けるの？（Step 1 からの進化）】
// Step 1 では全てを index.html の <script> タグに書いていました。
// Step 2 ではファイルを分割して「関心の分離（Separation of Concerns）」を実現。
//
// protocol.js — メッセージの構造に関するコード
// app.js      — UI操作やWebSocket接続に関するコード
//
// ファイルを分けるメリット:
// 1. 各ファイルの役割が明確になる
// 2. 変更の影響範囲が小さくなる（protocol を変えても UI コードに影響しない）
// 3. テストがしやすくなる
//
// =============================================================================

// =============================================================================
// メッセージタイプ定数
// =============================================================================
//
// 【Object.freeze() とは？】
// オブジェクトを「凍結」して、後から変更できなくする。
// Go の const に近い効果を持つ。
//
// 普通のオブジェクト: MessageType.VELOCITY_CMD = "hacked" → 変更できてしまう
// freeze したもの:    MessageType.VELOCITY_CMD = "hacked" → 無視される（変更されない）
//
// 【なぜ定数にするの？】
// "velocity_cmd" という文字列を直接使うと:
// - タイプミスに気づけない（"velociy_cmd" → バグ）
// - IDE の補完が効かない
// - 文字列を変更する時に全箇所を修正する必要がある
export const MessageType = Object.freeze({
  VELOCITY_CMD: "velocity_cmd",   // クライアント → サーバー: 速度コマンド
  SENSOR_DATA: "sensor_data",     // サーバー → クライアント: センサーデータ
  COMMAND_ACK: "command_ack",     // サーバー → クライアント: コマンド応答
  ERROR: "error",                 // サーバー → クライアント: エラー
});

// =============================================================================
// デフォルト設定
// =============================================================================
const DEFAULT_ROBOT_ID = "robot-01";

// =============================================================================
// createVelocityCmd — velocity_cmd メッセージを作成
// =============================================================================
//
// 【関数の設計思想】
// Go 側の protocol.NewVelocityCmd() と同じ構造のメッセージを作る。
// クライアントとサーバーで同じメッセージ構造を使うことで、
// 双方のコードが対称的になり、理解しやすくなる。
//
// 【デフォルト引数（= 値）とは？】
// 関数呼び出し時に引数を省略した場合に使われる値。
// createVelocityCmd(0.5) → linearY は 0, angularZ は 0 になる。
// Python のデフォルト引数、Go の ... に似た概念。
//
// 【引数の意味】
// linearX  — 前後方向の速度 (正: 前進, 負: 後退)
// linearY  — 左右方向の速度 (正: 左, 負: 右)
// angularZ — 回転速度 (正: 左旋回, 負: 右旋回)
export function createVelocityCmd(linearX = 0, linearY = 0, angularZ = 0) {
  return {
    type: MessageType.VELOCITY_CMD,
    robot_id: DEFAULT_ROBOT_ID,
    timestamp: new Date().toISOString(),
    payload: {
      linear_x: linearX,
      linear_y: linearY,
      angular_z: angularZ,
    },
  };
}

// =============================================================================
// encodeMessage — メッセージを JSON 文字列に変換（エンコード）
// =============================================================================
//
// 【JSON.stringify() とは？】
// JavaScript のオブジェクトを JSON 文字列に変換する関数。
// Go の json.Marshal() に相当。
//
// 例:
//   const obj = { type: "velocity_cmd", payload: { linear_x: 0.5 } };
//   JSON.stringify(obj)
//   → '{"type":"velocity_cmd","payload":{"linear_x":0.5}}'
//
// 第2引数: replacer（変換フィルター）— null で全フィールド
// 第3引数: space（インデント）— 省略すると1行、2 にすると見やすく整形
export function encodeMessage(msg) {
  return JSON.stringify(msg);
}

// =============================================================================
// decodeMessage — JSON 文字列をメッセージオブジェクトに変換（デコード）
// =============================================================================
//
// 【JSON.parse() とは？】
// JSON 文字列を JavaScript のオブジェクトに変換する関数。
// Go の json.Unmarshal() に相当。
//
// 【try-catch とは？】
// エラーが発生する可能性のあるコードを安全に実行する構文。
// Go の if err != nil パターンに相当。
//
// try {
//   // エラーが起きるかもしれないコード
// } catch (error) {
//   // エラーが起きた時の処理
// }
//
// 【なぜ try-catch が必要？】
// JSON.parse() に不正な文字列を渡すと例外（SyntaxError）が発生する。
// 例: JSON.parse("not json") → SyntaxError
// try-catch で囲まないと、プログラムがクラッシュ（停止）する。
export function decodeMessage(jsonString) {
  try {
    const msg = JSON.parse(jsonString);

    // --- バリデーション（検証） ---
    // 受信したデータが正しい形式かチェックする。
    //
    // 【なぜバリデーションが必要？】
    // ネットワークから来るデータは信頼できない。
    // 不正なデータがアプリに影響しないよう、入口でチェックする。
    // これを「入力バリデーション」と呼ぶ。
    if (!msg.type) {
      console.warn("⚠️ メッセージに type フィールドがありません:", msg);
      return null;
    }

    return msg;
  } catch (error) {
    console.error("JSON パースエラー:", error.message);
    return null;
  }
}

// =============================================================================
// formatSensorData — センサーデータを表示用文字列に変換
// =============================================================================
//
// 【テンプレートリテラル `...` 】
// バッククォート(`)で囲むと ${式} で値を埋め込める。
// 通常の '...' や "..." では変数を埋め込めない。
//
// 【.toFixed(n) とは？】
// 数値を小数点以下n桁の文字列に変換するメソッド。
// Go の fmt.Sprintf("%.1f", value) に相当。
// 例: (23.456).toFixed(1) → "23.5"
export function formatSensorData(payload) {
  return {
    temperature: `${payload.temperature.toFixed(1)}°C`,
    battery: `${payload.battery.toFixed(0)}%`,
    speed: `${payload.speed.toFixed(2)} m/s`,
    distance: `${payload.distance.toFixed(1)} m`,
  };
}

// =============================================================================
// WASD キーマッピング
// =============================================================================
//
// 【キーマッピングとは？】
// キーボードのキーとロボットの動作を対応付けるテーブル。
// ゲームでよく使われる WASD 配置:
//
//          W (前進)
//          ▲
//    A ◄  S  ► D
//   (左)  ▼  (右)
//       (後退)
//
// 【Map オブジェクトとは？】
// キーと値のペアを格納するデータ構造。
// 通常のオブジェクト {} と似ているが、以下の利点がある:
// - キーに任意の型を使える（オブジェクトは文字列のみ）
// - .size プロパティでエントリ数を取得できる
// - イテレーション（繰り返し処理）が簡単
// ここではシンプルなので通常のオブジェクトでも良いが、
// Map を使う練習として採用。
export const KeyBindings = new Map([
  // [キー名, { 速度パラメータ, 表示名 }]
  ["w", { linearX: 0.5, linearY: 0, angularZ: 0, label: "⬆ 前進" }],
  ["s", { linearX: -0.5, linearY: 0, angularZ: 0, label: "⬇ 後退" }],
  ["a", { linearX: 0, linearY: 0, angularZ: 0.5, label: "↺ 左旋回" }],
  ["d", { linearX: 0, linearY: 0, angularZ: -0.5, label: "↻ 右旋回" }],
  [" ", { linearX: 0, linearY: 0, angularZ: 0, label: "⏹ 停止" }],  // スペースキー
]);
