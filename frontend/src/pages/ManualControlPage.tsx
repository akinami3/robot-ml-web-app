/**
 * ============================================================================
 * ManualControlPage.tsx - 手動制御ページコンポーネント
 * ============================================================================
 *
 * 【ファイルの概要】
 * ロボットを手動で操縦するためのページです。
 * ジョイスティック操作やキーボード操作でロボットに速度コマンドを送信し、
 * リアルタイムにロボットを動かすことができます。
 *
 * 【このページの役割】
 * 1. 仮想ジョイスティックでロボットを操作する
 * 2. キーボード（WASD/矢印キー）でロボットを操作する
 * 3. 現在の速度コマンドをリアルタイムに表示する
 * 4. 緊急停止（E-Stop）ボタンでロボットを即座に停止する
 *
 * 【使われているデザインパターン】
 * - useCallback: 関数の再生成を防ぐメモ化パターン
 * - WebSocket通信: リアルタイムでロボットにコマンドを送信
 * - カスタムフック: useKeyboardControl, useWebSocket で複雑なロジックを分離
 * - 権限チェック: canControl()でユーザーの操作権限を確認
 * - 制御の無効化: disabled フラグで不適切な操作を防止
 *
 * 【ロボット制御の仕組み】
 * ユーザー操作（ジョイスティック/キーボード）
 *   ↓
 * 速度コマンド生成（linear_x, linear_y, angular_z）
 *   ↓
 * WebSocket経由でサーバーに送信
 *   ↓
 * サーバーがロボットアダプターに転送
 *   ↓
 * ロボットが動く
 *
 * 【速度の3軸について】
 * - linear_x (前進/後退): 正の値 = 前進、負の値 = 後退
 * - linear_y (左右移動): このロボットでは通常0
 * - angular_z (回転): 正の値 = 左回転、負の値 = 右回転
 *
 * 【画面構成】
 * ┌───────────────────────────────────────────┐
 * │ Manual Control（タイトル）                   │
 * │ [ロボット未選択時の警告メッセージ]             │
 * │                                           │
 * │ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
 * │ │ Joystick │ │ Velocity │ │  E-Stop  │    │
 * │ │   🕹️    │ │ X: 0.300 │ │   🛑     │    │
 * │ │          │ │ Y: 0.000 │ │          │    │
 * │ │ ☑ WASD  │ │ Z: 0.000 │ │          │    │
 * │ └──────────┘ └──────────┘ └──────────┘    │
 * │                                           │
 * │ Keyboard shortcuts: W/↑ Forward ...       │
 * └───────────────────────────────────────────┘
 */

// =============================================================================
// インポート部分
// =============================================================================

/**
 * useCallback - 関数をメモ化（キャッシュ）するフック
 * 依存配列の値が変わらない限り、同じ関数インスタンスを再利用します。
 *
 * 【なぜ必要？】
 * Reactでは、コンポーネントが再描画されるたびに内部の関数が新しく作り直されます。
 * これは通常問題ありませんが、以下の場合にパフォーマンス問題が発生:
 *   1. 関数を子コンポーネントにpropsとして渡す場合 → 不要な再描画が起きる
 *   2. 関数をuseEffectの依存配列に含める場合 → 無限ループの危険
 * useCallbackで関数をメモ化すると、同じ関数参照を保持するため、これらを防げます。
 *
 * useState - 状態管理フック（キーボード有効/無効の切り替え用）
 */
import { useCallback, useState } from "react";

/**
 * UIコンポーネント
 * Card系 - カードレイアウト（ジョイスティック、速度表示、E-Stop用）
 */
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

/**
 * EStopButton - 緊急停止ボタンコンポーネント
 * 赤い大きなボタンで、ロボットを即座に停止させます。
 *
 * 【E-Stop（Emergency Stop）とは？】
 * 「緊急停止」の意味で、ロボット工学の重要な安全機能です。
 * E-Stopが押されると、ロボットは全ての動作を即座に停止します。
 * 物理的なロボットには必ずE-Stopボタンが付いています。
 */
import { EStopButton } from "@/components/robot/EStopButton";

/**
 * JoystickController - 仮想ジョイスティックコンポーネント
 * 画面上にタッチ/ドラッグ操作可能なジョイスティックを表示します。
 * ジョイスティックの傾きに応じて速度コマンドを生成します。
 */
import { JoystickController } from "@/components/robot/JoystickController";

