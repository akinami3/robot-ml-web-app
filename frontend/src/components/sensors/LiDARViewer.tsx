// =============================================================================
// LiDARViewer.tsx - LiDARセンサーの点群データを2D表示するコンポーネント
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、ロボットのLiDARセンサーから得られた距離データを
// 2次元の鳥瞰図（上から見た図）としてCanvasに描画するコンポーネントです。
//
// 【LiDAR（ライダー）とは？】
// LiDAR = Light Detection and Ranging（光による検知と測距）
// レーザー光を360度（またはある範囲）に照射し、反射して戻ってくるまでの
// 時間を計測することで、周囲の物体までの距離を測定するセンサーです。
//
// 【LiDARのデータ構造】
// - ranges: 各角度方向の距離値（メートル単位）の配列
//   例: [2.5, 2.3, 3.1, ...] → 各角度方向に何メートル先に物体があるか
// - angleMin / angleMax: スキャン範囲の開始角度と終了角度（ラジアン単位）
//   例: -π 〜 π は360度全周スキャン
// - rangeMax: 検出可能な最大距離（メートル単位）
//
// 【Canvas APIとは？】
// HTML5のCanvas要素は、JavaScriptから直接ピクセルを描画できる領域です。
// 2Dグラフィックスの描画に使われ、ゲームやデータ可視化によく利用されます。
// このコンポーネントでは、Canvas上にLiDARの点群データを描画しています。
// =============================================================================

// -----------------------------------------------------------------------------
// インポート部分
// -----------------------------------------------------------------------------

// React Hooks（フック）のインポート
// 【useEffectとは？】
// コンポーネントがレンダリングされた「後に」実行される副作用（side effect）を
// 定義するフック。ここではCanvas描画処理に使用。
// データ（ranges）が変化するたびにCanvasを再描画する。
//
// 【useRefとは？】
// DOM要素への「参照」を保持するフック。
// Canvasの実際のDOM要素に直接アクセスするために使用。
// Reactは通常DOMを直接操作しないが、Canvas描画にはDOM要素が必要。
import { useEffect, useRef } from "react";

// カードUIコンポーネント（共通UIパーツ）
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

// -----------------------------------------------------------------------------
// 型定義（インターフェース）
// -----------------------------------------------------------------------------

// LiDARViewerProps: このコンポーネントに渡すpropsの型定義
interface LiDARViewerProps {
  /** Array of ranges in meters */
  // ranges: 各角度方向の距離の配列（メートル単位）
  // number[] は「数値の配列」を意味するTypeScriptの型表記
  ranges: number[];

  // angleMin: スキャン開始角度（ラジアン）。デフォルトは -π（-180度）
  // "?" はオプショナル（省略可能）
  angleMin?: number;

  // angleMax: スキャン終了角度（ラジアン）。デフォルトは π（180度）
  angleMax?: number;

  // rangeMax: 最大検出距離（メートル）。デフォルトは12m
  // この値を超える距離のデータは描画しない
  rangeMax?: number;
}

// =============================================================================
// LiDARViewerコンポーネント本体
// =============================================================================

