// =============================================================================
// OdometryDisplay.tsx - オドメトリ（移動量推定）データ表示コンポーネント
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、ロボットのオドメトリデータ（位置・姿勢・速度）を
// 数値とミニコンパスで表示するコンポーネントです。
//
// 【オドメトリ（Odometry）とは？】
// オドメトリは、ロボットの車輪の回転数やIMUセンサーなどから、
// ロボットが「どこにいるか」「どの方向を向いているか」を推定する技術です。
//
// 主なデータ：
// - x, y: ロボットの位置（メートル単位）
//   原点（0, 0）は通常、ロボットの起動地点
// - theta (θ): ロボットの向き（ラジアン単位）
//   0 = 初期方向（通常は前方）、π/2 = 左90度、-π/2 = 右90度
// - linearVelocity: 直線速度（m/s）= ロボットが前後にどれだけ速く動いているか
// - angularVelocity: 角速度（rad/s）= ロボットがどれだけ速く回転しているか
//
// 【なぜオドメトリが重要？】
// ロボットが自律的に移動するには、自分の位置を知る必要があります。
// GPSが使えない屋内では、オドメトリが位置推定の基本となります。
// ただし、車輪の滑りなどで誤差が蓄積するため、
// LiDARやカメラなど他のセンサーと組み合わせて補正します。
//
// 【SVG（Scalable Vector Graphics）について】
// このコンポーネントでは、ミニコンパスの描画にSVGを使用しています。
// SVGはXML形式のベクター画像で、拡大しても荒くならない利点があります。
// ReactではJSX内に直接SVGタグを記述できます。
// =============================================================================

// -----------------------------------------------------------------------------
// インポート部分
// -----------------------------------------------------------------------------

// カードUIコンポーネント（共通UIパーツ）
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

// lucide-react からアイコンをインポート
// - ArrowUp: 上向き矢印アイコン（直線速度の表示に使用）
// - RotateCw: 時計回り回転アイコン（角速度の表示に使用）
import { ArrowUp, RotateCw } from "lucide-react";

// -----------------------------------------------------------------------------
// 型定義（インターフェース）
// -----------------------------------------------------------------------------

// OdometryDisplayProps: このコンポーネントに渡すpropsの型定義
interface OdometryDisplayProps {
  // x: ロボットのX座標（メートル単位）
  // 通常、前方向が正
  x: number;

  // y: ロボットのY座標（メートル単位）
  // 通常、左方向が正
  y: number;

  // theta: ロボットの向き（ラジアン単位）
  // 【ラジアンとは？】角度の単位。360度 = 2π ラジアン
  // π ≈ 3.14159 なので、1ラジアン ≈ 57.3度
  theta: number;

  // linearVelocity: 直線速度（m/s）
  // 正の値 = 前進、負の値 = 後退
  linearVelocity: number;

  // angularVelocity: 角速度（rad/s）
  // 正の値 = 反時計回り（左旋回）、負の値 = 時計回り（右旋回）
  angularVelocity: number;
}

// =============================================================================
// OdometryDisplayコンポーネント本体
// =============================================================================

