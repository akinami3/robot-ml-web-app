/**
 * ============================================================
 * StatusBar.tsx - ステータスバーコンポーネント
 * ============================================================
 *
 * 【ファイルの概要】
 * このファイルは、画面上部に表示されるステータスバーを実装しています。
 * ロボットの現在の状態を一目で確認できる重要な UI コンポーネントです。
 *
 * 【表示する情報】
 * 1. WebSocket接続状態（接続中/切断中/再接続中）
 * 2. 選択中のロボットの名前と状態
 * 3. バッテリー残量
 *
 * 【ステータスバーの構造】
 * ┌──────────────────────────────────────────────────┐
 * │ 🟢 Connected  │  🤖 Robot-01 [active]  🔋 85% │
 * └──────────────────────────────────────────────────┘
 */

// -------------------------------------------------------
// インポート部分
// -------------------------------------------------------

/**
 * 【lucide-react アイコン】
 * ステータス表示に使うアイコンをインポートしています。
 *
 * - Wifi          → 接続中を示すWi-Fiアイコン
 * - WifiOff       → 切断中を示す×印付きWi-Fiアイコン
 * - Battery       → 通常のバッテリーアイコン
 * - BatteryWarning → バッテリー残量が少ないときの警告アイコン
 * - Bot           → ロボットのアイコン
 */
import { Wifi, WifiOff, Battery, BatteryWarning, Bot } from "lucide-react";

/**
 * 【Badge コンポーネント】
 * 小さなバッジ（ラベル）を表示するUIコンポーネントです。
 * ロボットの状態（active/idle/error など）をバッジで表示します。
 *
 * "@/components/ui/primitives" は、アプリ全体で再利用する
 * 基本的なUIコンポーネント群をまとめたファイルです。
 */
import { Badge } from "@/components/ui/primitives";

/**
 * 【useRobotStore】ロボットの状態管理ストア
 * 接続中のロボット一覧、選択中のロボットID、センサーデータなどを管理します。
 */
import { useRobotStore } from "@/stores/robotStore";

/**
 * 【robotStateColor ユーティリティ関数】
 * ロボットの状態（state）に応じた色のCSSクラスを返すヘルパー関数です。
 * 例："active" → "text-green-500", "error" → "text-red-500" など
 */
import { robotStateColor } from "@/lib/utils";

// -------------------------------------------------------
// 型定義（インターフェース）
// -------------------------------------------------------

/**
 * 【StatusBarProps インターフェース】
 * StatusBar コンポーネントが受け取る props の型定義です。
 *
 * - isConnected: boolean
 *   → WebSocket がサーバーに接続されているかどうか
 *   → true = 接続中、false = 切断中
 *
 * - reconnectCount: number
 *   → 再接続を試行した回数
 *   → 0 = まだ再接続していない
 *   → 1以上 = 接続が切れて再接続を試みている
 */
interface StatusBarProps {
  isConnected: boolean;
  reconnectCount: number;
}

// -------------------------------------------------------
// コンポーネント定義
// -------------------------------------------------------

/**
 * 【StatusBar コンポーネント】
 * アプリケーション上部のステータスバーを描画します。
 * AppLayout.tsx から呼び出されます。
 */
