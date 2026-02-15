// =============================================================================
// IMUChart.tsx - IMU（慣性計測装置）のデータをグラフ表示するコンポーネント
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、ロボットに搭載されたIMUセンサーのデータをリアルタイムで
// 折れ線グラフとして表示するコンポーネントです。
//
// 【IMU（Inertial Measurement Unit / 慣性計測装置）とは？】
// IMUはロボットの「動き」を測定するセンサーで、主に2つの機能があります：
//
// 1. 加速度計（Accelerometer）: ロボットにかかる力（加速度）を3軸（X,Y,Z）で計測
//    - 単位: m/s²（メートル毎秒毎秒）
//    - 静止時でも重力（約9.8 m/s²）がZ軸に検出される
//    - ロボットが傾いたり動いたりすると値が変化する
//
// 2. ジャイロスコープ（Gyroscope）: ロボットの回転速度を3軸（X,Y,Z）で計測
//    - 単位: rad/s（ラジアン毎秒）
//    - ロボットが回転すると値が変化する
//    - 静止時はほぼ0になる
//
// 【なぜIMUが重要？】
// IMUのデータを使って、ロボットの姿勢（傾き）や動きを推定できます。
// 自動運転車やドローンでも同じ原理が使われています。
//
// 【グラフライブラリ: Recharts】
// Rechartsは、Reactでグラフを描画するためのライブラリです。
// D3.jsをベースに、Reactコンポーネントとして使えるように作られています。
// =============================================================================

// -----------------------------------------------------------------------------
// インポート部分
// -----------------------------------------------------------------------------

// Rechartsライブラリからグラフ描画に必要なコンポーネントをインポート
// 【各コンポーネントの役割】
// - LineChart: 折れ線グラフのコンテナ（親コンポーネント）。データと子要素を管理
// - Line: 1本の折れ線。dataKeyで「どのデータ項目を描画するか」を指定
// - XAxis: X軸（横軸）。通常は時間などを表示
// - YAxis: Y軸（縦軸）。数値の範囲を表示
// - CartesianGrid: グラフの背景に表示する格子線（方眼紙のような線）
// - Tooltip: マウスを載せた時にデータの詳細値を表示するポップアップ
// - ResponsiveContainer: グラフを親要素のサイズに合わせてリサイズする
// - Legend: 凡例（各線の色と名前の対応表）
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

// カードUIコンポーネント（バッテリーゲージと同じ共通UIパーツ）
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

// -----------------------------------------------------------------------------
// 型定義（インターフェース）
// -----------------------------------------------------------------------------

// IMUChartProps: このコンポーネントに渡すデータの型定義
interface IMUChartProps {
  // 【JSDocコメント】 /** ... */ はJSDocコメントという特別なコメント形式
  // IDEがホバー時にこの説明を表示してくれる

  /** Array of { t, ax, ay, az, gx, gy, gz } history */
  // data: IMUセンサーの時系列データの配列
  // 【Array<{...}> とは？】
  // 「{...}の形をしたオブジェクトの配列」を意味する型表記
  // 例: [{ t: 0, ax: 1.2, ay: 0.5, ... }, { t: 1, ax: 1.3, ... }, ...]
  data: Array<{
    // t: タイムスタンプ（時刻）。X軸の値として使用
    t: number;
    // ax, ay, az: 加速度計のX, Y, Z軸の値（m/s²）
    // "?" はオプショナル（省略可能）。データが欠損している場合に対応
    ax?: number;
    ay?: number;
    az?: number;
    // gx, gy, gz: ジャイロスコープのX, Y, Z軸の値（rad/s）
    gx?: number;
    gy?: number;
    gz?: number;
  }>;
}

// =============================================================================
// IMUChartコンポーネント本体
// =============================================================================

