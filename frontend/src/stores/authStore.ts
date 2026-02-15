// =============================================================================
// authStore.ts — 認証（ログイン）状態を管理するストア
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、アプリケーション全体で「ユーザーがログインしているかどうか」
// 「誰がログインしているか」「どんな権限を持っているか」を管理します。
//
// 【なぜこのファイルが必要？】
// Webアプリでは、ログイン状態を複数のページやコンポーネントで共有する必要があります。
// 例えば、ヘッダーにユーザー名を表示したり、特定のページへのアクセスを制限したり。
// Zustand を使うことで、どのコンポーネントからでも簡単にログイン状態にアクセスできます。
//
// 【使われている技術】
// - Zustand: React用の軽量な状態管理ライブラリ（Reduxより簡単に使える）
// - persist ミドルウェア: ブラウザのlocalStorageに状態を保存し、ページ更新後も維持
// - JWT (JSON Web Token): ログイン認証に使われるトークン方式
//
// 【JWT認証の仕組み（初心者向け）】
// 1. ユーザーがログインすると、サーバーから「accessToken」と「refreshToken」が返される
// 2. accessToken: APIリクエストごとに送信する短期間のパスポートのようなもの
// 3. refreshToken: accessTokenの有効期限が切れたとき、新しいものを取得するための鍵
// 4. これらのトークンをブラウザに保存しておくことで、ログイン状態を維持する
// =============================================================================

// ---------------------------------------------------------------------------
// 【インポート】
// ---------------------------------------------------------------------------

// create: Zustandのストア（状態の入れ物）を作るための関数
// Zustandは「ズスタンド」と読み、ドイツ語で「状態」を意味します
import { create } from "zustand";

// persist: Zustandの「ミドルウェア」（追加機能）
// これを使うと、ストアの状態がブラウザのlocalStorageに自動保存されます
// → ページをリロードしても、ログイン状態が失われません
import { persist } from "zustand/middleware";

// AuthTokens: サーバーから返されるトークンペアの型（access_token と refresh_token）
// User: ユーザー情報（名前、メール、役割など）を表す型
// UserRole: ユーザーの役割（"admin" | "operator" | "viewer" など）を表す型
// 「type」キーワード: 型だけをインポート（実行時には消える。コードサイズに影響しない）
import type { AuthTokens, User, UserRole } from "@/types";

// ---------------------------------------------------------------------------
// 【インターフェース定義】AuthState — ストアが持つデータと関数の設計図
// ---------------------------------------------------------------------------
// TypeScriptの「interface」は、オブジェクトの形（どんなプロパティがあるか）を
// 事前に定義するものです。これにより、タイプミスや間違った使い方を防げます。
// ---------------------------------------------------------------------------
interface AuthState {
  // --- データ（ストアが保持する値） ---

  // accessToken: APIリクエスト時に「自分はログイン済みです」と証明するトークン
  // null = まだログインしていない状態
  accessToken: string | null;

  // refreshToken: accessTokenの有効期限が切れたとき、新しいものを取得するためのトークン
  // null = まだログインしていない状態
  refreshToken: string | null;

  // user: 現在ログインしているユーザーの情報（名前、メール、役割など）
  // null = ログインしていない
  user: User | null;

  // isAuthenticated: ログイン済みかどうかを示すフラグ（true/false）
  // accessToken の有無でも判断できるが、明示的なフラグがあると便利
  isAuthenticated: boolean;

  // --- アクション（ストアの値を変更する関数） ---

  // setTokens: ログイン成功時に、サーバーから受け取ったトークンペアを保存する関数
  // AuthTokens型のオブジェクト（access_token, refresh_token を含む）を受け取る
  setTokens: (tokens: AuthTokens) => void;

  // setUser: ログイン後にユーザー情報を保存する関数
  setUser: (user: User) => void;

  // logout: ログアウト時にすべての認証情報をクリアする関数
  logout: () => void;

  // hasRole: 指定された役割（権限）のいずれかを持っているかチェックする関数
  // ...roles は「残余引数（レストパラメータ）」: 任意の数の引数を配列として受け取る
  // 例: hasRole("admin", "operator") → adminまたはoperatorか？
  hasRole: (...roles: UserRole[]) => boolean;

  // canControlRobot: ロボットを操作する権限があるかチェックする関数
  // admin（管理者）または operator（操作者）のみ操作可能
  canControlRobot: () => boolean;
}