export function StatusBar({ isConnected, reconnectCount }: StatusBarProps) {
  /**
   * 【useRobotStore からの状態取得】
   * 3つのセレクターで必要な値だけを取り出しています。
   *
   * robots: 接続中のロボット一覧（配列）
   * selectedId: 現在選択中のロボットのID
   * latestSensor: 最新のセンサーデータ（ロボットIDをキーにしたオブジェクト）
   *
   * 【なぜ個別にセレクターを使うのか？】
   * (s) => ({ robots: s.robots, selectedId: s.selectedRobotId }) のように
   * まとめて取得することもできますが、個別に取得するほうが
   * 不要な再レンダリングを避けられます（Zustand の性能最適化）。
   */
  const robots = useRobotStore((s) => s.robots);
  const selectedId = useRobotStore((s) => s.selectedRobotId);
  const latestSensor = useRobotStore((s) => s.latestSensorData);

  /**
   * 【選択中のロボット情報の取得】
   *
   * robots.find((r) => r.id === selectedId)
   * → .find() は配列から条件に合う最初の要素を返すメソッド
   * → ロボット配列から、ID が selectedId と一致するロボットを探す
   * → 見つからなければ undefined が返る
   */
  const robot = robots.find((r) => r.id === selectedId);

  /**
   * 【バッテリーデータの取得】
   *
   * selectedId ? latestSensor[selectedId]?.battery : undefined
   * → 三項演算子と Optional Chaining（?.）を組み合わせています
   *
   * 【Optional Chaining（?.）とは？】
   * オブジェクトのプロパティに安全にアクセスする書き方です。
   * latestSensor[selectedId] が null や undefined の場合、
   * 通常の "." だとエラーになりますが、"?." だと undefined を返します。
   *
   * 例：latestSensor[selectedId] が undefined のとき
   *   latestSensor[selectedId].battery  → ❌ エラー！
   *   latestSensor[selectedId]?.battery → ✅ undefined（安全）
   */
  const battery = selectedId ? latestSensor[selectedId]?.battery : undefined;

  /**
   * 【バッテリー残量の計算】
   *
   * battery ? (...) : 0
   * → battery が存在する場合はパーセンテージを取得、なければ 0
   *
   * (battery as unknown as Record<string, number>).percentage
   * → TypeScript の型アサーション（Type Assertion）を使っています
   * → battery の型が正確に定義されていない場合、
   *   まず unknown に変換し、次に Record<string, number> として扱います
   * → Record<string, number> は「文字列キーで数値の値を持つオブジェクト」の型
   *
   * ?? 0 は Nullish Coalescing Operator（ヌリッシュ合体演算子）です
   * → 左辺が null または undefined のとき、右辺の 0 を使います
   * → || と似ていますが、0 や "" を false として扱わない点が異なります
   */
  const batteryLevel = battery ? ((battery as unknown as Record<string, number>).percentage ?? 0) : 0;

  return (
    /**
     * 【ステータスバーのコンテナ】
     * - "h-10"  → 高さ 2.5rem（40px）の薄いバー
     * - "gap-4" → 子要素間に余白 1rem（16px）
     * - "border-b" → 下に境界線
     * - "bg-card" → カード背景色（やや明るい色）
     * - "px-4"  → 左右に余白 1rem
     * - "text-sm" → 小さめのフォントサイズ
     */
    <div className="flex h-10 items-center gap-4 border-b bg-card px-4 text-sm">
      {/* ===== 接続状態セクション ===== */}
      {/**
       * WebSocket の接続状態に応じてアイコンとテキストを切り替えます。
       */}
      <div className="flex items-center gap-1.5">
        {/**
         * 【条件付きレンダリング - 三項演算子】
         * isConnected が true なら Wifi アイコン（緑色）、
         * false なら WifiOff アイコン（赤色＝destructive）を表示します。
         *
         * "text-green-500"  → 緑色（接続OK）
         * "text-destructive" → 赤色（エラー/切断）← テーマで定義された色
         */}
        {isConnected ? (
          <Wifi className="h-4 w-4 text-green-500" />
        ) : (
          <WifiOff className="h-4 w-4 text-destructive" />
        )}

        {/**
         * 【接続状態テキスト】
         * 3つの状態に応じてテキストを切り替えます：
         *
         * 1. isConnected → "Connected"（接続中）
         * 2. !isConnected && reconnectCount > 0 → "Reconnecting (n)"（再接続試行中）
         * 3. !isConnected && reconnectCount === 0 → "Disconnected"（切断中）
         *
         * 【ネストした三項演算子】
         * condition1 ? value1 : condition2 ? value2 : value3
         * → if-else if-else と同じ意味です
         *
         * 【テンプレートリテラル `...${...}...`】
         * `Reconnecting (${reconnectCount})` は
         * バッククォート（`）で囲んだ文字列テンプレートです。
         * ${...} の中に JavaScript の式を埋め込めます。
         */}
        <span className={isConnected ? "text-green-600 dark:text-green-400" : "text-destructive"}>
          {isConnected ? "Connected" : reconnectCount > 0 ? `Reconnecting (${reconnectCount})` : "Disconnected"}
        </span>
      </div>

      {/* ===== ロボット情報セクション ===== */}
      {/**
       * 【条件付きレンダリング - ロボット選択時のみ表示】
       * robot が存在する（ロボットが選択されている）場合のみ、
       * ロボット情報とバッテリー情報を表示します。
       *
       * 【React Fragment（<>...</>）】
       * React では、コンポーネントは1つの親要素しか返せません。
       * 複数の要素をまとめるとき、余計な div を増やしたくない場合は
       * <> と </> で囲みます。これを「フラグメント」と呼びます。
       * DOM に余計な要素を追加しません。
       */}
      {robot && (
        <>
          {/**
           * 【セパレーター（区切り線）】
           * 接続状態とロボット情報の間に縦線を引きます。
           * - "h-4"     → 高さ 1rem（16px）
           * - "w-px"    → 幅 1px（ピクセル）
           * - "bg-border" → 枠線の色で塗りつぶし
           */}
          <div className="h-4 w-px bg-border" />

          {/**
           * 【ロボット名と状態バッジ】
           * - Bot アイコン → ロボットであることを示す
           * - robot.name → ロボットの名前（"Robot-01" など）
           * - Badge → ロボットの状態をバッジで表示（"active" "idle" "error" など）
           *
           * 【Badge コンポーネントの props】
           * - variant="outline" → 枠線スタイルのバッジ
           * - className={robotStateColor(robot.state)}
           *   → 状態に応じた色クラスを動的に設定
           */}
          <div className="flex items-center gap-1.5">
            <Bot className="h-4 w-4" />
            <span className="font-medium">{robot.name}</span>
            <Badge variant="outline" className={robotStateColor(robot.state)}>
              {robot.state}
            </Badge>
          </div>

          {/* ===== バッテリー情報セクション ===== */}
          {/**
           * 【バッテリー表示】
           * バッテリー残量に応じてアイコンを切り替えます。
           * - 20%超: 通常の Battery アイコン（緑色）
           * - 20%以下: BatteryWarning アイコン（黄色 ← 注意の色）
           *
           * batteryLevel.toFixed(0): 小数点以下を切り捨てて表示
           * → toFixed(0) は数値を文字列に変換し、小数点以下0桁に丸めます
           * → 例: 85.7 → "86"（四捨五入）
           *
           * {batteryLevel.toFixed(0)}% → "85%" のような表示になる
           */}
          <div className="flex items-center gap-1.5">
            {batteryLevel > 20 ? (
              <Battery className="h-4 w-4 text-green-500" />
            ) : (
              <BatteryWarning className="h-4 w-4 text-yellow-500" />
            )}
            <span>{batteryLevel.toFixed(0)}%</span>
          </div>
        </>
      )}
    </div>
  );
}