/**
 * useWebSocket - WebSocket通信用のカスタムフック
 * リアルタイム通信（速度コマンド送信、E-Stop制御）を行います。
 *
 * 【WebSocketとは？】
 * 通常のHTTP通信は「リクエスト→レスポンス」の一方向ですが、
 * WebSocketは双方向のリアルタイム通信を可能にします。
 * ロボット制御のように大量のコマンドを高頻度で送る場合に適しています。
 *
 * 【HTTPとの違い】
 * HTTP: 毎回接続→送信→応答→切断（オーバーヘッドが大きい）
 * WebSocket: 一度接続すると、常に繋がったまま高速にデータをやり取りできる
 */
import { useWebSocket } from "@/hooks/useWebSocket";

/**
 * useKeyboardControl - キーボード操作用のカスタムフック
 * WASD や矢印キーの押下を検知し、対応するロボット操作を呼び出します。
 *
 * 【カスタムフックとは？】
 * 独自に作成したReactフックです。「use」で始まる関数がフックです。
 * 複雑なロジック（キーボードイベントの監視・解除など）を
 * コンポーネントから切り離してスッキリさせるために使います。
 */
import { useKeyboardControl } from "@/hooks/useKeyboardControl";

/**
 * useRobotStore - ロボット状態管理（選択中のロボットID、E-Stop状態、最後のコマンド）
 * useAuthStore - 認証状態管理（ユーザーの操作権限チェック用）
 */
import { useRobotStore } from "@/stores/robotStore";
import { useAuthStore } from "@/stores/authStore";

// =============================================================================
// 定数
// =============================================================================

/**
 * 速度定数
 * ロボットに送信する速度の大きさを定義します。
 *
 * LINEAR_SPEED = 0.3 (m/s) - 直進速度（毎秒0.3メートル）
 * ANGULAR_SPEED = 0.8 (rad/s) - 回転速度（毎秒0.8ラジアン）
 *
 * 【なぜ定数として定義？】
 * マジックナンバー（意味不明な数字）をコード内に直接書くのは悪い習慣です。
 * 定数にすることで:
 *   1. 数値の意味が明確になる
 *   2. 値を変更する際に1箇所の修正で済む
 *   3. 他の開発者が理解しやすい
 *
 * 【constの意味】
 * const は「再代入不可」の変数宣言です。定数として使う場合はconstを使います。
 * 大文字+アンダースコア（UPPER_SNAKE_CASE）は「定数」であることを示す命名規約です。
 */
const LINEAR_SPEED = 0.3;
const ANGULAR_SPEED = 0.8;

// =============================================================================
// ManualControlPageコンポーネント
// =============================================================================

/**
 * ManualControlPage - 手動制御ページのメインコンポーネント
 *
 * 【安全設計のポイント】
 * 1. ロボット未選択時は操作不能（disabled）
 * 2. E-Stop中は操作不能
 * 3. 権限がないユーザーは操作不能
 * 4. キーボード操作のON/OFF切替が可能
 */