// ---------------------------------------------------------------------------
// 【ストアの作成】useAuthStore — 認証状態を管理するZustandストア
// ---------------------------------------------------------------------------
//
// 【Zustandストアの基本パターン】
// const useXxxStore = create<型>()((set, get) => ({
//   状態1: 初期値,
//   状態2: 初期値,
//   アクション1: (引数) => set({ 状態1: 新しい値 }),
//   アクション2: () => { const 現在の値 = get().状態1; ... },
// }));
//
// - set: ストアの状態を更新する関数（Reactが自動的に再レンダリングする）
// - get: ストアの現在の状態を読み取る関数（set内では使えないときに便利）
//
// 【なぜ export const？】
// 他のファイル（コンポーネントなど）からインポートして使えるようにするため
// 使い方: const token = useAuthStore((s) => s.accessToken);
// ---------------------------------------------------------------------------
export const useAuthStore = create<AuthState>()(
  // persist() で囲むことで、状態がブラウザのlocalStorageに自動保存される
  // → ブラウザを閉じて再度開いても、ログイン状態が維持される
  persist(
    // (set, get) => ({...}) — ストアの中身を定義するコールバック関数
    // set: 状態を更新する関数
    // get: 現在の状態を取得する関数
    (set, get) => ({
      // --- 初期状態（アプリ起動時の値） ---
      // すべてnull/false = ログインしていない状態からスタート
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      // -------------------------------------------------------------------
      // 【アクション: setTokens】トークンペアを保存する
      // -------------------------------------------------------------------
      // ログイン成功時やトークンリフレッシュ時に呼ばれる
      // AuthTokens オブジェクトから access_token, refresh_token を取り出して保存
      // 同時に isAuthenticated を true に設定（ログイン済みフラグ）
      setTokens: (tokens: AuthTokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
        }),

      // -------------------------------------------------------------------
      // 【アクション: setUser】ユーザー情報を保存する
      // -------------------------------------------------------------------
      // ログイン後にサーバーから取得したユーザー情報を保存する
      // { user } は { user: user } の省略記法（ES6のショートハンドプロパティ）
      setUser: (user: User) => set({ user }),

      // -------------------------------------------------------------------
      // 【アクション: logout】ログアウト処理
      // -------------------------------------------------------------------
      // すべての認証情報をnull/falseに戻す（= 未ログイン状態に戻す）
      // localStorageからも自動的に削除される（persistミドルウェアのおかげ）
      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),

      // -------------------------------------------------------------------
      // 【アクション: hasRole】権限チェック
      // -------------------------------------------------------------------
      // 指定された役割（role）のいずれかをユーザーが持っているかどうかを判定する
      //
      // 【...roles（残余引数 / レストパラメータ）とは？】
      // 任意の数の引数を1つの配列にまとめて受け取る構文
      // 例: hasRole("admin", "operator") → roles = ["admin", "operator"]
      //
      // 【includes() メソッド】
      // 配列に指定した要素が含まれているかをチェック
      // 例: ["admin", "operator"].includes("admin") → true
      //
      // 【三項演算子 条件 ? 値A : 値B】
      // user が存在すれば roles に含まれるかチェック、なければ false
      hasRole: (...roles: UserRole[]) => {
        const user = get().user;
        return user ? roles.includes(user.role) : false;
      },

      // -------------------------------------------------------------------
      // 【アクション: canControlRobot】ロボット操作権限チェック
      // -------------------------------------------------------------------
      // ロボットを操作できるかどうかを判定する便利関数
      // admin または operator のみ操作可能
      //
      // 【includes() の別の使い方】
      // 文字列の配列リテラル ["admin", "operator"] で直接チェック
      // → user.role が "admin" か "operator" のどちらかなら true
      canControlRobot: () => {
        const user = get().user;
        return user ? ["admin", "operator"].includes(user.role) : false;
      },
    }),
    // -------------------------------------------------------------------
    // 【persist ミドルウェアの設定オブジェクト】
    // -------------------------------------------------------------------
    {
      // name: localStorageに保存するときのキー名
      // ブラウザの開発者ツール → Application → Local Storage で確認できる
      name: "robot-ai-auth",

      // partialize: ストアの状態のうち、どの部分をlocalStorageに保存するか選ぶ
      // ここでは accessToken と refreshToken の2つだけを保存する
      // user情報は保存せず、ページ更新時にサーバーから再取得する設計
      // 関数（setTokens, logoutなど）は保存しない（保存できないし、する必要もない）
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
