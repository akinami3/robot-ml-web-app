// =============================================================================
// primitives.tsx - 共通UIプリミティブ（基本UIコンポーネント集）
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、アプリ全体で使用する基本的なUI部品（プリミティブ）を
// まとめて定義しています。Button、Card、Input、Badge、Label、Textarea、Select
// といった、Webアプリの基盤となるコンポーネントが含まれています。
//
// 【なぜプリミティブを自作するのか？】
// 1. 一貫したデザイン: アプリ全体で統一されたスタイルを保てる
// 2. 再利用性: 同じコンポーネントをどこでも使い回せる
// 3. メンテナンス性: スタイルを変更する時、1箇所の修正で全体に反映される
// 4. 軽量化: 必要なコンポーネントだけを自作することで、大きなUIライブラリに
//    依存せずに済む
//
// 【Tailwind CSSの設計システムについて】
// このファイルでは Tailwind CSS のユーティリティクラスを多用しています。
// Tailwind CSSは「ユーティリティファースト」のCSSフレームワークで、
// 小さなクラスを組み合わせてスタイルを構築します。
// 例: "bg-primary text-white px-4 py-2 rounded-md"
//   → 背景色=primary, 文字色=白, 左右余白=16px, 上下余白=8px, 角丸=中
//
// 【デザイントークン（CSS変数）について】
// "bg-primary", "text-muted-foreground", "border-input" などのクラスは、
// カスタムCSS変数（デザイントークン）を参照しています。
// これにより、ダークモードやテーマ切り替えに対応できます。
// =============================================================================

// -----------------------------------------------------------------------------
// インポート部分
// -----------------------------------------------------------------------------

// React: ReactライブラリのメインインポートReact本体のインポート
// React.forwardRef や React.ButtonHTMLAttributes などの型にアクセスするために必要
import React from "react";

// cn: クラス名（className）を結合するユーティリティ関数
// 【cn関数の仕組み】
// 内部では clsx と tailwind-merge を組み合わせて使っている
// - clsx: 条件付きでクラス名を結合する（falsy値は無視される）
// - tailwind-merge: 重複するTailwindクラスを賢くマージする
//   例: cn("px-2", "px-4") → "px-4"（後のクラスが勝つ）
import { cn } from "@/lib/utils";

// =============================================================================
// Button（ボタン）コンポーネント
// =============================================================================

// -- Button ---------------------------------------------------------------

// 【interface ... extends とは？】
// TypeScriptの「extends」は、既存の型を「継承（拡張）」すること。
// React.ButtonHTMLAttributes<HTMLButtonElement> は、HTMLの<button>要素が
// 持つすべての属性（onClick, disabled, type, など）の型定義。
// つまり、ButtonPropsは通常のボタン属性 + 独自のvariantとsizeを持つ。
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  // variant: ボタンの見た目のバリエーション（種類）
  // "?" はオプショナル（省略するとデフォルト値が適用される）
  //
  // - "default": 主要アクション用のメインボタン（例: 送信、保存）
  // - "destructive": 危険な操作用の赤いボタン（例: 削除）
  // - "outline": 枠線だけのボタン（補助的なアクション）
  // - "ghost": 背景なしのボタン（ホバー時のみ背景が出る）
  // - "link": リンクのように見えるボタン（下線付き）
  variant?: "default" | "destructive" | "outline" | "ghost" | "link";

  // size: ボタンのサイズ
  // - "default": 通常サイズ
  // - "sm": 小さいサイズ
  // - "lg": 大きいサイズ
  // - "icon": アイコンだけのボタン（正方形）
  size?: "default" | "sm" | "lg" | "icon";
}

// 【Record<string, string> とは？】
// TypeScriptのユーティリティ型の1つ。
// Record<キーの型, 値の型> = 「キーが文字列、値も文字列」のオブジェクト型
// つまり { [key: string]: string } と同じ意味。
// ここでは variant名 → Tailwindクラスの対応表（マッピング）として使用

// variantStyles: 各バリアントに対応するTailwindクラスのマッピング
const variantStyles: Record<string, string> = {
  // default: プライマリカラーの背景と前景色。ホバー時に90%の不透明度
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  // destructive: 赤系の破壊的アクション用カラー
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  // outline: 枠線付き、透明背景。ホバー時にアクセント色の背景が出る
  outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
  // ghost: 通常時は完全に透明。ホバー時のみ背景色が表示される
  ghost: "hover:bg-accent hover:text-accent-foreground",
  // link: テキストリンクのスタイル。下線のオフセットとホバー時の下線表示
  link: "text-primary underline-offset-4 hover:underline",
};

