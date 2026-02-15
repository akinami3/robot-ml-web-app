/**
 * ============================================================
 * JoystickController.tsx - バーチャルジョイスティック操作コンポーネント
 * ============================================================
 *
 * 【ファイルの概要】
 * このファイルは、画面上に表示される仮想ジョイスティックを実装しています。
 * ユーザーがジョイスティックをドラッグすると、ロボットに移動コマンドが送信されます。
 *
 * 【ジョイスティックとは？】
 * ゲームコントローラーのスティックのような操作デバイスです。
 * ここでは画面上にタッチ/マウス操作可能な円形のコントローラーを表示し、
 * ドラッグの方向と距離に応じてロボットの速度を制御します。
 *
 * 【nipplejs ライブラリ】
 * nipplejs（ニップルJS）は、ブラウザ上でバーチャルジョイスティックを
 * 実現するためのオープンソースのJavaScriptライブラリです。
 * タッチデバイスでもマウスでも動作します。
 *
 * 【ロボットの移動コマンドの仕組み】
 * ロボットの速度は3つの値で表されます：
 * - linear_x : 前後方向の速度（正=前進、負=後退）
 * - linear_y : 左右方向の速度（通常は0、横移動できるロボットで使用）
 * - angular_z: 回転速度（正=左回転、負=右回転）
 *
 * ジョイスティックのドラッグ方向と距離を、これらの値に変換します。
 */

// -------------------------------------------------------
// インポート部分
// -------------------------------------------------------

/**
 * 【React フック（Hooks）のインポート】
 *
 * useEffect:
 *   コンポーネントの「副作用（side effect）」を管理するフックです。
 *   副作用 = 描画以外の処理（API呼び出し、DOM操作、タイマーなど）。
 *   ここでは nipplejs のジョイスティックの作成と破棄に使います。
 *
 * useRef:
 *   DOM要素やミュータブルな値への「参照」を保持するフックです。
 *   useState と違い、値が変わっても再レンダリングが発生しません。
 *
 *   【useRef の2つの用途】
 *   1. DOM要素への参照：<div ref={containerRef}> でDOM要素にアクセス
 *      → nipplejs がジョイスティックを描画するDOM要素を指定するために必要
 *   2. ミュータブルな値の保持：レンダリング間で値を保持したいが再描画は不要な場合
 *      → managerRef で nipplejs のインスタンスを保持
 *
 * useCallback:
 *   関数を「メモ化（memoize）」するフックです。
 *   依存配列の値が変わらない限り、同じ関数の参照を返します。
 *
 *   【なぜ useCallback が必要なのか？】
 *   React はコンポーネントが再レンダリングされるたびに関数を新しく作り直します。
 *   useEffect の依存配列に関数がある場合、毎回新しい関数と見なされて
 *   useEffect が無限に実行されてしまいます。
 *   useCallback で関数をメモ化すると、この問題を防げます。
 */
import { useEffect, useRef, useCallback } from "react";

/**
 * 【nipplejs ライブラリのインポート】
 * nipplejs → ジョイスティックを作成するメイン関数
 * JoystickManager → ジョイスティックの管理オブジェクトの型（TypeScript用）
 *
 * "type JoystickManager" の "type" は TypeScript の型のみインポートを示します。
 * 型情報はビルド時に除去されるため、バンドルサイズに影響しません。
 */
import nipplejs, { type JoystickManager } from "nipplejs";

// -------------------------------------------------------
// 型定義（インターフェース）
// -------------------------------------------------------

/**
 * 【JoystickControllerProps インターフェース】
 * このコンポーネントが受け取る props の型定義です。
 *
 * - onMove: ジョイスティックを動かしたときに呼ばれる関数
 *   → linear_x（前後速度）、linear_y（左右速度）、angular_z（回転速度）を受け取る
 *   → 親コンポーネントがこれらの値をロボットに送信する
 *
 * - onStop: ジョイスティックを離したときに呼ばれる関数
 *   → ロボットを停止させるために使う
 *
 * - maxLinear?: 最大直進速度（デフォルト: 0.5 m/s）
 *   → "?" は省略可能なプロパティ
 *   → 省略した場合、コンポーネント内でデフォルト値が使われる
 *
 * - maxAngular?: 最大回転速度（デフォルト: 1.0 rad/s）
 *
 * - disabled?: 操作を無効にするかどうか（デフォルト: false）
 *   → 緊急停止中など、操作を禁止したいときに true にする
 */
