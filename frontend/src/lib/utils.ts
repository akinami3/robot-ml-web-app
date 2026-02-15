/**
 * utils.ts - ユーティリティ関数（汎用的な便利関数）の定義ファイル
 *
 * =====================================================================
 * 📁 ファイルの概要（このファイルが何をするか）
 * =====================================================================
 * このファイルには、アプリケーション全体で再利用する「ユーティリティ関数」
 * （便利関数）をまとめています。
 *
 * 各関数の役割：
 * 1. cn() - CSSクラス名を条件付きで結合する関数
 * 2. formatBytes() - バイト数を人間が読みやすい形式に変換する関数
 * 3. formatDuration() - 秒数を時間・分・秒の形式に変換する関数
 * 4. robotStateColor() - ロボットの状態に応じたCSSクラス名を返す関数
 *
 * 💡 ユーティリティ関数とは？
 * - 特定の機能に依存しない、汎用的な関数のこと
 * - どのコンポーネントからでも使える共通処理をまとめる
 * - DRY原則（Don't Repeat Yourself = 同じコードを繰り返し書かない）に基づく
 * =====================================================================
 */

// === インポート部分 ===

// clsx: 複数のCSSクラス名を条件付きで結合するライブラリ
// - 使い方: clsx("btn", isActive && "btn-active", "mt-4")
//   → isActive が true なら "btn btn-active mt-4"
//   → isActive が false なら "btn mt-4"（falsy な値は無視される）
// - 条件分岐を含むクラス名の結合がシンプルに書ける
//
// type ClassValue: clsx が受け付ける引数の型定義
// - string, number, boolean, undefined, null, 配列、オブジェクトなどを受け付ける
// - import type: 型だけをインポート（実行時にはコードに含まれない）
import { clsx, type ClassValue } from "clsx";

// twMerge: Tailwind CSSのクラス名をインテリジェントにマージ（結合）するライブラリ
// - 通常のクラス結合: "p-4 p-2" → "p-4 p-2"（競合がそのまま残る）
// - twMerge を使用: "p-4 p-2" → "p-2"（後から指定した方が優先される）
// - Tailwind CSSでは同じプロパティのクラスが重複すると予期しない動作になるため、
//   twMerge で重複を解決するのがベストプラクティス
import { twMerge } from "tailwind-merge";

