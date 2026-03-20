/**
 * ============================================================
 * EStopButton.tsx - 緊急停止（Emergency Stop）ボタンコンポーネント
 * ============================================================
 *
 * 【ファイルの概要】
 * このファイルは、ロボットの「緊急停止ボタン（E-Stop）」を実装しています。
 * 実際の産業用ロボットには必ず赤い緊急停止ボタンが付いていますが、
 * このコンポーネントはそのデジタル版です。
 *
 * 【緊急停止ボタンとは？】
 * ロボットが予期しない動作をしたとき、すべての動作を即座に停止させるボタンです。
 * 安全性において最も重要な機能の一つです。
 *
 * 【このボタンの動作】
 * 1. 通常状態：赤い丸いボタンに「E-STOP」と表示
 * 2. 押すと：緊急停止が有効になり、ボタンが脈動（パルス）アニメーション
 * 3. もう一度押すと：緊急停止が解除される
 *
 * 【アクセシビリティ（a11y）への配慮】
 * - role="switch" → ON/OFF を切り替えるスイッチとして認識される
 * - aria-checked → 現在の状態（ON/OFF）をスクリーンリーダーに伝える
 * - aria-label → ボタンの用途を説明する
 */

// -------------------------------------------------------
// インポート部分
// -------------------------------------------------------

/**
 * 【useRobotStore】ロボットの状態を管理するストア
 * ロボットの接続状態、センサーデータ、緊急停止状態などを
 * アプリ全体で共有するための Zustand ストアです。
 */
import { useRobotStore } from "@/stores/robotStore";

/**
 * 【cn ユーティリティ】
 * 複数のCSSクラスを条件付きで結合する関数。
 * 詳しくは Sidebar.tsx のコメントを参照してください。
 */
import { cn } from "@/lib/utils";

// -------------------------------------------------------
// 型定義（インターフェース）
// -------------------------------------------------------

/**
 * 【interface（インターフェース）とは？】
 * TypeScript で「オブジェクトの形」を定義する仕組みです。
 * このコンポーネントが受け取る props（プロパティ）の型を定義しています。
 *
 * 【なぜ型を定義するのか？】
 * 1. コードの自己文書化：何が渡せるか一目でわかる
 * 2. 型安全性：間違った型の値を渡すとエラーが出る（バグを防ぐ）
 * 3. エディタの補完：入力中に候補が表示される（開発効率アップ）
 *
 * 【各プロパティの説明】
 * - robotId?: string
 *   → "?" は「省略可能（Optional）」を意味する
 *   → 渡しても渡さなくてもよい。渡さない場合は undefined になる
 *   → 複数のロボットがある場合、どのロボットを停止するか指定する
 *
 * - onActivate: (robotId?: string) => void
 *   → 緊急停止を「有効にする」ときに呼ばれるコールバック関数
 *   → (robotId?: string) => void は「string型の引数を受け取り、何も返さない関数」の型
 *   → void = 「何も返さない」
 *
 * - onRelease: (robotId?: string) => void
 *   → 緊急停止を「解除する」ときに呼ばれるコールバック関数
 *
 * 【コールバック関数とは？】
 * 「あとで呼んでね」と渡す関数のことです。
 * 親コンポーネントが「停止ボタンが押されたらこの処理をしてね」と
 * 関数を渡し、このコンポーネントはボタンが押されたときに呼び出します。
 * これにより、親コンポーネントが実際の処理を制御できます。
 */
interface EStopButtonProps {
  robotId?: string;
  onActivate: (robotId?: string) => void;
  onRelease: (robotId?: string) => void;
}

// -------------------------------------------------------
// コンポーネント定義
// -------------------------------------------------------

/**
 * 【EStopButton コンポーネント】
 * 緊急停止ボタンの UI を描画する関数コンポーネントです。
 *
 * 【Props の分割代入】
 * { robotId, onActivate, onRelease } は引数の分割代入です。
 * EStopButtonProps 型のオブジェクトから3つのプロパティを取り出しています。
 *
 * ": EStopButtonProps" は TypeScript の型注釈で、
 * 「この引数は EStopButtonProps 型ですよ」と宣言しています。
 */
