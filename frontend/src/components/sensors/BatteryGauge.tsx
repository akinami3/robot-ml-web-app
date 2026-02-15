// =============================================================================
// BatteryGauge.tsx - バッテリー残量ゲージコンポーネント
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、ロボットのバッテリー残量を視覚的に表示するコンポーネントです。
// バッテリーの残量（パーセント）、電圧（ボルト）、充電状態を表示します。
//
// 【バッテリーとは？】
// ロボットは電池（バッテリー）で動きます。バッテリーの残量を常に監視することは
// ロボット運用において非常に重要です。残量が少なくなると、ロボットが突然止まって
// しまう可能性があるため、ユーザーに警告を出す必要があります。
//
// 【このコンポーネントの機能】
// - 残量50%以上 → 緑色（安全）
// - 残量20〜50% → 黄色（注意）
// - 残量20%以下 → 赤色（危険）
// - 充電中はアイコンと表示が変わる
// =============================================================================

// -----------------------------------------------------------------------------
// インポート部分
// -----------------------------------------------------------------------------

// Card系コンポーネント: UIの「カード」（角丸の枠で囲まれた領域）を構成するパーツ
// - Card: カード全体の外枠
// - CardHeader: カードの上部（タイトルなどを配置する部分）
// - CardTitle: カードのタイトルテキスト
// - CardContent: カードの本体部分（メインコンテンツを配置する部分）
// "@/components/ui/primitives" は自分たちで作ったUIプリミティブ（基本部品）です
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

// lucide-react: アイコンライブラリ（軽量でシンプルなSVGアイコン集）
// - Battery: 通常のバッテリーアイコン（十分な残量がある時に表示）
// - BatteryCharging: 充電中のバッテリーアイコン（⚡マーク付き）
// - BatteryWarning: 警告付きバッテリーアイコン（残量が少ない時に⚠マーク付き）
import { Battery, BatteryCharging, BatteryWarning } from "lucide-react";

// cn: クラス名（className）を結合するユーティリティ関数
// 複数のCSSクラスを条件付きで結合できます
// 例: cn("text-red", isActive && "font-bold") → isActiveがtrueなら "text-red font-bold"
import { cn } from "@/lib/utils";

// -----------------------------------------------------------------------------
// 型定義（インターフェース）
// -----------------------------------------------------------------------------

// 【interfaceとは？】
// TypeScriptの「interface（インターフェース）」は、データの形（構造）を定義します。
// 「このコンポーネントにはどんなデータを渡す必要があるか？」を明確にします。
// これにより、間違ったデータを渡すとコンパイル時にエラーが出て、バグを防げます。

// BatteryGaugeProps: BatteryGaugeコンポーネントに渡すprops（プロパティ）の型定義
interface BatteryGaugeProps {
  // percentage: バッテリー残量のパーセンテージ（0〜100の数値）
  // 例: 75.5 は 75.5% を意味する
  percentage: number;

  // voltage: バッテリーの電圧（ボルト単位）
  // 例: 12.6 は 12.6V を意味する
  // 【電圧とは？】電気の「圧力」のようなもの。バッテリーが消耗すると電圧が下がる
  voltage: number;

  // isCharging: 充電中かどうかのフラグ（true = 充電中, false = 充電していない）
  // "?" はオプショナル（省略可能）という意味。省略した場合はundefinedになる
  isCharging?: boolean;
}

// =============================================================================
// BatteryGaugeコンポーネント本体
// =============================================================================