// sizeStyles: 各サイズに対応するTailwindクラスのマッピング
const sizeStyles: Record<string, string> = {
  // default: 高さ40px、左右に16px上下に8pxの余白
  default: "h-10 px-4 py-2",
  // sm: 高さ36px、角丸md、左右に12pxの余白
  sm: "h-9 rounded-md px-3",
  // lg: 高さ44px、角丸md、左右に32pxの余白
  lg: "h-11 rounded-md px-8",
  // icon: 40px × 40pxの正方形（アイコンのみのボタン用）
  icon: "h-10 w-10",
};

// 【React.forwardRef とは？】
// forwardRefは、親コンポーネントから子コンポーネント内のDOM要素に
// 直接アクセスするための「参照（ref）」を転送する仕組みです。
//
// 【なぜforwardRefが必要？】
// 通常、Reactコンポーネントにrefを渡しても、内部のDOM要素には届きません。
// forwardRefを使うことで、<Button ref={myRef} /> と書くと、
// myRefが内部の<button>要素を直接参照できるようになります。
// これはフォームライブラリやアニメーションライブラリで必要になることが多いです。
//
// React.forwardRef<参照先のDOM型, propsの型>
// - 第1引数型: HTMLButtonElement → 実際のHTMLボタン要素
// - 第2引数型: ButtonProps → このコンポーネントのprops
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  // forwardRefの第1引数は、propsとrefを受け取る関数
  // ({ className, variant, size, ...props }, ref) の部分で：
  // - className, variant, size は個別に取り出す
  // - ...props は「残りの全てのprops」をまとめて受け取る（スプレッド構文）
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    // 実際にレンダリングされるHTML <button> 要素
    <button
      // ref: 親から転送されたrefを<button>要素に設定
      ref={ref}
      // cn(): 複数のTailwindクラスを結合
      className={cn(
        // ベーススタイル: すべてのボタンに共通するスタイル
        // inline-flex: インラインレベルのFlexbox
        // items-center justify-center: 中身を上下左右中央揃え
        // whitespace-nowrap: テキストの折り返しを禁止
        // rounded-md: 中程度の角丸
        // text-sm: 小さめのテキスト
        // font-medium: やや太い文字
        // ring-offset-background: フォーカスリングのオフセット色
        // transition-colors: 色の変化にアニメーションを適用
        "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors",
        // フォーカス時のスタイル: キーボード操作でフォーカスした時のリング表示
        // focus-visible: Tab キーなどでフォーカスした時のみ適用（クリック時は不適用）
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        // 無効（disabled）状態のスタイル
        // pointer-events-none: クリック不可
        // opacity-50: 半透明にする
        "disabled:pointer-events-none disabled:opacity-50",
        // variantとsizeに応じたスタイルを適用（上で定義したマッピングから取得）
        variantStyles[variant],
        sizeStyles[size],
        // 親から渡されたclassNameがあれば追加（カスタマイズ用）
        className
      )}
      // ...props: onClick, disabled, type などの残りのpropsをすべて<button>に転送
      {...props}
    />
  )
);
// displayName: React DevToolsでコンポーネント名を表示するために設定
// forwardRefを使うと匿名コンポーネントになるため、明示的に名前を付ける
Button.displayName = "Button";

// =============================================================================
// Card（カード）コンポーネント群
// =============================================================================

// -- Card -----------------------------------------------------------------

// 【React.HTMLAttributes<HTMLDivElement> とは？】
// HTMLの<div>要素が持つすべての属性（className, onClick, style, id, など）の型。
// これをpropsの型として使うことで、通常のdivと同じ属性を受け付けられる。

// Card: カード全体の外枠コンポーネント
// 角丸のボーダー、背景色、影（shadow）を持つ箱を描画する
export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  // rounded-lg: 大きめの角丸
  // border: 細い枠線
  // bg-card: カード専用の背景色（テーマ対応）
  // text-card-foreground: カード専用の文字色
  // shadow-sm: 軽い影（奥行き感を出す）
  return <div className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />;
}

// CardHeader: カードの上部（ヘッダー）コンポーネント
// タイトルやサブタイトルを配置する領域
export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  // flex flex-col: 子要素を縦方向に並べる
  // space-y-1.5: 子要素間に0.375remの間隔
  // p-6: 全方向に1.5rem（24px）のパディング
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

// CardTitle: カードのタイトルコンポーネント
// h3要素（見出しレベル3）として描画される
export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  // text-2xl: 大きめのテキスト（24px）
  // font-semibold: やや太い文字
  // leading-none: 行の高さをテキストサイズと同じにする
  // tracking-tight: 文字間隔をやや詰める
  return <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}

