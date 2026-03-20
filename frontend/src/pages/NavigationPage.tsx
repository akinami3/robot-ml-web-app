/**
 * ============================================================================
 * NavigationPage.tsx - 自律ナビゲーションページコンポーネント
 * ============================================================================
 *
 * 【ファイルの概要】
 * ロボットの自律ナビゲーション（自動移動）を制御するページです。
 * 目標地点の座標（X, Y, θ）を入力して、ロボットに自動で移動させます。
 *
 * 【手動制御（ManualControlPage）との違い】
 * - ManualControlPage: ユーザーがリアルタイムに操縦する（ラジコン操作）
 * - NavigationPage: 目的地を指定して、ロボットが自律的に移動する
 *
 * 【このページの役割】
 * 1. 目標座標（X, Y, θ）の入力フォームを提供
 * 2. ナビゲーションゴールをWebSocket経由でサーバーに送信
 * 3. ナビゲーション状態（移動中/待機中）を表示
 * 4. 緊急停止（E-Stop）ボタンを提供
 * 5. 将来的にマップ表示を行うプレースホルダーを配置
 *
 * 【使われているデザインパターン】
 * - useCallback: ゴール送信関数のメモ化
 * - WebSocket通信: ナビゲーションゴールの送信
 * - 状態マシン: "idle" | "navigating" の2状態で管理
 * - フォーム制御: 座標入力の管理
 *
 * 【ナビゲーションの仕組み】
 * ユーザーが座標を入力して「Send Goal」ボタンをクリック
 *   ↓
 * WebSocket経由でサーバーにゴール座標を送信
 *   ↓
 * ロボットがパスプランニング（経路計画）を実行
 *   ↓
 * 障害物を回避しながら目標地点に自律移動
 *
 * 【座標系の説明】
 * X (m) - 前後方向の位置（メートル単位）
 * Y (m) - 左右方向の位置（メートル単位）
 * θ (rad) - ロボットの向き（ラジアン単位、0=正面、π/2=左向き）
 *
 * 【画面構成】
 * ┌───────────────────────────────────────────┐
 * │ Navigation（タイトル）                       │
 * │ [ロボット未選択時の警告]                       │
 * │                                           │
 * │ ┌──────────────────────┐ ┌──────────┐      │
 * │ │ 📍 Navigation Goal    │ │  E-Stop  │      │
 * │ │ X:[__] Y:[__] θ:[__] │ │   🛑     │      │
 * │ │ [Send Goal] [Cancel]  │ │          │      │
 * │ │ Navigating to (1,2,0) │ │          │      │
 * │ │ ┌─────────────────┐   │ │          │      │
 * │ │ │ Map (future)     │   │ │          │      │
 * │ │ └─────────────────┘   │ │          │      │
 * │ └──────────────────────┘ └──────────┘      │
 * └───────────────────────────────────────────┘
 */

// =============================================================================
// インポート部分
// =============================================================================

/**
 * useState - 状態管理フック
 *   このページでは4つの状態を管理:
 *   goalX, goalY, goalTheta（座標入力値）, navStatus（ナビゲーション状態）
 *
 * useCallback - 関数メモ化フック
 *   handleSendGoalの再生成を防ぐために使用
 *
 * 【useCallbackが重要な理由（このページの場合）】
 * handleSendGoalは入力値が変わるたびに再生成されますが、
 * useCallbackを使うことで、依存値が変わった場合のみ再生成されます。
 * これにより、不要な再描画を防ぎます。
 */
import { useState, useCallback } from "react";

/**
 * UIコンポーネント
 * Card系 - カードレイアウト
 * Button - ボタン（Send Goal, Cancel）
 * Input - 数値入力欄（X, Y, θ）
 */
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from "@/components/ui/primitives";

/**
 * EStopButton - 緊急停止ボタンコンポーネント
 * ナビゲーション中でも即座にロボットを停止できます。
 * 自律移動中は特に重要（ロボットが自分で動いているため）。
 */