export function ManualControlPage() {
  // ---------------------------------------------------------------------------
  // ストアからの状態・関数取得
  // ---------------------------------------------------------------------------

  /**
   * selectedRobotId - 現在選択されているロボットのID
   * ダッシュボードで選択したロボットのIDがここに入ります。
   * 未選択の場合はnull（何も選ばれていない状態）。
   */
  const selectedRobotId = useRobotStore((s) => s.selectedRobotId);

  /**
   * isEStopActive - 緊急停止が有効かどうか
   * trueの場合、全ての操作がブロックされます（安全のため）。
   */
  const isEStopActive = useRobotStore((s) => s.isEStopActive);

  /**
   * lastCommand - 最後に送信した速度コマンド
   * { linear_x, linear_y, angular_z } の形式で速度表示に使用します。
   */
  const lastCommand = useRobotStore((s) => s.lastCommand);

  /** setLastCommand - 最後のコマンドを更新する関数 */
  const setLastCommand = useRobotStore((s) => s.setLastCommand);

  /**
   * canControl - ユーザーがロボットを操作する権限があるか確認する関数
   * 例: 管理者（admin）は操作可能、閲覧専用ユーザー（viewer）は操作不可
   *
   * 【関数として取得する理由】
   * canControlは「呼び出すたびに現在の権限を確認する関数」です。
   * 値ではなく関数を取得することで、常に最新の権限状態を取得できます。
   */
  const canControl = useAuthStore((s) => s.canControlRobot);

  // ---------------------------------------------------------------------------
  // WebSocket通信
  // ---------------------------------------------------------------------------

  /**
   * useWebSocketフックから通信関数を取得（分割代入）
   *
   * sendVelocity - ロボットに速度コマンドを送信する関数
   *   sendVelocity(robotId, linear_x, linear_y, angular_z)
   *
   * sendEStop - 緊急停止を有効化する関数
   *   sendEStop(robotId)
   *
   * releaseEStop - 緊急停止を解除する関数
   *   releaseEStop(robotId)
   */
  const { sendVelocity, sendEStop, releaseEStop } = useWebSocket();

  // ---------------------------------------------------------------------------
  // ローカル状態
  // ---------------------------------------------------------------------------

  /** キーボード操作が有効かどうか（チェックボックスで切替可能） */
  const [keyboardEnabled, setKeyboardEnabled] = useState(true);

  // ---------------------------------------------------------------------------
  // 制御の無効化判定
  // ---------------------------------------------------------------------------

  /**
   * disabled - 操作を無効化するべきかのフラグ
   *
   * 以下のいずれかの条件でtrue（操作不可）になります:
   * 1. !selectedRobotId - ロボットが選択されていない
   * 2. isEStopActive - 緊急停止が有効
   * 3. !canControl() - ユーザーに操作権限がない
   *
   * 【|| (OR演算子) の意味】
   * どれか1つでもtrueなら、全体がtrueになります。
   * つまり、3つの安全条件のうち1つでも該当すれば操作を無効にします。
   */
  const disabled = !selectedRobotId || isEStopActive || !canControl();

  // ---------------------------------------------------------------------------
  // コールバック関数（メモ化済み）
  // ---------------------------------------------------------------------------

  /**
   * move - ロボットを動かすコールバック関数
   *
   * @param lx - linear_x（前進/後退速度）
   * @param ly - linear_y（左右移動速度、通常0）
   * @param az - angular_z（回転速度）
   *
   * 【useCallbackの第2引数（依存配列）】
   * [disabled, selectedRobotId, sendVelocity, setLastCommand]
   * → これらの値が変わった時だけ、新しいmove関数が作成されます。
   *   値が変わらなければ、前回と同じ関数参照を再利用します。
   *
   * 【なぜuseCallbackが必要？】
   * move関数はJoystickControllerとuseKeyboardControlに渡されます。
   * 毎回新しい関数が作られると、これらのコンポーネント/フックが
   * 不要な再実行をしてしまいます。useCallbackで防止します。
   */
  const move = useCallback(
    (lx: number, ly: number, az: number) => {
      /** 操作が無効化されている場合は何もしない */
      if (disabled || !selectedRobotId) return;

      /** WebSocket経由でロボットに速度コマンドを送信 */
      sendVelocity(selectedRobotId, lx, ly, az);

      /** UIの速度表示を更新（Zustandストアに保存） */
      setLastCommand({ linear_x: lx, linear_y: ly, angular_z: az });
    },
    [disabled, selectedRobotId, sendVelocity, setLastCommand]
  );

  /**
   * stop - ロボットを停止するコールバック関数
   * 全ての速度を0にして、ロボットを停止させます。
   *
   * 【moveとstopを分ける理由】
   * 停止処理はdisabledチェックを行いません（E-Stop解除後の停止にも使うため）。
   * また、selectedRobotIdのチェックだけ行います。
   */
  const stop = useCallback(() => {
    if (!selectedRobotId) return;
    sendVelocity(selectedRobotId, 0, 0, 0);
    setLastCommand({ linear_x: 0, linear_y: 0, angular_z: 0 });
  }, [selectedRobotId, sendVelocity, setLastCommand]);

  // ---------------------------------------------------------------------------
  // キーボード操作の設定
  // ---------------------------------------------------------------------------

  /**
   * useKeyboardControl - キーボード操作を設定するカスタムフック
   *
   * 各キーに対応するコールバック関数を設定:
   * - W / ↑ → onForward（前進）
   * - S / ↓ → onBackward（後退）
   * - A / ← → onLeft（左回転）
   * - D / → → onRight（右回転）
   * - Space → onStop（停止）
   * - ESC → onEStop（緊急停止）
   *
   * enabled - キーボード操作を有効にするかどうか
   *   keyboardEnabled（チェックボックスの値）&& !disabled（操作可能状態）
   *   両方trueの場合にのみキーボード操作が有効になります。
   *
   * 【?? undefined の意味】
   * selectedRobotId ?? undefined は
   * 「selectedRobotIdがnullの場合はundefinedを使う」という意味です。
   * sendEStopがnullではなくundefinedを期待する場合の型変換です。
   */
  useKeyboardControl({
    onForward: () => move(LINEAR_SPEED, 0, 0),
    onBackward: () => move(-LINEAR_SPEED, 0, 0),
    onLeft: () => move(0, 0, ANGULAR_SPEED),
    onRight: () => move(0, 0, -ANGULAR_SPEED),
    onStop: stop,
    onEStop: () => sendEStop(selectedRobotId ?? undefined),
    enabled: keyboardEnabled && !disabled,
  });

  // ---------------------------------------------------------------------------
  // JSX（画面の描画部分）
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/** ページタイトル */}
      <h1 className="text-2xl font-bold">Manual Control</h1>

      {/**
       * 警告メッセージ - ロボット未選択時に表示
       *
       * {!selectedRobotId && (...)} は「短絡評価（Short-circuit evaluation）」です。
       * 左側がfalsy（null/undefined/false/0等）の場合、右側は評価されません。
       * 左側がtruthyの場合のみ、右側のJSXが描画されます。
       *
       * 【Tailwindクラスの説明】
       * border-yellow-300 - 黄色の枠線
       * bg-yellow-50 - 薄い黄色の背景
       * dark:... - ダークモード時のスタイル
       *   ダークモードでは黄色が濃い背景に変わり、読みやすくなります。
       */}
      {!selectedRobotId && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-200">
          Select a robot from the Dashboard first.
        </div>
      )}

      {/**
       * メインの3カラムグリッドレイアウト
       * grid gap-6 - CSSグリッド、間隔24px
       * lg:grid-cols-3 - PCサイズ以上で3列
       * モバイルでは1列、PCでは3列に自動調整されます。
       */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* ================================================================ */}
        {/* ジョイスティックカード                                              */}
        {/* ================================================================ */}
        {/**
         * lg:col-span-1 - 3列中1列分の幅を占める
         */}
        <Card className="lg:col-span-1">
          <CardHeader>
            {/** text-base - 基本フォントサイズ（16px） */}
            <CardTitle className="text-base">Joystick</CardTitle>
          </CardHeader>
          {/**
           * flex flex-col items-center gap-4
           * → 縦方向のFlexbox、要素を中央揃え、間隔16px
           */}
          <CardContent className="flex flex-col items-center gap-4">
            {/**
             * JoystickController - 仮想ジョイスティック
             *
             * onMove - ジョイスティック操作時のコールバック
             *   (lx, _ly, az) → lyは使わないので_lyと命名（慣例）
             *   move(lx, 0, az) → ly は常に0で呼び出す
             *
             * onStop - ジョイスティックリリース時のコールバック
             * disabled - 操作無効フラグ
             */}
            <JoystickController
              onMove={(lx, _ly, az) => move(lx, 0, az)}
              onStop={stop}
              disabled={disabled}
            />

            {/**
             * キーボード操作の有効/無効チェックボックス
             *
             * <input type="checkbox" /> - HTMLのチェックボックス
             * checked={keyboardEnabled} - チェック状態をstateと連動
             * onChange - チェック変更時にstateを更新
             *   e.target.checked でチェックされているかの真偽値を取得
             */}
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={keyboardEnabled}
                onChange={(e) => setKeyboardEnabled(e.target.checked)}
                className="rounded"
              />
              Keyboard (WASD / Arrows)
            </label>
          </CardContent>
        </Card>

        {/* ================================================================ */}
        {/* 速度表示カード                                                     */}
        {/* ================================================================ */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Velocity</CardTitle>
          </CardHeader>
          {/**
           * font-mono - 等幅フォント（数字の表示を揃えるため）
           * space-y-3 - バー間の間隔12px
           *
           * 【等幅フォントを使う理由】
           * 数値が変化しても桁数が同じなら表示幅が変わらず、値が読みやすくなります。
           */}
          <CardContent className="space-y-3 font-mono text-sm">
            {/**
             * VelocityBar - 速度をバーグラフで表示するサブコンポーネント
             *
             * lastCommand?.linear_x ?? 0
             * → ?.（オプショナルチェーン）: lastCommandがnullの場合はundefined
             * → ??（nullish coalescing）: undefinedの場合は0を使う
             * つまり「lastCommandが存在すればlinear_xを、なければ0を表示」
             */}
            <VelocityBar label="Linear X" value={lastCommand?.linear_x ?? 0} max={1} />
            <VelocityBar label="Linear Y" value={lastCommand?.linear_y ?? 0} max={1} />
            <VelocityBar label="Angular Z" value={lastCommand?.angular_z ?? 0} max={2} />
          </CardContent>
        </Card>

        {/* ================================================================ */}
        {/* 緊急停止（E-Stop）カード                                          */}
        {/* ================================================================ */}
        {/**
         * flex items-center justify-center - カード内を中央揃え（E-Stopボタンを中央に配置）
         */}
        <Card className="flex items-center justify-center lg:col-span-1">
          <CardContent className="py-8">
            {/**
             * EStopButton - 緊急停止ボタンコンポーネント
             *
             * robotId - 対象のロボットID
             *   selectedRobotId ?? undefined でnull→undefinedに変換
             * onActivate - 緊急停止を有効化するコールバック
             * onRelease - 緊急停止を解除するコールバック
             */}
            <EStopButton
              robotId={selectedRobotId ?? undefined}
              onActivate={sendEStop}
              onRelease={releaseEStop}
            />
          </CardContent>
        </Card>
      </div>

      {/**
       * キーボードショートカットのヘルプテキスト
       *
       * text-xs - 小さいフォント
       * text-muted-foreground - 薄い色（目立たないヒント表示）
       * <strong> - 太字
       *
       * 【UXの配慮】
       * キーボードショートカットは便利ですが、知らないと使えません。
       * 画面下部にヘルプテキストを表示して、使い方を案内します。
       */}
      <div className="rounded-md border p-3 text-xs text-muted-foreground">
        <strong>Keyboard shortcuts:</strong> W/↑ Forward · S/↓ Backward · A/← Turn Left · D/→ Turn Right · Space Stop · ESC Emergency Stop
      </div>
    </div>
  );
}