// 【export function とは？】
// - export: この関数を他のファイルからインポートできるようにする
// - function: 関数（コンポーネント）を定義する
//
// 【分割代入（Destructuring）とは？】
// { percentage, voltage, isCharging = false } の部分は、propsオブジェクトから
// 個々のプロパティを取り出しています。
// "isCharging = false" はデフォルト値の設定。渡されなかった場合はfalseになる。
export function BatteryGauge({ percentage, voltage, isCharging = false }: BatteryGaugeProps) {
  // ---------------------------------------------------------------------------
  // 残量に応じた色の決定（条件付き変数）
  // ---------------------------------------------------------------------------

  // 【三項演算子（ternary operator）とは？】
  // 条件 ? 真の場合の値 : 偽の場合の値
  // ここでは三項演算子を入れ子（ネスト）にして3段階の判定をしている：
  //
  // percentage > 50  → "bg-green-500"  （50%超: 緑色 → 安全）
  // percentage > 20  → "bg-yellow-500" （20〜50%: 黄色 → 注意）
  // それ以外         → "bg-red-500"    （20%以下: 赤色 → 危険）
  //
  // "bg-green-500" はTailwind CSSのクラス名で、背景色（background）を緑色にする
  const color =
    percentage > 50 ? "bg-green-500" : percentage > 20 ? "bg-yellow-500" : "bg-red-500";

  // ---------------------------------------------------------------------------
  // 表示するアイコンの決定
  // ---------------------------------------------------------------------------

  // 【動的なコンポーネント選択パターン】
  // Reactでは、コンポーネント（関数）を変数に代入できます。
  // 条件によって表示するアイコンを切り替えています：
  // - 充電中 → BatteryCharging（充電マーク付きアイコン）
  // - 残量20%超 → Battery（通常アイコン）
  // - 残量20%以下 → BatteryWarning（警告アイコン）
  //
  // 変数名を大文字（Icon）で始めるのは、Reactのルールです。
  // Reactは大文字で始まる名前をコンポーネントとして扱います。
  const Icon = isCharging ? BatteryCharging : percentage > 20 ? Battery : BatteryWarning;

  // ---------------------------------------------------------------------------
  // JSX（レンダリング部分）
  // ---------------------------------------------------------------------------

  // 【JSXとは？】
  // JavaScriptの中にHTMLのようなコードを書ける構文です。
  // Reactはこの書き方でUIを組み立てます。
  return (
    // Card: カード全体を囲む外枠（角丸、ボーダー、影付きの箱）
    <Card>
      {/* CardHeader: カードの上部。タイトルを表示する領域 */}
      {/* className="pb-2": padding-bottom（下の内側余白）を0.5rem（8px）に設定 */}
      <CardHeader className="pb-2">
        {/* CardTitle: カードのタイトル。"Battery"と表示 */}
        {/* className="text-base": テキストサイズをbase（16px）に設定 */}
        <CardTitle className="text-base">Battery</CardTitle>
      </CardHeader>

      {/* CardContent: カードのメインコンテンツ部分 */}
      {/* flex: Flexboxレイアウト（要素を柔軟に配置するCSS手法） */}
      {/* flex-col: 子要素を縦方向（column）に並べる */}
      {/* items-center: 子要素を水平方向の中央に揃える */}
      {/* gap-3: 子要素間の間隔を0.75rem（12px）に設定 */}
      <CardContent className="flex flex-col items-center gap-3">

        {/* アイコンの表示 */}
        {/* cn()関数で、固定クラスと条件付きクラスを結合している */}
        {/* "h-10 w-10": アイコンの高さと幅を2.5rem（40px）に設定 */}
        {/* 残量に応じてテキスト色（アイコン色）を緑/黄/赤に変更 */}
        <Icon className={cn("h-10 w-10", percentage > 50 ? "text-green-500" : percentage > 20 ? "text-yellow-500" : "text-red-500")} />

        {/* バッテリー残量のプログレスバー（横棒グラフ） */}
        {/* これは2つのdivを重ねて作る一般的なUIパターン: */}
        {/*   外側のdiv: 灰色の背景（空のバー全体を表す） */}
        {/*   内側のdiv: 色付きの塗り部分（実際の残量を表す） */}
        {/* h-3: 高さ0.75rem（12px）。 w-full: 幅100% */}
        {/* rounded-full: 完全に丸い角（角丸）にする */}
        {/* bg-muted: 控えめな背景色（テーマに依存する灰色系） */}
        <div className="h-3 w-full rounded-full bg-muted">
          {/* 内側のdiv: 実際のバッテリー残量を表す色付きバー */}
          {/* cn(): colorクラス（緑/黄/赤）を動的に適用 */}
          {/* transition-all: すべてのCSS変化にアニメーションを付ける */}
          {/* style={{ width: `${...}%` }}: インラインスタイルで幅をパーセンテージ指定 */}
          {/* Math.min(percentage, 100): 100%を超えないように制限（安全策） */}
          <div
            className={cn("h-full rounded-full transition-all", color)}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>

        {/* パーセンテージと電圧の数値表示 */}
        {/* flex w-full justify-between: 左右に分散配置（スペースビトウィーン） */}
        {/* text-sm: テキストサイズを小さめ（14px）に設定 */}
        <div className="flex w-full justify-between text-sm">
          {/* 左側: バッテリー残量のパーセンテージ */}
          {/* font-mono: 等幅フォント（数値が揃って見やすくなる） */}
          {/* font-semibold: やや太い文字（強調表示） */}
          {/* toFixed(1): 小数点以下1桁に丸める。例: 75.4999 → "75.5" */}
          <span className="font-mono font-semibold">{percentage.toFixed(1)}%</span>

          {/* 右側: バッテリー電圧 */}
          {/* text-muted-foreground: 薄い色のテキスト（補助情報として控えめに表示） */}
          {/* toFixed(2): 小数点以下2桁に丸める。例: 12.599 → "12.60" */}
          <span className="font-mono text-muted-foreground">{voltage.toFixed(2)} V</span>
        </div>

        {/* 充電中の場合のみ「Charging」テキストを表示 */}
        {/* 【条件付きレンダリング】 */}
        {/* isCharging && (...) は短絡評価（ショートサーキット）パターン */}
        {/* isChargingがtrueの場合のみ、&&の右側のJSXが表示される */}
        {/* isChargingがfalseの場合、何も表示されない（非表示になる） */}
        {isCharging && (
          // text-xs: 非常に小さいテキスト（12px）
          // text-green-600: 緑色テキスト（ライトモード用）
          // dark:text-green-400: ダークモード時はやや明るい緑色にする
          <span className="text-xs text-green-600 dark:text-green-400">Charging</span>
        )}
      </CardContent>
    </Card>
  );
}