import { EStopButton } from "@/components/robot/EStopButton";

/**
 * useWebSocket - WebSocket通信用カスタムフック
 * sendNavGoal - ナビゲーションゴールを送信する関数
 * sendEStop / releaseEStop - 緊急停止の有効化/解除
 */
import { useWebSocket } from "@/hooks/useWebSocket";

/**
 * useRobotStore - ロボット状態管理ストア
 * selectedRobotId - 現在選択されているロボットのID
 */
import { useRobotStore } from "@/stores/robotStore";

/**
 * lucide-reactアイコン
 * MapPin - 地図ピンアイコン（📍）ナビゲーションゴールのタイトルに使用
 * Navigation (NavIcon) - ナビゲーションアイコン（ボタンに使用）
 *   ※ ReactのNavigation名前空間と衝突するため、NavIconにリネーム
 * X - ×アイコン（キャンセルボタンに使用）
 *
 * 【asによるリネーム (Navigation as NavIcon)】
 * importする名前が既存の何かと衝突したり、わかりにくい場合に別名をつけます。
 * 「Navigation」はReact Routerでも使われる名前なので、NavIconに変更しています。
 */
import { MapPin, Navigation as NavIcon, X } from "lucide-react";

// =============================================================================
// NavigationPageコンポーネント
// =============================================================================

/**
 * NavigationPage - ナビゲーションページのメインコンポーネント
 *
 * 【ManualControlPageとの類似点と相違点】
 * 類似点:
 *   - ロボット選択チェック
 *   - E-Stopボタン
 *   - WebSocket通信
 *   - 警告メッセージ
 * 相違点:
 *   - ジョイスティック/キーボード → 座標入力フォーム
 *   - リアルタイム速度送信 → 1回のゴール送信
 *   - 速度バー表示 → ナビゲーション状態表示
 */