// =============================================================================
// VelocityBar サブコンポーネント
// =============================================================================

/**
 * VelocityBar - 速度値を水平バーグラフで表示するコンポーネント
 *
 * 【仕組み】
 * 速度値を棒グラフとして視覚化します。
 * 中央が0で、正の値は右方向、負の値は左方向にバーが伸びます。
 *
 * 【表示例】
 *           -1.0         0         +1.0
 *            |           |           |
 * 正の値:    [           |████      ]  → 右方向にバー
 * 負の値:    [      ████|           ]  → 左方向にバー
 *
 * @param label - バーのラベル（"Linear X", "Angular Z" など）
 * @param value - 現在の速度値
 * @param max - 最大値（バーの100%に相当する値）
 */
function VelocityBar({ label, value, max }: { label: string; value: number; max: number }) {
  /**
   * pct - バーの長さをパーセンテージで計算
   * Math.abs(value) - 絶対値（正負に関わらず大きさだけ取得）
   * / max - 最大値で割って0〜1の範囲に正規化
   * * 100 - パーセンテージに変換
   *
   * 例: value=0.3, max=1 → (0.3/1)*100 = 30%
   */
  const pct = (Math.abs(value) / max) * 100;

  /** isNegative - 値が負（後退や右回転）かどうか */
  const isNegative = value < 0;

  return (
    <div>
      {/**
       * ラベルと数値の表示
       * flex justify-between - 左にラベル、右に数値を配置
       * .toFixed(3) - 小数点以下3桁まで表示（例: 0.300）
       */}
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span>{value.toFixed(3)}</span>
      </div>

      {/**
       * 正の値用のバー（右半分）
       *
       * 【構造】
       * [左半分（空）| 右半分（バー表示エリア） ]
       *
       * w-1/2 - 幅50%
       * relative - 子要素の位置決めの基準点を設定
       * absolute left-0 - 左端からバーを伸ばす
       * rounded-r-full - 右端だけ丸く
       * bg-primary - プライマリカラーの背景
       * transition-all - 値変化時にアニメーションする
       *
       * style={{ width: `${pct}%` }} - バーの幅をパーセンテージで設定
       * → インラインスタイルを使う理由: Tailwindでは動的な数値をクラスにできないため
       */}
      <div className="mt-1 flex h-2 overflow-hidden rounded-full bg-muted">
        <div className="w-1/2" />
        <div className="relative w-1/2">
          {!isNegative && (
            <div
              className="absolute left-0 h-full rounded-r-full bg-primary transition-all"
              style={{ width: `${pct}%` }}
            />
          )}
        </div>
      </div>

      {/**
       * 負の値用のバー（左半分）
       *
       * 【構造（正のバーの逆方向）】
       * [左半分（バー表示エリア） | 右半分（空） ]
       *
       * absolute right-0 - 右端からバーを伸ばす（中央方向にバーが伸びる）
       * rounded-l-full - 左端だけ丸く
       *
       * marginTop: -8 - 正のバーの上に重ねて表示するためのマイナスマージン
       * これにより1つのバーのように見えますが、実際は2つのdivで構成されています。
       */}
      <div className="flex h-2 overflow-hidden rounded-full bg-muted" style={{ marginTop: -8 }}>
        <div className="relative w-1/2">
          {isNegative && (
            <div
              className="absolute right-0 h-full rounded-l-full bg-primary transition-all"
              style={{ width: `${pct}%` }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