// =====================================================================
// 🎨 cn() - CSSクラス名を結合する関数
// =====================================================================
// Tailwind CSS のクラス名を安全に結合するユーティリティ関数
// shadcn/ui（UIコンポーネントライブラリ）で標準的に使われるパターン
//
// 💡 レストパラメータ（...）とは？
// - ...inputs: ClassValue[] → 任意の個数の引数を配列として受け取る
// - 例: cn("a", "b", "c") → inputs = ["a", "b", "c"]
// - 例: cn("a") → inputs = ["a"]
// - 引数の数が不定（何個でもOK）な関数を作るときに使う
//
// 使用例：
// cn("px-4 py-2", isActive && "bg-blue-500", "rounded")
// → isActive が true: "px-4 py-2 bg-blue-500 rounded"
// → isActive が false: "px-4 py-2 rounded"
//
// 処理の流れ：
// 1. clsx(...inputs) → 条件付きでクラス名を結合（falsy値を除外）
// 2. twMerge(...) → Tailwind CSSの競合するクラスを解決
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// =====================================================================
// 📏 formatBytes() - バイト数を人間が読みやすい形式に変換する関数
// =====================================================================
// 例: formatBytes(0) → "0 B"
// 例: formatBytes(1024) → "1 KB"
// 例: formatBytes(1536) → "1.5 KB"
// 例: formatBytes(1073741824) → "1 GB"
//
// 💡 なぜこの関数が必要？
// - ファイルサイズは通常バイト単位の大きな数値で返ってくる
// - "1073741824 bytes" より "1 GB" の方がユーザーにわかりやすい
//
// 引数:
// - bytes: number → 変換したいバイト数
// 戻り値:
// - string → フォーマットされた文字列（例: "1.5 KB"）
export function formatBytes(bytes: number): string {
  // 0バイトの場合は特別に処理（Math.log(0) は -Infinity になるため）
  if (bytes === 0) return "0 B";

  // k = 1024: 1KB = 1024バイト（2の10乗）
  // - コンピュータの世界では 1024 = 2^10 が基本単位
  const k = 1024;

  // sizes: 単位の配列
  // - インデックス 0 = "B"（バイト）
  // - インデックス 1 = "KB"（キロバイト）
  // - インデックス 2 = "MB"（メガバイト）
  // - インデックス 3 = "GB"（ギガバイト）
  const sizes = ["B", "KB", "MB", "GB"];

  // i: 適切な単位のインデックスを計算する
  //
  // 💡 Math.log() とは？
  // - 自然対数（底がe≒2.718のlog）を計算する数学関数
  // - Math.log(bytes) / Math.log(k) は「kを底とするbytesの対数」
  //   → つまり「1024を何回掛けたらbytesになるか」を計算している
  // - 例: bytes=1024 → log(1024)/log(1024) = 1 → インデックス1 = "KB"
  // - 例: bytes=1048576 → log(1048576)/log(1024) = 2 → インデックス2 = "MB"
  //
  // 💡 Math.floor() とは？
  // - 小数点以下を切り捨てて整数にする関数
  // - Math.floor(1.7) → 1
  // - Math.floor(2.999) → 2
  // - 配列のインデックスには整数が必要なので切り捨てる
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  // 結果を組み立てて返す
  //
  // 💡 テンプレートリテラル（`${...}`）とは？
  // - バッククォート（`）で囲んだ文字列内に、${式} で値を埋め込む機能
  // - 例: `Hello ${name}!` → name が "太郎" なら "Hello 太郎!"
  // - 文字列連結（"Hello " + name + "!"）より読みやすい
  //
  // Math.pow(k, i): kのi乗を計算する（例: Math.pow(1024, 2) = 1048576）
  // bytes / Math.pow(k, i): バイト数を適切な単位に変換
  // .toFixed(1): 小数点以下1桁に丸める（例: 1.5678 → "1.6"）
  // parseFloat(): 文字列を浮動小数点数に変換（余分な0を除去）
  //   → "1.0" → 1 になり、"1.5" → 1.5 のまま
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// =====================================================================
// ⏱️ formatDuration() - 秒数を時間・分・秒の形式に変換する関数
// =====================================================================
// 例: formatDuration(65) → "1m 5s"
// 例: formatDuration(3661) → "1h 1m 1s"
// 例: formatDuration(30) → "30s"
//
// 引数:
// - seconds: number → 変換したい秒数
// 戻り値:
// - string → フォーマットされた文字列（例: "1h 30m 15s"）
export function formatDuration(seconds: number): string {
  // h: 時間数を計算
  // 3600 = 60分 × 60秒（1時間の秒数）
  // Math.floor で小数点以下を切り捨て
  const h = Math.floor(seconds / 3600);

  // m: 分数を計算
  // seconds % 3600: 時間を引いた残りの秒数
  //   - %（剰余演算子）: 割り算の余りを求める
  //   - 例: 3661 % 3600 = 61（61秒が残る）
  // / 60: 秒を分に変換
  // Math.floor: 端数を切り捨て
  const m = Math.floor((seconds % 3600) / 60);

  // s: 秒数を計算
  // seconds % 60: 60で割った余り = 分に収まらない残りの秒数
  const s = Math.floor(seconds % 60);

  // 条件に応じてフォーマットを変える
  // - 1時間以上: "1h 30m 15s"
  // - 1分以上: "30m 15s"
  // - 1分未満: "15s"
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

// =====================================================================
// 🤖 robotStateColor() - ロボット状態に応じたCSSクラス名を返す関数
// =====================================================================
// ロボットの状態に応じて、TailwindCSSのカスタムカラークラスを返す
// UIでロボットの状態を色で視覚的に表現するために使用
//
// 💡 「単一責任の原則」: この関数は「状態→色の変換」だけを担当する
// → UIロジック（表示）とビジネスロジック（状態管理）を分離する設計
//
// 引数:
// - state: string → ロボットの状態文字列
// 戻り値:
// - string → TailwindCSSのカラークラス名
//
// 使用例:
// <span className={robotStateColor(robot.state)}>{robot.state}</span>
export function robotStateColor(state: string): string {
  // switch文でstateの値に応じてクラス名を返す
  switch (state) {
    // アイドル状態 → アイドル色（通常は緑系）
    case "idle":
      return "text-robot-idle";

    // 移動中 → 移動中色（通常は青系）
    case "moving":
      return "text-robot-moving";

    // エラーまたは緊急停止 → エラー色（通常は赤系）
    // 💡 複数のcaseをまとめる（フォールスルー）:
    // case "error": の後に break がないので、次の case も実行される
    // → "error" と "emergency_stopped" の両方が同じ処理になる
    case "error":
    case "emergency_stopped":
      return "text-robot-error";

    // 上記以外の状態（"disconnected", "connecting" など）→ 切断色（通常はグレー系）
    // default: どの case にも一致しなかった場合の処理
    default:
      return "text-robot-disconnected";
  }
}