// 【デフォルト引数の設定】
// angleMin = -Math.PI は -180度（左方向）
// angleMax = Math.PI は 180度（右方向）
// つまりデフォルトで360度全周をカバー
// Math.PI はJavaScriptの組み込み定数で、π（約3.14159）の値
export function LiDARViewer({
  ranges,
  angleMin = -Math.PI,
  angleMax = Math.PI,
  rangeMax = 12,
}: LiDARViewerProps) {
  // ---------------------------------------------------------------------------
  // Canvas要素への参照を作成
  // ---------------------------------------------------------------------------

  // 【useRef<HTMLCanvasElement>(null) とは？】
  // useRefフックを使って、HTML Canvas要素への参照を作成。
  // <HTMLCanvasElement> はTypeScriptのジェネリクスで、「HTMLCanvasElement型の参照」
  // であることを明示。初期値はnull（まだDOM要素が存在しないため）。
  // この参照は、後でJSXの <canvas ref={canvasRef} /> で紐づけられる。
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // ---------------------------------------------------------------------------
  // Canvas描画処理（useEffect内）
  // ---------------------------------------------------------------------------

  // 【useEffectの使い方】
  // useEffect(() => { 処理 }, [依存配列])
  // - 第1引数: 実行する処理（関数）
  // - 第2引数: 依存配列。この配列内の値が変化した時に処理が再実行される
  //   ここでは ranges, angleMin, angleMax, rangeMax が変化するたびに再描画
  useEffect(() => {
    // Canvas要素を取得する
    // canvasRef.current は実際のDOM要素、またはnull
    const canvas = canvasRef.current;

    // Canvas要素が存在しない、またはデータが空の場合は何もしない
    // 【早期リターン（early return）パターン】
    // 条件を満たさない場合にすぐ関数を抜けることで、ネストが深くなるのを防ぐ
    if (!canvas || ranges.length === 0) return;

    // 【2Dコンテキストの取得】
    // Canvas APIで描画するには、まず描画コンテキスト（context）を取得する必要がある。
    // "2d" を指定すると、2D描画用のAPIが使えるようになる。
    // 3D描画の場合は "webgl" を指定する。
    const ctx = canvas.getContext("2d");

    // コンテキストが取得できない場合は何もしない（通常は起こらない）
    if (!ctx) return;

    // Canvas のサイズを変数に格納（後で計算に使う）
    const w = canvas.width;   // Canvasの幅（ピクセル）
    const h = canvas.height;  // Canvasの高さ（ピクセル）
    const cx = w / 2;         // Canvasの中心X座標（ロボットの位置）
    const cy = h / 2;         // Canvasの中心Y座標（ロボットの位置）

    // 【スケール（拡大縮小率）の計算】
    // LiDARの距離データ（メートル単位）をCanvas上のピクセルに変換する比率
    // Math.min(cx, cy) * 0.85: 画面に収まるように85%のマージンを確保
    // / rangeMax: 最大距離がCanvas内に収まるように調整
    const scale = Math.min(cx, cy) * 0.85 / rangeMax;

    // 【Canvas全体をクリア（消去）する】
    // clearRect(x, y, 幅, 高さ): 指定した矩形領域を透明にする
    // 前のフレームの描画を消してから新しいフレームを描画する
    ctx.clearRect(0, 0, w, h);

    // =======================================================================
    // 格子円（グリッドサークル）の描画
    // =======================================================================
    // 距離の目安を示す同心円を描画する。2m間隔で描画。
    // 例: rangeMax=12 なら、2m, 4m, 6m, 8m, 10m, 12m の6つの円

    // 【strokeStyleとは？】線の色を設定するプロパティ
    // "rgba(100,100,100,0.3)" は半透明の灰色
    // rgba = Red, Green, Blue, Alpha（透明度）
    ctx.strokeStyle = "rgba(100,100,100,0.3)";

    // 【lineWidthとは？】線の太さを設定するプロパティ（ピクセル単位）
    ctx.lineWidth = 0.5;

    // 2m間隔で同心円を描画するforループ
    for (let r = 2; r <= rangeMax; r += 2) {
      // 【beginPath()とは？】
      // 新しいパス（描画の経路）を開始する。これを呼ばないと、
      // 前のパスと結合されてしまい、意図しない描画になる。
      ctx.beginPath();

      // 【arc()とは？】円弧を描く
      // arc(中心X, 中心Y, 半径, 開始角度, 終了角度)
      // cx, cy: Canvasの中心（ロボットの位置）
      // r * scale: 距離をピクセルに変換
      // 0 〜 Math.PI * 2: 0度から360度まで（完全な円）
      ctx.arc(cx, cy, r * scale, 0, Math.PI * 2);

      // 【stroke()とは？】
      // 設定した色と太さで、パスに沿って線を描画する
      // fill()だと塗りつぶし、stroke()だと輪郭線のみ
      ctx.stroke();
    }

    // =======================================================================
    // 十字線の描画
    // =======================================================================
    // Canvas中央に十字線を描画。ロボットの前後左右を示す補助線。

    ctx.beginPath();
    // 【moveTo()とは？】ペンを持ち上げて指定座標に移動する（線は描かない）
    // 縦線: 上端(cx, 0)から下端(cx, h)まで
    ctx.moveTo(cx, 0);
    // 【lineTo()とは？】現在位置から指定座標まで線を引く
    ctx.lineTo(cx, h);
    // 横線: 左端(0, cy)から右端(w, cy)まで
    ctx.moveTo(0, cy);
    ctx.lineTo(w, cy);
    ctx.stroke();

    // =======================================================================
    // ロボットの位置を示す青い丸の描画
    // =======================================================================

    // 【fillStyleとは？】塗りつぶしの色を設定するプロパティ
    // "#3b82f6" はTailwind CSSのblue-500に相当する青色
    ctx.fillStyle = "#3b82f6";
    ctx.beginPath();
    // 中心位置に半径4pxの円を描画
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    // 【fill()とは？】パスの内側を塗りつぶす
    ctx.fill();

    // =======================================================================
    // LiDARの点群データの描画
    // =======================================================================

    // 各レーザービーム間の角度差（ラジアン）を計算
    // 例: 360度スキャンで360個のデータなら、1度（π/180ラジアン）ずつ
    const angleStep = (angleMax - angleMin) / ranges.length;

    // 点群の色を赤に設定
    ctx.fillStyle = "#ef4444";

    // 全てのレーザービームについてループ
    for (let i = 0; i < ranges.length; i++) {
      const r = ranges[i]; // i番目のビームが検出した距離（メートル）

      // 距離が0以下（無効データ）、またはrangeMax以上（範囲外）の場合はスキップ
      if (r <= 0 || r >= rangeMax) continue;

      // 【極座標から直交座標への変換】
      // LiDARのデータは極座標（角度と距離）で表される：
      //   角度θ = angleMin + i * angleStep
      //   距離r = ranges[i]
      //
      // これをCanvas上のXY座標に変換する：
      //   X = cx + cos(θ) * r * scale
      //   Y = cy + sin(θ) * r * scale
      //
      // - Math.PI / 2 はCanvasの座標系に合わせるための90度回転
      // （Canvasでは上が0度、数学では右が0度のため）
      const angle = angleMin + i * angleStep - Math.PI / 2;
      const px = cx + Math.cos(angle) * r * scale;  // X座標
      const py = cy + Math.sin(angle) * r * scale;  // Y座標

      // 計算した座標に半径1.5pxの小さな赤い円を描画
      ctx.beginPath();
      ctx.arc(px, py, 1.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [ranges, angleMin, angleMax, rangeMax]);
  // ↑ 依存配列: これらの値が変わると自動的にuseEffect内の処理が再実行される

  // ---------------------------------------------------------------------------
  // JSX（レンダリング部分）
  // ---------------------------------------------------------------------------

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">LiDAR</CardTitle>
      </CardHeader>

      {/* flex items-center justify-center: 中身を上下左右中央に配置 */}
      <CardContent className="flex items-center justify-center">
        {/* HTML5 Canvas要素 */}
        {/* ref={canvasRef}: useRefで作った参照をこのCanvas要素に紐づける */}
        {/* width={300} height={300}: Canvas描画サイズ（ピクセル単位） */}
        {/* 【注意】CSSのwidth/heightとCanvas属性のwidth/heightは別物 */}
        {/* Canvas属性のサイズは描画解像度を決定する */}
        {/* bg-black/5: ライトモードでは薄い黒の背景 */}
        {/* dark:bg-white/5: ダークモードでは薄い白の背景 */}
        <canvas
          ref={canvasRef}
          width={300}
          height={300}
          className="rounded-lg bg-black/5 dark:bg-white/5"
        />
      </CardContent>
    </Card>
  );
}