// 【コンポーネントの構造】
// このコンポーネントは、1つのカード内に2つのグラフを縦に並べて表示します：
// 1. 上段: 加速度計のグラフ（ax, ay, az の3本の線）
// 2. 下段: ジャイロスコープのグラフ（gx, gy, gz の3本の線）
export function IMUChart({ data }: IMUChartProps) {
  return (
    // Card: カード全体の外枠
    <Card>
      {/* カードのヘッダー部分。"IMU"というタイトルを表示 */}
      <CardHeader className="pb-2">
        <CardTitle className="text-base">IMU</CardTitle>
      </CardHeader>

      {/* カードのメインコンテンツ */}
      <CardContent>
        {/* space-y-4: 子要素間に縦方向の間隔（1rem = 16px）を設定 */}
        {/* 上段のグラフと下段のグラフの間にスペースが入る */}
        <div className="space-y-4">

          {/* ======================================================= */}
          {/* 上段: 加速度計（Accelerometer）のグラフ */}
          {/* ======================================================= */}
          <div>
            {/* グラフのラベル。mb-1: 下に小さな余白 */}
            {/* text-xs: 非常に小さいテキスト */}
            {/* text-muted-foreground: 控えめな色のテキスト */}
            <p className="mb-1 text-xs text-muted-foreground">Accelerometer (m/s²)</p>

            {/* ResponsiveContainer: 親要素のサイズに合わせてグラフをリサイズ */}
            {/* width="100%": 幅を親要素の100%に合わせる */}
            {/* height={150}: 高さを150px固定 */}
            {/* 【なぜResponsiveContainerが必要？】 */}
            {/* Rechartsのグラフは固定サイズで描画されるため、 */}
            {/* このラッパーがないとウィンドウサイズに追従しない */}
            <ResponsiveContainer width="100%" height={150}>
              {/* LineChart: 折れ線グラフの親コンポーネント */}
              {/* data={data}: 表示するデータ配列を渡す */}
              <LineChart data={data}>
                {/* CartesianGrid: 背景の格子線（方眼紙のような補助線） */}
                {/* strokeDasharray="3 3": 3px描画して3px空ける破線パターン */}
                {/* opacity={0.3}: 30%の透明度で控えめに表示 */}
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />

                {/* XAxis: X軸（横軸）の設定 */}
                {/* dataKey="t": データの"t"プロパティ（時刻）をX軸に使用 */}
                {/* tick={false}: 軸の目盛りラベルを非表示（スペース節約） */}
                <XAxis dataKey="t" tick={false} />

                {/* YAxis: Y軸（縦軸）の設定 */}
                {/* width={40}: Y軸ラベルの表示幅を40pxに設定 */}
                {/* fontSize={10}: 目盛りのフォントサイズを10pxに設定 */}
                <YAxis width={40} fontSize={10} />

                {/* Tooltip: マウスオーバー時にデータ値を表示するポップアップ */}
                <Tooltip />

                {/* Legend: 凡例（どの色がどのデータを表すかの説明） */}
                {/* iconSize={8}: 凡例アイコンのサイズを8pxに設定 */}
                {/* wrapperStyle: 凡例テキストのフォントサイズを10pxに設定 */}
                <Legend iconSize={8} wrapperStyle={{ fontSize: 10 }} />

                {/* 各Line: 1本の折れ線を描画する */}
                {/* type="monotone": 滑らかな曲線で線を描画（カクカクしない） */}
                {/* dataKey="ax": データの"ax"プロパティの値を描画 */}
                {/* stroke="#ef4444": 線の色（赤色） */}
                {/* dot={false}: データポイントの丸い点を非表示（性能向上のため） */}
                {/* strokeWidth={1.5}: 線の太さを1.5pxに設定 */}
                {/* name="X": 凡例に表示する名前 */}

                {/* X軸方向の加速度 → 赤色 */}
                <Line type="monotone" dataKey="ax" stroke="#ef4444" dot={false} strokeWidth={1.5} name="X" />
                {/* Y軸方向の加速度 → 緑色 */}
                <Line type="monotone" dataKey="ay" stroke="#22c55e" dot={false} strokeWidth={1.5} name="Y" />
                {/* Z軸方向の加速度 → 青色 */}
                <Line type="monotone" dataKey="az" stroke="#3b82f6" dot={false} strokeWidth={1.5} name="Z" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* ======================================================= */}
          {/* 下段: ジャイロスコープ（Gyroscope）のグラフ */}
          {/* ======================================================= */}
          {/* 構造は上段と同じだが、表示するデータキーと色が異なる */}
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Gyroscope (rad/s)</p>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="t" tick={false} />
                <YAxis width={40} fontSize={10} />
                <Tooltip />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 10 }} />

                {/* X軸の回転速度 → オレンジ色 */}
                <Line type="monotone" dataKey="gx" stroke="#f97316" dot={false} strokeWidth={1.5} name="X" />
                {/* Y軸の回転速度 → 紫色 */}
                <Line type="monotone" dataKey="gy" stroke="#a855f7" dot={false} strokeWidth={1.5} name="Y" />
                {/* Z軸の回転速度 → シアン（水色） */}
                <Line type="monotone" dataKey="gz" stroke="#06b6d4" dot={false} strokeWidth={1.5} name="Z" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