interface JoystickControllerProps {
  onMove: (linear_x: number, linear_y: number, angular_z: number) => void;
  onStop: () => void;
  maxLinear?: number;
  maxAngular?: number;
  disabled?: boolean;
}

// -------------------------------------------------------
// コンポーネント定義
// -------------------------------------------------------

/**
 * 【JoystickController コンポーネント】
 * バーチャルジョイスティックを描画し、ユーザーの操作を速度コマンドに変換します。
 *
 * 【デフォルトパラメータ】
 * maxLinear = 0.5 のような書き方は「デフォルト値」の指定です。
 * 親コンポーネントが maxLinear を渡さなかった場合、0.5 が使われます。
 */
export function JoystickController({
  onMove,
  onStop,
  maxLinear = 0.5,
  maxAngular = 1.0,
  disabled = false,
}: JoystickControllerProps) {
  /**
   * 【useRef - DOM要素への参照】
   * containerRef は、ジョイスティックを表示するための div 要素への参照です。
   *
   * useRef<HTMLDivElement>(null) の意味：
   * - <HTMLDivElement> → この ref が div 要素を指すことを型で示す
   * - (null) → 初期値は null（まだ DOM にマウントされていないため）
   *
   * コンポーネントがマウント（表示）された後、
   * containerRef.current に実際の DOM 要素が入ります。
   */
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * 【useRef - ミュータブルな値の保持】
   * managerRef は nipplejs のジョイスティックマネージャーを保持します。
   *
   * - JoystickManager | null → マネージャーインスタンスまたは null
   * - クリーンアップ時にジョイスティックを破棄するために参照を保持します
   * - useState ではなく useRef を使う理由：
   *   マネージャーが変わっても再レンダリングは不要だから
   */
  const managerRef = useRef<JoystickManager | null>(null);

  /**
   * 【useCallback - handleMove 関数のメモ化】
   * ジョイスティックが動いたときに呼ばれるコールバック関数です。
   *
   * 【なぜ useCallback で包むのか？】
   * この関数は useEffect の依存配列に含まれています。
   * useCallback を使わないと、コンポーネントが再レンダリングされるたびに
   * 新しい関数が作られ、useEffect が何度も再実行されてしまいます。
   * useCallback を使うと、依存配列の値が変わるまで同じ関数参照が維持されます。
   *
   * 【引数の説明】
   * _ : 最初の引数（イベントオブジェクト）は使わないので "_" で無視
   *     → JavaScript の慣習として、使わない引数は "_" と名付けます
   * data: nipplejs が提供するジョイスティックの位置データ
   *   - data.distance: 中心からの距離（ピクセル単位）
   *   - data.angle.radian: ジョイスティックの傾き角度（ラジアン単位）
   *
   * 【速度計算のロジック】
   * 1. force = Math.min(data.distance / 75, 1)
   *    → 距離を 0〜1 の範囲に正規化（75px で最大力）
   *    → Math.min() で1を超えないように制限
   *
   * 2. linear_x = Math.sin(angle) * force * maxLinear
   *    → 前後方向の速度 = sin(角度) × 力 × 最大速度
   *    → sin を使うのは、上方向のドラッグを前進にマッピングするため
   *
   * 3. angular_z = -Math.cos(angle) * force * maxAngular
   *    → 回転速度 = -cos(角度) × 力 × 最大回転速度
   *    → cos を使い、左右のドラッグを回転にマッピング
   *    → マイナスは座標系の変換（画面座標とロボット座標の違い）
   *
   * 【依存配列 [disabled, maxLinear, maxAngular, onMove]】
   * これらの値が変わった場合のみ、関数が再作成されます。
   * 値が変わらなければ、前回と同じ関数参照が返されます。
   */
  const handleMove = useCallback(
    (_: unknown, data: { distance: number; angle: { radian: number } }) => {
      // 無効状態なら何もしない
      if (disabled) return;

      // ジョイスティックの傾き量を 0〜1 に正規化（75px を最大とする）
      const force = Math.min(data.distance / 75, 1);

      // ジョイスティックの角度（ラジアン）
      const angle = data.angle.radian;

      // 前後速度：sin(角度) × 力の大きさ × 最大速度
      const linear_x = Math.sin(angle) * force * maxLinear;

      // 回転速度：-cos(角度) × 力の大きさ × 最大回転速度
      const angular_z = -Math.cos(angle) * force * maxAngular;

      // 親コンポーネントに速度を通知（linear_y は通常 0）
      onMove(linear_x, 0, angular_z);
    },
    [disabled, maxLinear, maxAngular, onMove]
  );

  /**
   * 【useEffect - ジョイスティックの作成と破棄】
   *
   * useEffect は以下のタイミングで実行されます：
   * 1. コンポーネントがマウント（初回表示）されたとき
   * 2. 依存配列 [disabled, handleMove, onStop] の値が変わったとき
   *
   * 【return 文（クリーンアップ関数）】
   * useEffect が返す関数は「クリーンアップ関数」と呼ばれ、
   * コンポーネントがアンマウント（画面から消える）されるときや、
   * 依存配列の値が変わって再実行される前に呼ばれます。
   *
   * ここでは manager.destroy() でジョイスティックを破棄しています。
   * 【なぜクリーンアップが必要なのか？】
   * 破棄しないと、古いジョイスティックのイベントリスナーが残り続け、
   * メモリリークやバグの原因になります。
   */
  useEffect(() => {
    // DOM 要素がまだ準備できていない場合は何もしない
    if (!containerRef.current) return;

    /**
     * 【nipplejs.create() - ジョイスティックの作成】
     * nipplejs ライブラリを使って仮想ジョイスティックを作成します。
     *
     * オプションの説明：
     * - zone: ジョイスティックを配置するDOM要素
     * - mode: "static" → 固定位置に配置（"dynamic" だとタッチ位置に出現）
     * - position: ジョイスティックの位置（コンテナの中央に配置）
     * - color: ジョイスティックの色
     *   → disabled の場合は灰色（#999）、有効なら青色（#3b82f6）
     * - size: ジョイスティックの直径（120ピクセル）
     */
    const manager = nipplejs.create({
      zone: containerRef.current,
      mode: "static",
      position: { left: "50%", top: "50%" },
      color: disabled ? "#999" : "#3b82f6",
      size: 120,
    });

    // マネージャーの参照を保存（将来の破棄用）
    managerRef.current = manager;

    /**
     * 【イベントリスナーの登録】
     *
     * manager.on("move", ...) → ジョイスティックが動いたときに handleMove を呼ぶ
     *   "as never" は TypeScript の型の不一致を回避するための型アサーション
     *
     * manager.on("end", ...) → ジョイスティックを離したときに onStop を呼ぶ
     *   → ロボットに「停止してください」と伝えます
     */
    manager.on("move", handleMove as never);
    manager.on("end", () => onStop());

    /**
     * 【クリーンアップ関数】
     * コンポーネントが消えるとき、またはエフェクトが再実行される前に、
     * ジョイスティックを破棄して後片付けをします。
     */
    return () => {
      manager.destroy();
    };
  }, [disabled, handleMove, onStop]); // ← 依存配列：これらの値が変わると再実行

  return (
    /**
     * 【ジョイスティックの外側コンテナ】
     * ジョイスティック本体と説明テキストを縦に並べます。
     */
    <div className="flex flex-col items-center gap-2">
      {/**
       * 【ジョイスティック描画エリア】
       * ref={containerRef} で、この div を containerRef に紐づけます。
       * nipplejs はこの div の中にジョイスティックの Canvas を描画します。
       *
       * - "relative"  → 子要素の絶対位置の基準点にする
       * - "h-40 w-40" → 幅・高さ 10rem（160px）の正方形
       * - "rounded-full" → 円形にする
       * - "border-2 border-dashed border-muted-foreground/30"
       *   → 点線の薄い枠線（ジョイスティックの範囲を視覚的に示す）
       *   → "/30" は不透明度30%（30% opacity）
       *
       * style={{ touchAction: "none" }}
       * → ブラウザのデフォルトのタッチ操作（スクロール、ズームなど）を無効にする
       * → これがないと、ジョイスティックを操作しようとしたときに
       *   ページがスクロールしてしまいます
       * → CSS の touch-action プロパティをインラインスタイルで設定
       */}
      <div
        ref={containerRef}
        className="relative h-40 w-40 rounded-full border-2 border-dashed border-muted-foreground/30"
        style={{ touchAction: "none" }}
      />

      {/**
       * 【説明テキスト】
       * ジョイスティックの下に操作方法を表示します。
       * disabled の状態に応じてテキストを切り替えます。
       */}
      <span className="text-xs text-muted-foreground">
        {disabled ? "Control disabled" : "Drag to move"}
      </span>
    </div>
  );
}
