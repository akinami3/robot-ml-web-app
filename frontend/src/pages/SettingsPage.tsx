// =============================================================================
// SettingsPage.tsx — 設定ページ
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、アプリケーションの各種設定を管理するページです。
// 主に以下の3カテゴリの設定を提供する：
//
// 1. 外観（Appearance）: ライト/ダークテーマの切り替え
// 2. 安全制限（Safety Limits）: ロボットの最大速度・角速度の制限
// 3. レコーディングデフォルト（Recording Defaults）: センサー記録の周波数設定
//
// 【なぜ設定ページが必要か？】
// - テーマ切り替え: ユーザーの好み・作業環境に合わせた表示
// - 安全制限: ロボットが暴走しないよう速度に上限を設ける
// - レコーディング設定: データ収集の頻度を調整（高頻度 = 精密だがデータ量増大）
//
// 【主な技術的ポイント】
// - localStorage: ブラウザにデータを永続保存するWeb API
// - useEffect: テーマ変更時にDOMを操作する副作用処理
// - document.documentElement: HTML文書の<html>要素への参照
// - classList.toggle: CSSクラスの追加/削除を切り替える
// - 遅延初期化（Lazy Initialization）: useState の初期値を関数で計算
// =============================================================================

// ---------------------------------------------------------------------------
// インポート部分
// ---------------------------------------------------------------------------

// 【useState】コンポーネントの状態（テーマ、速度上限など）を管理するフック。
// 【useEffect】副作用処理フック。テーマ変更時にDOMへの反映とlocalStorage保存を行う。
import { useState, useEffect } from "react";

// 【UIコンポーネント】
// Card系: カードレイアウト（設定カテゴリごとにカードで区切る）
// Button: ボタン（テーマ切替、保存）
// Input: テキスト/数値入力フィールド
// Label: フォーム要素のラベル（「Max Linear Speed」など）
// Select: ドロップダウン選択（センサー周波数）
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Label, Select } from "@/components/ui/primitives";

// 【Lucide React アイコン】
// Moon: 月アイコン（ダークテーマ表示時）
// Sun: 太陽アイコン（ライトテーマ表示時）
// Save: 保存アイコン（フロッピーディスク型）
import { Moon, Sun, Save } from "lucide-react";