// CardContent: カードのメインコンテンツ部分コンポーネント
export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  // p-6 pt-0: 全方向に1.5remのパディング、ただし上だけ0（ヘッダーとの隙間を避ける）
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

// =============================================================================
// Input（テキスト入力欄）コンポーネント
// =============================================================================

// -- Input ----------------------------------------------------------------

// 【React.InputHTMLAttributes<HTMLInputElement>】
// HTMLの<input>要素が持つすべての属性の型。
// type, placeholder, value, onChange, disabled, maxLength などを含む。
export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        // h-10 w-full: 高さ40px、幅100%
        // rounded-md: 中程度の角丸
        // border border-input: 入力欄用の枠線
        // bg-background: テーマに応じた背景色
        // px-3 py-2: 左右12px、上下8pxの余白
        // text-sm: 小さめのテキスト
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
        // file:〜: ファイル選択ボタンのスタイル（<input type="file">用）
        // ring-offset-background: フォーカスリングのオフセット色
        "ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium",
        // placeholder: プレースホルダーテキストの色
        // focus-visible: キーボードフォーカス時のリング表示
        "placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        // disabled: 無効状態のスタイル（カーソルを「禁止」に変更し半透明に）
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
// displayName: React DevToolsでの表示名を設定
Input.displayName = "Input";

// =============================================================================
// Badge（バッジ）コンポーネント
// =============================================================================

// -- Badge ----------------------------------------------------------------

// 【バッジとは？】
// ステータスやカテゴリを示す小さなラベル。
// 例: 「オンライン」「新着」「エラー」などの状態表示に使用。

// BadgeProps: Badge専用のprops型
// React.HTMLAttributes<HTMLSpanElement> を継承（<span>の全属性を受け付ける）
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  // variant: バッジの見た目のバリエーション
  // - "default": メインカラーの背景
  // - "secondary": セカンダリカラーの背景
  // - "destructive": エラー・警告用の赤い背景
  // - "outline": 枠線のみ（背景なし）
  variant?: "default" | "secondary" | "destructive" | "outline";
}

// badgeVariants: 各バリアントのスタイルマッピング
const badgeVariants: Record<string, string> = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  outline: "border text-foreground",
};

// Badge コンポーネント本体
export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        // inline-flex: インラインのFlexbox
        // items-center: 中身を上下中央揃え
        // rounded-full: 完全な角丸（丸いピル形状）
        // px-2.5 py-0.5: 左右10px、上下2pxの余白
        // text-xs: 非常に小さいテキスト（12px）
        // font-semibold: やや太い文字
        // transition-colors: 色変化にアニメーション
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
        // バリアントに応じたスタイルを適用
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  );
}

// =============================================================================
// Label（ラベル）コンポーネント
// =============================================================================

// -- Label ----------------------------------------------------------------

// 【<label>要素とは？】
// フォーム入力欄に関連付けられるテキストラベル。
// htmlFor属性やfor属性を使って、クリック時に対応する入力欄にフォーカスを移せる。
// アクセシビリティ（障害のあるユーザーへの対応）のためにも重要。

export const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        // text-sm font-medium leading-none: 小さめで太い文字、行の高さ = テキストサイズ
        // peer-disabled:〜: 兄弟要素（peer）がdisabledの時のスタイル
        //   Tailwind CSSの「peer」修飾子を使い、関連する入力欄が無効な時に
        //   ラベルのカーソルを「禁止」にし、半透明にする
        "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        className
      )}
      {...props}
    />
  )
);
Label.displayName = "Label";

// =============================================================================
// Textarea（テキストエリア / 複数行テキスト入力欄）コンポーネント
// =============================================================================

// -- Textarea -------------------------------------------------------------

// 【TextareaとInputの違い】
// Input: 1行のテキスト入力（名前、メールアドレスなど短い入力用）
// Textarea: 複数行のテキスト入力（コメント、説明文など長い入力用）

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        // min-h-[80px]: 最小高さ80px（Tailwindのarbitrary value記法）
        // w-full: 幅100%
        // その他はInputとほぼ同じスタイル
        "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
        "ring-offset-background placeholder:text-muted-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

// =============================================================================
// Select（セレクトボックス / ドロップダウン選択欄）コンポーネント
// =============================================================================

// -- Select ---------------------------------------------------------------

// 【<select>要素とは？】
// ドロップダウンリストから選択肢を選ぶためのフォーム要素。
// 子要素として<option>を持ち、ユーザーが1つ（または複数）を選択できる。
// 例:
//   <Select>
//     <option value="manual">手動操作</option>
//     <option value="auto">自動運転</option>
//   </Select>

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        // Inputとほぼ同じスタイル（統一感のあるフォームデザイン）
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
        "ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Select.displayName = "Select";
