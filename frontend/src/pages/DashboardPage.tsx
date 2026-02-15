/**
 * ============================================================================
 * DashboardPage.tsx - ダッシュボードページコンポーネント
 * ============================================================================
 *
 * 【ファイルの概要】
 * ログイン後に最初に表示されるメイン画面（ダッシュボード）です。
 * ロボットの一覧、接続状況、データセット数などの概要情報を表示します。
 *
 * 【このページの役割】
 * 1. 登録されたロボットの一覧を表示する
 * 2. 各ロボットの接続状態やバッテリー残量を表示する
 * 3. サマリーカードで全体の統計情報を表示する
 * 4. 定期的に最新データを自動取得する（ポーリング）
 *
 * 【使われているデザインパターン】
 * - React Query（TanStack Query）: サーバーデータの取得・キャッシュ・自動更新
 * - コンポーネント分割: SummaryCardを別コンポーネントとして切り出し
 * - Zustandストア連携: 取得したロボットデータをグローバルストアにも保存
 * - 条件付きレンダリング: ロボットが0台の場合とある場合で表示を切り替え
 *
 * 【画面構成】
 * ┌───────────────────────────────────────────┐
 * │ Dashboard（タイトル）                       │
 * │                                           │
 * │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
 * │ │Robots│ │Active│ │Data │ │ RAG │ ← サマリーカード4枚
 * │ └─────┘ └─────┘ └─────┘ └─────┘          │
 * │                                           │
 * │ ┌─────────────────────────────────────┐   │
 * │ │ Connected Robots                     │   │
 * │ │  🤖 Robot-A  sim  100%  connected    │   │
 * │ │  🤖 Robot-B  ros  -     disconnected │   │
 * │ └─────────────────────────────────────┘   │
 * └───────────────────────────────────────────┘
 */

// =============================================================================
// インポート部分
// =============================================================================

/**
 * useQuery - TanStack Query（React Query）のデータ取得フック
 *
 * 【React Queryとは？】
 * サーバーからデータを取得し、キャッシュ（一時保存）し、
 * 自動的に再取得するためのライブラリです。
 *
 * 【なぜuseEffectではなくuseQueryを使う？】
 * useEffect + fetchでもデータ取得はできますが、以下の機能が不足します:
 *   - ローディング状態の管理
 *   - エラー状態の管理
 *   - キャッシュ（同じデータを何度もリクエストしない）
 *   - 自動再取得（refetchInterval）
 *   - バックグラウンドでの更新
 * React Queryはこれらを全て自動で行ってくれます。
 */
import { useQuery } from "@tanstack/react-query";

/**
 * lucide-reactアイコン
 * Bot - ロボットアイコン（🤖）
 * Database - データベースアイコン
 * Activity - アクティビティ（波形）アイコン
 * MessageSquare - メッセージ（吹き出し）アイコン
 *
 * 各サマリーカードとロボット一覧で使用します。
 */
import { Bot, Database, Activity, MessageSquare } from "lucide-react";

/**
 * UIコンポーネント
 * Card系 - カードレイアウト
 * Badge - バッジ（小さなラベル表示、例: "connected", "disconnected"）
 *
 * 【Badgeとは？】
 * 小さなタグやラベルのようなUI要素です。
 * ロボットの状態（接続中/切断中）を色付きのラベルで表示するのに使います。
 */
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui/primitives";

/**
 * APIクライアント
 * robotApi - ロボット関連のAPI（一覧取得など）
 * datasetApi - データセット関連のAPI（一覧取得など）
 */
import { robotApi, datasetApi } from "@/services/api";

/**
 * useRobotStore - ロボット状態管理ストア（Zustand）
 * 取得したロボットデータをグローバルに共有するためのストアです。
 *
 * 【なぜReact Queryとストアの両方を使う？】
 * - React Query: サーバーデータの取得・キャッシュを管理
 * - Zustandストア: 他のページ（ManualControlPage等）でもロボットデータを使うため
 * つまり、React Queryで取得したデータをストアにも保存する「二重管理」をしています。
 */
import { useRobotStore } from "@/stores/robotStore";

/**
 * robotStateColor - ロボットの状態に応じた色クラスを返すユーティリティ関数
 * 例: "connected" → 緑色, "disconnected" → 灰色
 */
import { robotStateColor } from "@/lib/utils";