// 全てのpropsを分割代入で取り出す
export function OdometryDisplay({ x, y, theta, linearVelocity, angularVelocity }: OdometryDisplayProps) {
  // ---------------------------------------------------------------------------
  // ラジアンから度への変換
  // ---------------------------------------------------------------------------

  // 【ラジアン → 度の変換公式】
  // 度 = ラジアン × (180 / π)
  // 例: π/2 ラジアン → 90度、π ラジアン → 180度
  // toFixed(1) で小数点以下1桁に丸める
  const thetaDeg = ((theta * 180) / Math.PI).toFixed(1);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Odometry</CardTitle>
      </CardHeader>

      <CardContent>
        {/* grid grid-cols-2: CSSグリッドレイアウトで2列に配置 */}
        {/* 左列: 位置情報（X, Y, θ）、右列: 速度情報 */}
        {/* gap-4: グリッドセル間の間隔を1rem（16px）に設定 */}
        <div className="grid grid-cols-2 gap-4">

          {/* ===== 左列: 位置情報 ===== */}
          <div>
            {/* セクションラベル: "Position"（位置） */}
            <p className="text-xs text-muted-foreground">Position</p>

            {/* X座標の表示 */}
            {/* font-mono: 等幅フォント（数値の桁が揃って見やすい） */}
            {/* text-sm: 小さめのテキスト */}
            {/* toFixed(3): 小数点以下3桁に丸める（ミリメートル精度） */}
            <p className="font-mono text-sm">
              X: {x.toFixed(3)} m
            </p>

            {/* Y座標の表示 */}
            <p className="font-mono text-sm">
              Y: {y.toFixed(3)} m
            </p>

            {/* 角度（θ: シータ）の表示 */}
            {/* ラジアンではなく度で表示（人間にとってわかりやすいため） */}
            <p className="font-mono text-sm">
              θ: {thetaDeg}°
            </p>
          </div>

          {/* ===== 右列: 速度情報 ===== */}
          <div>
            {/* セクションラベル: "Velocity"（速度） */}
            <p className="text-xs text-muted-foreground">Velocity</p>

            {/* 直線速度の表示（上向き矢印アイコン付き） */}
            {/* flex items-center gap-1: アイコンとテキストを横に並べ、中央揃え */}
            <div className="flex items-center gap-1">
              {/* ArrowUp: 上向き矢印アイコン（直線的な前進を象徴） */}
              {/* h-3 w-3: 12px × 12pxの小さなアイコン */}
              <ArrowUp className="h-3 w-3" />
              {/* linearVelocityを小数点以下3桁で表示 */}
              <span className="font-mono text-sm">{linearVelocity.toFixed(3)} m/s</span>
            </div>

            {/* 角速度の表示（回転アイコン付き） */}
            <div className="flex items-center gap-1">
              {/* RotateCw: 時計回り回転アイコン（回転運動を象徴） */}
              <RotateCw className="h-3 w-3" />
              <span className="font-mono text-sm">{angularVelocity.toFixed(3)} rad/s</span>
            </div>
          </div>
        </div>

        {/* ================================================================= */}
        {/* ミニコンパス（方位表示）- SVGで描画 */}
        {/* ================================================================= */}
        {/* mt-3: 上に0.75remの余白。flex justify-center: 中央に配置 */}
        <div className="mt-3 flex justify-center">

          {/* 【SVG要素の説明】 */}
          {/* <svg>: SVG（Scalable Vector Graphics）のルート要素 */}
          {/* width="80" height="80": SVG全体のサイズ（80px × 80px） */}
          {/* viewBox="0 0 80 80": SVG内部の座標系を定義 */}
          {/*   viewBoxとは「仮想的な描画領域」のこと */}
          {/*   "0 0 80 80" = 左上が(0,0)、右下が(80,80)の座標空間 */}
          {/*   widthとviewBoxが同じなので、1:1の等倍表示になる */}
          <svg width="80" height="80" viewBox="0 0 80 80">

            {/* 外枠の円 */}
            {/* 【circle要素の属性】 */}
            {/* cx, cy: 円の中心座標（ここでは40, 40 = SVGの中心） */}
            {/* r: 円の半径（35px） */}
            {/* fill="none": 塗りつぶしなし（輪郭のみ） */}
            {/* stroke="currentColor": 線の色をテーマの文字色に合わせる */}
            {/* opacity={0.2}: 20%の透明度で控えめに表示 */}
            {/* strokeWidth="1": 線の太さ1px */}
            <circle cx="40" cy="40" r="35" fill="none" stroke="currentColor" opacity={0.2} strokeWidth="1" />

            {/* 方向を示す三角形（コンパスの針） */}
            {/* 【g要素とtransform属性】 */}
            {/* <g>: グループ要素。複数のSVG要素をまとめて変換（回転等）できる */}
            {/* transform={`rotate(角度, 中心X, 中心Y)`}: 指定した中心点を軸に回転 */}
            {/* -theta * 180 / Math.PI: ラジアンを度に変換し、符号を反転 */}
            {/* 符号を反転する理由: 数学の反時計回りとSVGの時計回りの違いを補正 */}
            <g transform={`rotate(${-theta * 180 / Math.PI}, 40, 40)`}>

              {/* 前方向を示す青い三角形（北の針） */}
              {/* 【polygon要素】 */}
              {/* polygon: 多角形を描画する要素 */}
              {/* points: 頂点の座標をスペース区切りで指定 */}
              {/* "40,10 35,30 45,30" → 3つの頂点: */}
              {/*   (40,10) = 上の頂点（前方） */}
              {/*   (35,30) = 左下 */}
              {/*   (45,30) = 右下 */}
              {/* fill="#3b82f6": 青色で塗りつぶし（前方向を表す） */}
              <polygon points="40,10 35,30 45,30" fill="#3b82f6" />

              {/* 後方向を示す灰色の三角形（南の針） */}
              {/* "40,70 35,50 45,50" → 3つの頂点: */}
              {/*   (40,70) = 下の頂点（後方） */}
              {/*   (35,50) = 左上 */}
              {/*   (45,50) = 右上 */}
              {/* fill="#94a3b8": 灰色で塗りつぶし（後方向を表す） */}
              <polygon points="40,70 35,50 45,50" fill="#94a3b8" />
            </g>
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}
