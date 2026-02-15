// =============================================================================
// TailwindCSS 設定ファイル（tailwind.config.js）
// =============================================================================
//
// 【TailwindCSSとは？】
// ユーティリティファースト（Utility-First）のCSSフレームワークです。
// 従来のCSS: クラス名を考えてCSSファイルにスタイルを書く
// Tailwind:  HTMLに直接ユーティリティクラスを書く
//
// 例（従来のCSS）:
//   <button class="submit-btn">送信</button>
//   .submit-btn { background: blue; color: white; padding: 8px 16px; border-radius: 4px; }
//
// 例（TailwindCSS）:
//   <button class="bg-blue-500 text-white px-4 py-2 rounded">送信</button>
//
// 【メリット】
// - CSSファイルが肥大化しない（使用クラスのみ生成）
// - クラス名を考える必要がない
// - デザインの一貫性を保てる（色やサイズが規格化されている）
// =============================================================================

// 【@type アノテーション】TypeScriptの型情報をJSDocコメントで指定
// エディタの自動補完（IntelliSense）が効くようになります
/** @type {import('tailwindcss').Config} */
export default {
  // ===========================================================================
  // content: Tailwindがクラスを検索するファイルのパス
  // ===========================================================================
  // 【content配列】Tailwindがスキャンするファイルを指定
  // これらのファイル内で使われているTailwindクラスだけがCSSに含まれます
  // 未使用のクラスは自動的に除外される（Tree Shaking / Purge）
  //
  // "./index.html"          → ルートのHTMLファイル
  // "./src/**/*.{js,ts,jsx,tsx}" → src/ 配下のすべてのJS/TSファイル
  //   ** は任意の深さのサブディレクトリにマッチ
  //   {js,ts,jsx,tsx} は複数の拡張子にマッチ
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],

  // ===========================================================================
  // darkMode: ダークモードの切り替え方式
  // ===========================================================================
  // 【"class" モード】HTMLの最上位要素に "dark" クラスを追加してダークモードを切り替え
  //   <html class="dark"> → ダークモード
  //   <html>             → ライトモード
  //
  // 使い方: className="bg-white dark:bg-gray-900"
  //   → ライトモード: 白背景 / ダークモード: 濃いグレー背景
  //
  // 他の方式:
  //   "media" → OSのダークモード設定に自動追従（prefers-color-scheme）
  //   "class" → JavaScriptで手動切り替え（ユーザーの好みに対応可能）
  darkMode: "class",

  // ===========================================================================
  // theme: デザインテーマのカスタマイズ
  // ===========================================================================
  theme: {
    // 【extend】既存のTailwindのデフォルトテーマを拡張（上書きではなく追加）
    // extend を使わずに直接指定すると、デフォルトの色やサイズが消えてしまう
    extend: {
      // =====================================================================
      // カスタムカラー（色の定義）
      // =====================================================================
      // 【CSS変数 + HSL を使ったカラーシステム】
      // HSL = Hue（色相）, Saturation（彩度）, Lightness（明度）
      //
      // なぜCSS変数（var(--xxx)）を使う？
      //   → ダークモード切り替え時に、CSS変数の値を変えるだけで
      //     全体の色が切り替わる（各コンポーネントを変更する必要がない）
      //
      // 例: --background: 0 0% 100%（ライト: 白）
      //     --background: 0 0% 4%（ダーク: ほぼ黒）
      //     → bg-background クラスが自動的に適切な色になる
      colors: {
        // 【UIコンポーネント用の色】shadcn/ui のカラーシステム
        // 各色はCSS変数から値を取得するため、テーマの切り替えが容易
        border: "hsl(var(--border))",           // ボーダー（枠線）の色
        input: "hsl(var(--input))",             // 入力フィールドの枠線色
        ring: "hsl(var(--ring))",               // フォーカスリングの色
        background: "hsl(var(--background))",   // ページの背景色
        foreground: "hsl(var(--foreground))",   // メインのテキスト色

        // 【primary】メインの強調色（ボタン、リンクなど）
        // DEFAULT: クラス名に色名だけ使った場合の色（例: bg-primary）
        // foreground: その上に乗るテキストの色（例: ボタンの文字色）
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },

        // 【secondary】副次的な強調色（サブボタンなど）
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },

        // 【destructive】危険な操作を示す色（削除ボタンなど）
        // 通常は赤系の色を設定します
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },

        // 【muted】控えめな要素の色（補助テキスト、無効状態など）
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },

        // 【accent】アクセント色（ホバー時のハイライトなど）
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },

        // 【card】カードコンポーネントの色
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },

        // 【estop】緊急停止（Emergency Stop）ボタン専用の色
        // ロボット制御において最も重要な安全機能
        // 鮮やかな赤色 #FF0000 で、目立つようにしています
        estop: "#FF0000",

        // 【robot】ロボットの状態表示に使う色
        // ダッシュボードでロボットの現在の状態を色で直感的に示します
        robot: {
          idle: "#22c55e",          // 待機中: 緑（正常・準備OK）
          moving: "#3b82f6",        // 移動中: 青（動作中）
          error: "#ef4444",         // エラー: 赤（問題発生）
          disconnected: "#6b7280",  // 切断: グレー（通信なし）
        },
      },

      // =====================================================================
      // カスタム border-radius（角丸の設定）
      // =====================================================================
      // CSS変数 --radius を基準にして、統一感のある角丸を定義
      // 例: --radius: 0.5rem（8px）の場合
      //   lg: 0.5rem（8px）, md: 0.375rem（6px）, sm: 0.25rem（4px）
      borderRadius: {
        lg: "var(--radius)",                    // 大きい角丸
        md: "calc(var(--radius) - 2px)",        // 中くらいの角丸
        sm: "calc(var(--radius) - 4px)",        // 小さい角丸
      },

      // =====================================================================
      // カスタムキーフレームアニメーション
      // =====================================================================
      // 【keyframes】CSSアニメーションの動きを定義
      // @keyframes ルールと同等の機能をTailwindの設定で定義できます
      keyframes: {
        // 【estop-pulse】緊急停止ボタンの点滅アニメーション
        // ロボットが緊急停止状態のとき、注意を引くために
        // ボタンを点滅（パルス）させます
        //
        // 0%（開始）→ 50%（中間）→ 100%（終了）の順に変化
        //   0%, 100%: opacity 1（完全に表示）
        //   50%:      opacity 0.5（半透明）
        // → ゆっくり明滅を繰り返す効果
        "estop-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },

      // =====================================================================
      // カスタムアニメーション
      // =====================================================================
      // 【animation】上で定義したkeyframesを使ったアニメーションの設定
      // CSSの animation プロパティのショートハンド形式
      animation: {
        // 【estop-pulse アニメーション】
        // "estop-pulse"  → 使用するkeyframes名
        // "1s"           → 1回のアニメーションにかかる時間
        // "ease-in-out"  → 速度変化（ゆっくり始まり、ゆっくり終わる）
        // "infinite"     → 無限に繰り返し
        //
        // 使い方: className="animate-estop-pulse"
        "estop-pulse": "estop-pulse 1s ease-in-out infinite",
      },
    },
  },

  // ===========================================================================
  // plugins: Tailwindの機能を追加するプラグイン
  // ===========================================================================
  // 現在はプラグインなし
  // よく使われるプラグインの例:
  //   @tailwindcss/forms     → フォーム要素のスタイルをリセット
  //   @tailwindcss/typography → 記事・文章向けの美しいタイポグラフィ
  //   @tailwindcss/aspect-ratio → アスペクト比の制御
  plugins: [],
};