/**
 * 型定義のインポート
 * type キーワードは「型情報だけをインポートする」ことを明示します。
 * 実行時のJavaScriptには含まれず、開発時の型チェックにのみ使われます。
 *
 * Robot - ロボットのデータ構造を定義する型
 *   例: { id: string, name: string, state: string, adapter_type: string, ... }
 * Dataset - データセットのデータ構造を定義する型
 *
 * 【typeインポートとは？】
 * import type { Robot } は、Robot型の情報だけを取り込みます。
 * コンパイル後のJavaScriptからは完全に消えるため、バンドルサイズに影響しません。
 */
import type { Robot, Dataset } from "@/types";

// =============================================================================
// DashboardPageコンポーネント
// =============================================================================

/**
 * DashboardPage - ダッシュボードのメインコンポーネント
 *
 * 【このコンポーネントの特徴】
 * - React Queryで2つのAPIを呼び出し（ロボット一覧 + データセット一覧）
 * - ロボット一覧は10秒ごとに自動更新（refetchInterval）
 * - 取得したデータをサマリーカードとリストで表示
 */
export function DashboardPage() {
  // ---------------------------------------------------------------------------
  // ストアからの関数取得
  // ---------------------------------------------------------------------------

  /**
   * setRobots - ストアにロボットデータを保存する関数
   * React Queryで取得したデータを、他のページでも使えるようにストアに保存します。
   */
  const setRobots = useRobotStore((s) => s.setRobots);

  // ---------------------------------------------------------------------------
  // データ取得（React Query）
  // ---------------------------------------------------------------------------

  /**
   * useQueryでロボット一覧を取得
   *
   * 【useQueryの引数】
   * queryKey: ["robots"]
   *   → クエリを識別するキー。同じキーのクエリはキャッシュを共有します。
   *     他のコンポーネントで同じキーでuseQueryを使うと、同じデータが返ります。
   *
   * queryFn: async () => { ... }
   *   → データを取得する関数。この関数の戻り値がdataに入ります。
   *
   * refetchInterval: 10000
   *   → 10秒（10000ミリ秒）ごとに自動で再取得。
   *     ロボットの状態が変わることがあるため、定期的に最新情報を取得します。
   *     これを「ポーリング」と呼びます。
   *
   * 【{ data: robots = [] }の意味】
   * useQueryの戻り値からdataプロパティを取り出し、robotsという名前に変更。
   * = [] は「dataがundefinedの場合は空配列を使う」というデフォルト値です。
   * データ取得前（ローディング中）は undefined なので、空配列で安全に処理できます。
   *
   * 【<Robot[]>ジェネリクスの意味】
   * useQuery<Robot[]>は「このクエリが返すデータの型はRobotの配列です」と宣言しています。
   * TypeScriptがデータの型を正しく推論できるようになります。
   */
  const { data: robots = [] } = useQuery<Robot[]>({
    queryKey: ["robots"],
    queryFn: async () => {
      /** robotApi.list()でサーバーからロボット一覧を取得 */
      const res = await robotApi.list();
      /**
       * 取得したデータをZustandストアにも保存
       * これにより、ManualControlPageなど他のページでもロボットデータを参照可能
       */
      setRobots(res.data);
      return res.data;
    },
    refetchInterval: 10000,  // 10秒ごとに自動更新
  });

  /**
   * useQueryでデータセット一覧を取得
   *
   * 【refetchIntervalを設定しない理由】
   * データセットはロボットの状態ほど頻繁に変化しないため、
   * ページ表示時に1回だけ取得すれば十分です。
   *
   * 【(res.data as unknown as ...).items ?? res.data の意味】
   * サーバーのレスポンス形式が2パターン考えられる場合の対応:
   *   パターン1: { items: [...] } → items配列を使用
   *   パターン2: [...] → 直接配列として使用
   * ?? 演算子は「左側がnull/undefinedなら右側を使う」というnullish coalescing演算子です。
   */
  const { data: datasets = [] } = useQuery<Dataset[]>({
    queryKey: ["datasets"],
    queryFn: async () => {
      const res = await datasetApi.list();
      return (res.data as unknown as { items?: Dataset[] }).items ?? res.data;
    },
  });

  // ---------------------------------------------------------------------------
  // 計算値
  // ---------------------------------------------------------------------------

  /**
   * 接続中のロボット数を計算
   *
   * robots.filter() - 配列から条件に合う要素だけを抽出する配列メソッド
   * (r) => r.state !== "disconnected"
   *   → state が "disconnected" ではないロボットだけをフィルタリング
   * .length - フィルタリング後の配列の要素数（= 接続中ロボット数）
   *
   * 【filterメソッドとは？】
   * 配列の各要素に条件関数を適用し、trueを返す要素だけの新しい配列を作ります。
   * 元の配列は変更されません（非破壊的メソッド）。
   */
  const connected = robots.filter((r) => r.state !== "disconnected").length;

  // ---------------------------------------------------------------------------
  // JSX（画面の描画部分）
  // ---------------------------------------------------------------------------

  /**
   * 【全体のレイアウト】
   * space-y-6 - 子要素間に24pxの縦方向の間隔
   *
   * 構成:
   * 1. ページタイトル「Dashboard」
   * 2. サマリーカード4枚（グリッドレイアウト）
   * 3. ロボット一覧カード
   */
  return (
    <div className="space-y-6">
      {/**
       * ページタイトル
       * text-2xl - フォントサイズ1.5rem（24px）
       * font-bold - 太字
       */}
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* ================================================================== */}
      {/* サマリーカード（概要情報カード）                                       */}
      {/* ================================================================== */}
      {/**
       * グリッドレイアウトでサマリーカードを配置
       *
       * grid - CSSグリッドレイアウトを適用
       * gap-4 - カード間の間隔を16px
       * sm:grid-cols-2 - 画面幅640px以上で2列
       * lg:grid-cols-4 - 画面幅1024px以上で4列
       *
       * 【レスポンシブデザイン】
       * sm:, lg: は「ブレークポイント」と呼ばれ、画面サイズに応じてレイアウトを変えます。
       * スマホ→1列、タブレット→2列、PC→4列 というように自動調整されます。
       *
       * 【SummaryCardコンポーネント】
       * このファイルの下部で定義されているサブコンポーネントです。
       * icon, label, value, sub という4つのpropsを受け取ります。
       */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard icon={Bot} label="Robots" value={robots.length} sub={`${connected} connected`} />
        <SummaryCard icon={Activity} label="Active" value={connected} sub="online now" />
        <SummaryCard icon={Database} label="Datasets" value={datasets.length} sub="total" />
        <SummaryCard icon={MessageSquare} label="RAG Docs" value="-" sub="uploaded" />
      </div>

      {/* ================================================================== */}
      {/* ロボット一覧                                                        */}
      {/* ================================================================== */}
      <Card>
        <CardHeader>
          {/** text-lg - フォントサイズ1.125rem（18px） */}
          <CardTitle className="text-lg">Connected Robots</CardTitle>
        </CardHeader>
        <CardContent>
          {/**
           * 条件付きレンダリング（Conditional Rendering）
           * ロボットが0台の場合と1台以上の場合で表示を切り替えます。
           *
           * {robots.length === 0 ? (表示A) : (表示B)}
           * → 三項演算子: 条件がtrueなら表示A、falseなら表示Bを描画
           *
           * 【なぜ条件分岐が必要？】
           * ロボットが登録されていない場合に空のリストを表示するのではなく、
           * 「登録されていません」というメッセージを表示する方がユーザーに親切です。
           */}
          {robots.length === 0 ? (
            /** ロボット未登録時のメッセージ */
            <p className="text-sm text-muted-foreground">No robots registered.</p>
          ) : (
            /**
             * ロボットリスト
             * space-y-3 - 各ロボットカード間に12pxの間隔
             */
            <div className="space-y-3">
              {/**
               * robots.map() - 配列の各要素をJSXに変換
               *
               * 【mapメソッドとは？】
               * 配列の各要素に関数を適用し、その結果で新しい配列を作る関数です。
               * Reactでは「配列データ → UIリスト」の変換によく使います。
               *
               * key={r.id} - Reactが各要素を識別するための一意のキー
               *   Reactは更新時に、どの要素が追加・削除・変更されたかをkeyで判断します。
               *   keyがないと警告が出て、パフォーマンスにも影響します。
               *
               * 【各ロボット行のレイアウト】
               * ┌─ 🤖 ─ Robot-A ──────────────── 100% ── connected ─┐
               * │       sim                                         │
               * └───────────────────────────────────────────────────┘
               */}
              {robots.map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded-md border p-3">
                  {/**
                   * 左側: アイコン + ロボット名 + アダプタータイプ
                   * gap-3 - 要素間の間隔12px
                   */}
                  <div className="flex items-center gap-3">
                    {/** ロボットアイコン（薄めの色で表示） */}
                    <Bot className="h-5 w-5 text-muted-foreground" />
                    <div>
                      {/** ロボット名（太字、小さいフォント） */}
                      <p className="font-medium text-sm">{r.name}</p>
                      {/**
                       * アダプタータイプ（simu, rosなど）
                       * text-xs - 極小フォント
                       */}
                      <p className="text-xs text-muted-foreground">{r.adapter_type}</p>
                    </div>
                  </div>

                  {/**
                   * 右側: バッテリー残量 + 接続状態バッジ
                   */}
                  <div className="flex items-center gap-3">
                    {/**
                     * バッテリー残量の表示
                     * r.battery_level != null → nullでもundefinedでもない場合
                     * .toFixed(0) → 小数点以下を削除して整数で表示
                     * ?? は「左側がnull/undefinedなら右側を使う」演算子
                     *
                     * 【!= null vs !== null の違い】
                     * != null は null と undefined の両方をチェック
                     * !== null は null だけをチェック
                     * battery_levelがundefinedの場合もあるので、!= を使います
                     */}
                    <span className="text-xs text-muted-foreground">
                      {r.battery_level != null ? `${r.battery_level.toFixed(0)}%` : "-"}
                    </span>
                    {/**
                     * 状態バッジ
                     * variant="outline" - 外枠だけのスタイル
                     * className={robotStateColor(r.state)} - 状態に応じた色を適用
                     *   例: connected → 緑, disconnected → 灰色
                     */}
                    <Badge variant="outline" className={robotStateColor(r.state)}>
                      {r.state}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// =============================================================================
// SummaryCard サブコンポーネント
// =============================================================================

/**
 * SummaryCard - サマリー情報を表示する小さなカードコンポーネント
 *
 * 【コンポーネントを分離する理由】
 * ダッシュボードには4つのサマリーカードがあり、全て同じ構造です。
 * コンポーネントとして分離すると:
 *   1. コードの重複を避けられる（DRY原則: Don't Repeat Yourself）
 *   2. 修正が1箇所で済む
 *   3. DashboardPageのコードが読みやすくなる
 *
 * 【propsの型定義】
 * { icon: Icon, label, value, sub } は「分割代入」で各propsを取り出します。
 * icon: Icon は「iconプロパティを受け取り、Icon変数に代入する」という書き方です。
 * コンポーネントとして使うため、大文字で始まる変数名（Icon）にリネームしています。
 *
 * 【React.ElementTypeとは？】
 * Reactコンポーネントとして使用できる任意の型を表します。
 * Bot, Activity, Database など、アイコンコンポーネントを受け取るための型です。
 *
 * 【カード内のレイアウト】
 * ┌──────────────────────┐
 * │  [アイコン]  42        │
 * │             Robots · 3 connected │
 * └──────────────────────┘
 */
function SummaryCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ElementType;    // アイコンコンポーネント
  label: string;              // ラベル（"Robots", "Active" など）
  value: string | number;     // 値（数値または文字列）
  sub: string;                // 補足テキスト（"3 connected" など）
}) {
  return (
    <Card>
      {/**
       * CardContent のカスタムレイアウト
       * flex items-center gap-4 - 横並び、中央揃え、要素間16px
       * p-6 - 内側の余白24px
       */}
      <CardContent className="flex items-center gap-4 p-6">
        {/**
         * アイコンの背景
         * h-10 w-10 - 40x40pxの正方形
         * rounded-lg - 角丸（大きめ）
         * bg-primary/10 - プライマリカラーの10%透明度
         */}
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          {/** 受け取ったアイコンコンポーネントを描画 */}
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          {/** 値の表示（大きな太字フォント） */}
          <p className="text-2xl font-bold">{value}</p>
          {/**
           * ラベルと補足テキスト
           * 「·」(中黒)でラベルと補足を区切って表示
           */}
          <p className="text-xs text-muted-foreground">
            {label} · {sub}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