export function NavigationPage() {
  // ---------------------------------------------------------------------------
  // ストアからの状態取得
  // ---------------------------------------------------------------------------

  /** 選択中のロボットID（未選択ならnull） */
  const selectedRobotId = useRobotStore((s) => s.selectedRobotId);

  // ---------------------------------------------------------------------------
  // WebSocket通信関数の取得
  // ---------------------------------------------------------------------------

  /**
   * sendNavGoal - ナビゲーションゴールをサーバーに送信
   *   sendNavGoal(robotId, x, y, theta)
   * sendEStop - 緊急停止を有効化
   * releaseEStop - 緊急停止を解除
   */
  const { sendNavGoal, sendEStop, releaseEStop } = useWebSocket();

  // ---------------------------------------------------------------------------
  // 状態（State）の定義
  // ---------------------------------------------------------------------------

  /**
   * 目標座標の入力値
   *
   * 【なぜ数値ではなく文字列?】
   * HTMLの<input type="number">のvalueは文字列です。
   * "0.5"のような入力途中の値を正しく扱うため、文字列で管理し、
   * 送信時にparseFloat()で数値に変換します。
   *
   * 例: ユーザーが「1.」と入力中 → 文字列なら"1."として保持可能
   *     数値にすると1になってしまい、小数点が消えてしまいます。
   */
  const [goalX, setGoalX] = useState("0");         // X座標（メートル）
  const [goalY, setGoalY] = useState("0");         // Y座標（メートル）
  const [goalTheta, setGoalTheta] = useState("0"); // θ角度（ラジアン）

  /**
   * ナビゲーション状態（状態マシン）
   *
   * 【ユニオン型 "idle" | "navigating" とは？】
   * TypeScriptのリテラル型のユニオン（合併型）です。
   * navStatus は "idle" か "navigating" のどちらかしか取れません。
   * 文字列ならなんでもOKの string 型と違い、間違った値を代入するとエラーになります。
   *
   * "idle" - 待機中（ゴール未送信、またはキャンセル後）
   * "navigating" - ナビゲーション中（ゴール送信後）
   *
   * 【状態マシン（State Machine）パターンとは？】
   * システムの状態を「有限個の状態のどれか」として管理するパターンです。
   * 状態が明確になり、不正な状態遷移を防げます。
   *   idle → navigating（ゴール送信時）
   *   navigating → idle（キャンセル時）
   */
  const [navStatus, setNavStatus] = useState<"idle" | "navigating">("idle");

  // ---------------------------------------------------------------------------
  // コールバック関数
  // ---------------------------------------------------------------------------

  /**
   * handleSendGoal - 「Send Goal」ボタンクリック時の処理
   *
   * 1. ロボット未選択ならreturnで中断
   * 2. 文字列の座標値を数値に変換（parseFloat）
   * 3. WebSocket経由でゴールを送信
   * 4. 状態を "navigating" に変更
   *
   * 【parseFloat()とは？】
   * 文字列を浮動小数点数（float）に変換する組み込み関数です。
   * "1.5" → 1.5, "0" → 0, "abc" → NaN（Not a Number）
   *
   * 【useCallbackの依存配列】
   * [selectedRobotId, goalX, goalY, goalTheta, sendNavGoal]
   * → これらの値が変わった場合のみ、新しい関数が作成されます。
   *   座標値が変わるたびに再生成されますが、Buttonに渡すために必要です。
   */
  const handleSendGoal = useCallback(() => {
    if (!selectedRobotId) return;
    sendNavGoal(selectedRobotId, parseFloat(goalX), parseFloat(goalY), parseFloat(goalTheta));
    setNavStatus("navigating");
  }, [selectedRobotId, goalX, goalY, goalTheta, sendNavGoal]);

  // ---------------------------------------------------------------------------
  // JSX（画面の描画部分）
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/** ページタイトル */}
      <h1 className="text-2xl font-bold">Navigation</h1>

      {/**
       * 警告メッセージ（ロボット未選択時）
       * ManualControlPageと同じパターンの条件付きレンダリング
       */}
      {!selectedRobotId && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-200">
          Select a robot from the Dashboard first.
        </div>
      )}

      {/**
       * 2カラムグリッドレイアウト
       * lg:grid-cols-3 - 3列グリッド（ゴール設定=2列分、E-Stop=1列分）
       */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* ================================================================ */}
        {/* ナビゲーションゴール設定カード                                       */}
        {/* ================================================================ */}
        {/**
         * lg:col-span-2 - 3列中2列分の幅を使用（ゴール設定は広めに配置）
         */}
        <Card className="lg:col-span-2">
          <CardHeader>
            {/**
             * タイトルにアイコンとテキストを横並びで配置
             * flex items-center gap-2 - 横並び、中央揃え、間隔8px
             */}
            <CardTitle className="flex items-center gap-2 text-base">
              {/** MapPinアイコン（📍） h-4 w-4 = 16x16px */}
              <MapPin className="h-4 w-4" />
              Navigation Goal
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {/**
             * 座標入力欄（3列グリッド: X, Y, θ）
             * grid grid-cols-3 gap-3 - 3列グリッド、間隔12px
             */}
            <div className="grid grid-cols-3 gap-3">
              {/**
               * X座標入力欄
               * type="number" - 数値入力モード（上下矢印で増減可能）
               * step="0.1" - 矢印クリック時の増減量（0.1メートル刻み）
               *
               * 【labelとLabelの違い】
               * ここでは小文字のlabel（HTML標準要素）を使っています。
               * 見た目が少し違うだけで、基本的な機能は同じです。
               */}
              <div>
                <label className="text-xs text-muted-foreground">X (m)</label>
                <Input type="number" step="0.1" value={goalX} onChange={(e) => setGoalX(e.target.value)} />
              </div>

              {/** Y座標入力欄 */}
              <div>
                <label className="text-xs text-muted-foreground">Y (m)</label>
                <Input type="number" step="0.1" value={goalY} onChange={(e) => setGoalY(e.target.value)} />
              </div>

              {/**
               * θ（シータ）入力欄 - ロボットの目標向き
               * 【ラジアンとは？】
               * 角度の単位。360度 = 2π ≈ 6.28 ラジアン
               * π/2 ≈ 1.57 が90度に相当します。
               */}
              <div>
                <label className="text-xs text-muted-foreground">θ (rad)</label>
                <Input type="number" step="0.1" value={goalTheta} onChange={(e) => setGoalTheta(e.target.value)} />
              </div>
            </div>

            {/**
             * アクションボタン群
             * flex gap-3 - 横並び、間隔12px
             */}
            <div className="flex gap-3">
              {/**
               * Send Goalボタン
               * onClick={handleSendGoal} - クリック時にゴール送信
               * disabled={!selectedRobotId} - ロボット未選択時は無効化
               * gap-2 - アイコンとテキストの間隔8px
               */}
              <Button onClick={handleSendGoal} disabled={!selectedRobotId} className="gap-2">
                {/** NavIcon - ナビゲーションアイコン */}
                <NavIcon className="h-4 w-4" />
                Send Goal
              </Button>

              {/**
               * キャンセルボタン（ナビゲーション中のみ表示）
               *
               * {navStatus === "navigating" && (...)} → 条件付きレンダリング
               *
               * variant="outline" - 外枠だけのスタイル（副次的なアクション用）
               *   → メインアクション（Send Goal）と視覚的に区別するため
               *
               * onClick={() => setNavStatus("idle")} - 状態を "idle" に戻す
               *   ※ 現時点ではサーバーにキャンセルコマンドは送信していません
               *     （将来的に実装する予定の箇所）
               */}
              {navStatus === "navigating" && (
                <Button variant="outline" onClick={() => setNavStatus("idle")} className="gap-2">
                  {/** X（×）アイコン */}
                  <X className="h-4 w-4" />
                  Cancel
                </Button>
              )}
            </div>

            {/**
             * ナビゲーション中のステータス表示
             * ナビゲーション中にのみ表示される青い情報ボックス
             *
             * bg-blue-50 - 薄い青色の背景
             * text-blue-800 - 濃い青色のテキスト
             * dark:... - ダークモード時のスタイル
             *
             * ({goalX}, {goalY}, {goalTheta})...
             * → テンプレートリテラル的に変数を埋め込んで座標を表示
             */}
            {navStatus === "navigating" && (
              <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-200">
                Navigating to ({goalX}, {goalY}, {goalTheta})...
              </div>
            )}

            {/* ============================================================ */}
            {/* マッププレースホルダー（将来実装予定）                           */}
            {/* ============================================================ */}
            {/**
             * 将来的にマップ（地図）を表示するための空きスペース
             *
             * h-64 - 高さ256px
             * border-2 border-dashed - 太い破線の枠線
             * border-muted-foreground/20 - 薄い色の枠線（20%透明度）
             *
             * 【プレースホルダーパターン】
             * まだ実装されていない機能の場所を「ここに将来表示されます」と
             * 示しておくUIパターンです。開発中の画面でよく使われます。
             * これにより、レイアウト全体のイメージを事前に確認できます。
             */}
            <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20">
              <p className="text-sm text-muted-foreground">Map visualization (future)</p>
            </div>
          </CardContent>
        </Card>

        {/* ================================================================ */}
        {/* 緊急停止（E-Stop）カード                                          */}
        {/* ================================================================ */}
        {/**
         * ManualControlPageと同じE-Stopカード
         *
         * 【なぜナビゲーションページにもE-Stopがある？】
         * 自律ナビゲーション中もロボットは動き続けるため、
         * 緊急時にすぐ止められることが安全上重要です。
         * 特に自律移動はユーザーが直接操作していないため、
         * 予期しない動きをする可能性があり、E-Stopは必須です。
         */}
        <Card className="flex items-center justify-center">
          <CardContent className="py-8">
            <EStopButton
              robotId={selectedRobotId ?? undefined}
              onActivate={sendEStop}
              onRelease={releaseEStop}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