export function EStopButton({ robotId, onActivate, onRelease }: EStopButtonProps) {
  /**
   * 【緊急停止状態の取得】
   * useRobotStore から isEStopActive（緊急停止がアクティブか）を取得します。
   * (s) => s.isEStopActive はセレクター関数で、
   * ストアから isEStopActive の値だけを取り出しています。
   *
   * この値が変わると、コンポーネントが自動的に再レンダリングされ、
   * ボタンの見た目が切り替わります。
   */
  const isActive = useRobotStore((s) => s.isEStopActive);

  return (
    /**
     * 【外側のコンテナ】
     * ボタンとテキストを縦に並べるための div です。
     * - "flex flex-col" → 縦方向に並べる
     * - "items-center"  → 中央揃え
     * - "gap-2"         → 子要素間に余白 0.5rem（8px）
     */
    <div className="flex flex-col items-center gap-2">
      {/**
       * 【緊急停止ボタン本体】
       *
       * onClick={...}
       * → 三項演算子を使って、状態に応じて呼ぶ関数を切り替えています
       * → isActive が true なら onRelease（解除）を呼ぶ
       * → isActive が false なら onActivate（有効化）を呼ぶ
       * → robotId を引数として渡す（どのロボットを停止するか）
       *
       * 【cn() による複雑なスタイル切り替え】
       * ボタンのスタイルを3つのグループに分けて管理しています：
       *
       * 1. 共通スタイル（常に適用）：
       *    - "relative"       → 位置の基準点にする
       *    - "h-24 w-24"      → 幅・高さ 6rem（96px）の丸い大きなボタン
       *    - "rounded-full"   → 完全な円形にする
       *    - "border-4"       → 太い枠線
       *    - "font-bold"      → 太字
       *    - "text-white"     → 白い文字
       *    - "text-sm"        → フォントサイズ小
       *    - "uppercase"      → 大文字変換
       *    - "tracking-wider" → 文字間隔を広げる
       *    - "shadow-lg"      → 大きな影（3D効果）
       *    - "transition-all" → すべてのプロパティの変化をアニメーション
       *
       * 2. フォーカス時のスタイル（Tab キーでフォーカスしたとき）：
       *    - "focus-visible:outline-none"         → デフォルトのアウトラインを消す
       *    - "focus-visible:ring-4"               → 太いリング（輪）を表示
       *    - "focus-visible:ring-yellow-400"       → 黄色のリング
       *    → キーボード操作のユーザーが「今ここにフォーカスがある」とわかる
       *    → これはアクセシビリティの重要な要素です
       *
       * 3. 状態別スタイル（isActive に応じて切り替え）：
       *    アクティブ時：
       *    - "animate-estop-pulse" → 脈動するカスタムアニメーション
       *    - "border-red-800"     → 暗い赤の枠線
       *    - "bg-red-600"         → 赤い背景
       *    - "hover:bg-red-700"   → ホバー時にさらに暗い赤
       *
       *    非アクティブ時：
       *    - "border-red-700"     → やや暗い赤の枠線
       *    - "bg-red-500"         → 通常の赤い背景
       *    - "hover:bg-red-600"   → ホバー時にやや暗い赤
       *    - "hover:scale-105"    → ホバー時に少し大きくなる（105%）
       *    - "active:scale-95"    → クリック中に少し小さくなる（95%）
       *    → scale の変化で「押せるボタン」だと視覚的に伝えます
       */}
      <button
        onClick={() => (isActive ? onRelease(robotId) : onActivate(robotId))}
        className={cn(
          "relative h-24 w-24 rounded-full border-4 font-bold text-white text-sm uppercase tracking-wider shadow-lg transition-all",
          "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-yellow-400",
          isActive
            ? "animate-estop-pulse border-red-800 bg-red-600 hover:bg-red-700"
            : "border-red-700 bg-red-500 hover:bg-red-600 hover:scale-105 active:scale-95"
        )}
        /**
         * 【aria-label - アクセシビリティのラベル】
         * ボタンの現在の状態に応じて、スクリーンリーダーに伝えるラベルを切り替えます。
         * 視覚障害のあるユーザーにも、ボタンの用途が明確に伝わります。
         */
        aria-label={isActive ? "Release Emergency Stop" : "Activate Emergency Stop"}
        /**
         * 【role="switch" と aria-checked】
         * role="switch" → このボタンがON/OFF切り替えスイッチであることを宣言
         * aria-checked → 現在の状態（ON=true / OFF=false）を伝える
         *
         * これにより、スクリーンリーダーは
         * 「緊急停止スイッチ、現在オン」のように読み上げます。
         */
        role="switch"
        aria-checked={isActive}
      >
        {/**
         * 【ボタンのテキスト】
         * isActive の状態に応じてテキストを切り替えます。
         * - アクティブ時："RELEASE"（解除してください）
         * - 非アクティブ時："E-STOP"（緊急停止）
         *
         * "leading-tight" → 行の高さを狭くして、ボタン内のテキストを収める
         */}
        <span className="block leading-tight">
          {isActive ? "RELEASE" : "E-STOP"}
        </span>
      </button>

      {/**
       * 【状態説明テキスト】
       * ボタンの下に表示される補助テキストです。
       * 現在の状態と操作方法をユーザーに知らせます。
       *
       * - "text-xs"              → とても小さいフォントサイズ
       * - "text-muted-foreground" → 控えめな色（グレー系）
       */}
      <span className="text-xs text-muted-foreground">
        {isActive ? "Emergency stop active" : "Press ESC or click"}
      </span>
    </div>
  );
}