// =============================================================================
// SettingsPage コンポーネント
// =============================================================================
export function SettingsPage() {
  // ---------------------------------------------------------------------------
  // テーマの状態管理
  // ---------------------------------------------------------------------------
  //
  // 【useState の遅延初期化（Lazy Initialization）】
  // useState に関数（() => ...）を渡すと、初回レンダリング時のみその関数が実行される。
  // 通常の値を渡すと毎回のレンダリングで評価されるが、関数型は初回だけ。
  // localStorage からの読み取りは重い処理なので、遅延初期化が適切。
  //
  // 【localStorage.getItem("theme")】
  // ブラウザの永続ストレージから "theme" キーの値を取得する。
  // ブラウザを閉じてもデータが残る（sessionStorageは閉じると消える）。
  //
  // 【as "light" | "dark"】
  // 型アサーション。localStorage.getItem の戻り値は string | null だが、
  // ここでは "light" か "dark" のリテラル型に変換する。
  //
  // 【?? "light"】
  // Nullish Coalescing。localStorageに値がない（null）場合は "light" を使う。
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") ?? "light"
  );

  // ---------------------------------------------------------------------------
  // ロボットの安全制限値の状態
  // ---------------------------------------------------------------------------
  //
  // 【なぜ数値を文字列（string）で管理するのか？】
  // HTMLの<input type="number">の value は文字列型。
  // 数値型で管理すると、"0." のような入力途中の状態を表現できない。
  // 文字列として管理し、サーバーに送る時に数値に変換するのが一般的。

  // maxLinear: 最大直線速度（m/s = メートル毎秒）
  const [maxLinear, setMaxLinear] = useState("0.5");

  // maxAngular: 最大角速度（rad/s = ラジアン毎秒）
  const [maxAngular, setMaxAngular] = useState("1.0");

  // ---------------------------------------------------------------------------
  // センサー記録周波数の状態
  // ---------------------------------------------------------------------------
  //
  // 【Hz（ヘルツ）とは？】
  // 1秒あたりの測定回数。10Hz = 1秒に10回データを記録する。
  // 高い周波数: より精密なデータが得られるが、データ量が増える
  // 低い周波数: データ量は少ないが、細かい変化を見逃す可能性がある
  const [sensorFreq, setSensorFreq] = useState("10");

  // ---------------------------------------------------------------------------
  // テーマ変更時のDOM操作（useEffect）
  // ---------------------------------------------------------------------------
  //
  // 【useEffect(callback, [theme])】
  // 依存配列に [theme] を指定しているため、theme の値が変わるたびに実行される。
  // 初回レンダリング時にも実行される。
  //
  // 【document.documentElement】
  // DOMのルート要素（<html>タグ）への参照。
  // ここにCSSクラスを追加/削除してテーマを切り替える。
  //
  // 【classList.toggle("dark", condition)】
  // 第2引数が true なら "dark" クラスを追加、false なら削除する。
  // Tailwind CSSの dark: プレフィックスを使ったスタイリングをトリガーする。
  // 例: dark:bg-gray-900 は "dark" クラスがある時だけ適用される。
  //
  // 【localStorage.setItem("theme", theme)】
  // テーマ設定をブラウザに保存する。次回アクセス時に復元される。
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  // ===========================================================================
  // JSX（レンダリング部分）
  // ===========================================================================
  //
  // 【ページのレイアウト構成】
  // ┌─────────────────────────────────────────┐
  // │ Settings（タイトル）                     │
  // ├──────────────────┬──────────────────────┤
  // │ Appearance       │ Safety Limits         │
  // │ Theme: [切替]    │ Max Linear: [0.5]     │
  // │                  │ Max Angular: [1.0]    │
  // │                  │ [Save]                │
  // ├──────────────────┼──────────────────────┤
  // │ Recording        │                       │
  // │ Defaults         │                       │
  // │ Freq: [10 Hz ▼]  │                       │
  // │ [Save]           │                       │
  // └──────────────────┴──────────────────────┘

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* 設定カードをグリッドで配置 */}
      {/* lg:grid-cols-2: 大画面で2列レイアウト */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* ================================================================= */}
        {/* 外観設定カード（テーマ切り替え）                                  */}
        {/* ================================================================= */}
        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Appearance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              {/* Label: アクセシビリティのためのラベル要素 */}
              <Label>Theme</Label>
              {/* テーマ切替ボタン */}
              {/* onClick: クリック時にテーマを切り替える */}
              {/* setTheme((t) => ...): 関数型更新で現在のテーマ(t)を基に切り替え */}
              {/* 三項演算子: light↔dark を反転させる */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
                className="gap-2"
              >
                {/* 現在のテーマに応じてアイコンを切り替え */}
                {theme === "light" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                {/* 現在のテーマ名を表示 */}
                {theme === "light" ? "Light" : "Dark"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* ================================================================= */}
        {/* 安全制限設定カード                                                */}
        {/* ================================================================= */}
        {/* Safety */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Safety Limits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 最大直線速度の入力 */}
            <div>
              <Label>Max Linear Speed (m/s)</Label>
              {/* 【Input type="number"の属性】 */}
              {/* step="0.1": 矢印ボタンで0.1ずつ増減する */}
              {/* min="0": 最小値は0（負の速度は不可） */}
              {/* max="2": 最大値は2 m/s（安全のため） */}
              <Input type="number" step="0.1" min="0" max="2" value={maxLinear} onChange={(e) => setMaxLinear(e.target.value)} />
            </div>

            {/* 最大角速度の入力 */}
            <div>
              <Label>Max Angular Speed (rad/s)</Label>
              <Input type="number" step="0.1" min="0" max="5" value={maxAngular} onChange={(e) => setMaxAngular(e.target.value)} />
            </div>

            {/* 保存ボタン */}
            {/* 現在はクリック時の処理が未実装（将来APIに保存する処理を追加予定） */}
            <Button className="gap-2">
              <Save className="h-4 w-4" />
              Save
            </Button>
          </CardContent>
        </Card>

        {/* ================================================================= */}
        {/* レコーディングデフォルト設定カード                                */}
        {/* ================================================================= */}
        {/* Recording */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recording Defaults</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Default Sensor Frequency (Hz)</Label>
              {/* 【Select ドロップダウン】 */}
              {/* 選択肢: 1Hz, 5Hz, 10Hz, 20Hz, 50Hz */}
              {/* 低い Hz = データが粗いが容量節約 */}
              {/* 高い Hz = データが精密だが容量増大 */}
              <Select value={sensorFreq} onChange={(e) => setSensorFreq(e.target.value)}>
                <option value="1">1 Hz</option>
                <option value="5">5 Hz</option>
                <option value="10">10 Hz</option>
                <option value="20">20 Hz</option>
                <option value="50">50 Hz</option>
              </Select>
            </div>

            {/* 保存ボタン */}
            <Button className="gap-2">
              <Save className="h-4 w-4" />
              Save
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
