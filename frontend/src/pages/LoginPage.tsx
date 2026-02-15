/**
 * ============================================================================
 * LoginPage.tsx - ログインページコンポーネント
 * ============================================================================
 *
 * 【ファイルの概要】
 * ユーザーがアプリケーションにログインするためのページです。
 * ユーザー名とパスワードを入力し、認証APIに送信してログインを行います。
 *
 * 【このページの役割】
 * 1. ユーザー名とパスワードの入力フォームを表示する
 * 2. 入力された情報をサーバーに送信して認証を行う
 * 3. 認証成功時にトークンを保存し、ダッシュボードに遷移する
 * 4. 認証失敗時にエラーメッセージを表示する
 *
 * 【使われているデザインパターン】
 * - フォーム制御パターン（Controlled Component）: useStateでフォームの各入力値を管理
 * - 非同期処理パターン: async/awaitでAPIリクエストを処理
 * - try/catch/finally: エラーハンドリングとローディング状態の管理
 * - 認証フロー: ログイン → トークン保存 → ユーザー情報取得 → 画面遷移
 *
 * 【画面構成】
 * ┌─────────────────────────────┐
 * │     🤖 Robot AI              │
 * │    Sign in to continue      │
 * │                             │
 * │  Username: [____________]   │
 * │  Password: [____________]   │
 * │                             │
 * │     [ Sign in ボタン ]       │
 * │                             │
 * │  Don't have an account?     │
 * │  Sign up (リンク)            │
 * └─────────────────────────────┘
 */

// =============================================================================
// インポート部分
// =============================================================================

/**
 * useState - Reactの「状態管理フック」
 * コンポーネント内でデータ（状態）を保持・更新するために使います。
 * 例: ユーザー名、パスワード、ローディング状態などを管理
 *
 * 【なぜ必要？】
 * Reactでは、普通の変数（let）の値が変わっても画面は自動更新されません。
 * useStateを使うことで、値が変わると自動的に画面が再描画（リレンダリング）されます。
 */
import { useState } from "react";

/**
 * useNavigate - React Routerの「画面遷移フック」
 * プログラムから別のページに移動するために使います。
 * 例: ログイン成功後にダッシュボードページへ自動遷移
 *
 * Link - React Routerの「リンクコンポーネント」
 * HTMLの<a>タグの代わりに使い、ページ全体をリロードせずに画面遷移します。
 * 例: 「アカウント登録はこちら」のリンク
 *
 * 【なぜ<a>タグではなくLinkを使う？】
 * <a>タグはページ全体をリロードしてしまい、アプリの状態が消えます。
 * Linkはページ遷移だけ行い、アプリの状態を保持したまま移動できます（SPA方式）。
 */
import { useNavigate, Link } from "react-router-dom";

/**
 * Bot - lucide-reactライブラリのロボットアイコン
 * 🤖のようなSVGアイコンをReactコンポーネントとして使えます。
 * <Bot /> のように書くだけでアイコンが表示されます。
 */
import { Bot } from "lucide-react";

/**
 * UIコンポーネントのインポート（再利用可能な「部品」）
 *
 * Button - ボタン部品（クリック可能な要素）
 * Input - テキスト入力欄（ユーザーが文字を入力する部品）
 * Label - 入力欄のラベル（「ユーザー名」「パスワード」などの説明文）
 * Card, CardHeader, CardTitle, CardContent - カード型UIレイアウト部品
 *   → カードは情報をまとめて表示するための「枠」です
 *
 * 【@/ パスエイリアス】
 * @/ は src/ フォルダを指すショートカットです。
 * "@/components/ui/primitives" = "src/components/ui/primitives"
 */
import { Button, Input, Label, Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

/**
 * authApi - 認証関連のAPIクライアント
 * サーバーとの通信（ログイン、サインアップ、ユーザー情報取得）を行う関数群です。
 *
 * 【APIとは？】
 * API（Application Programming Interface）は、フロントエンド（画面）と
 * バックエンド（サーバー）が通信するための「窓口」です。
 * authApi.login()を呼ぶと、サーバーにログインリクエストが送信されます。
 */
import { authApi } from "@/services/api";

/**
 * useAuthStore - 認証状態管理ストア（Zustand）
 * アプリケーション全体で共有される認証情報（トークン、ユーザー情報）を管理します。
 *
 * 【ストアとは？】
 * 複数のコンポーネント間でデータを共有するための「グローバルな変数置き場」です。
 * ログインページでトークンを保存すると、他のページでもそのトークンを参照できます。
 *
 * 【Zustandとは？】
 * React用の軽量な状態管理ライブラリ。Reduxよりもシンプルに使えます。
 */
import { useAuthStore } from "@/stores/authStore";

/**
 * toast - react-hot-toastライブラリの通知関数
 * 画面の端に一時的なメッセージ（トースト通知）を表示します。
 * 例: toast.success("成功！") → 緑色の成功メッセージ
 *     toast.error("失敗！") → 赤色のエラーメッセージ
 *
 * 【トースト通知とは？】
 * パンがトースターから飛び出すように、画面の端から現れて数秒後に消える通知です。
 * ユーザーの操作を邪魔せずに結果を伝える、一般的なUIパターンです。
 */
import toast from "react-hot-toast";

// =============================================================================
// LoginPageコンポーネント
// =============================================================================

/**
 * LoginPage - ログインページのメインコンポーネント
 *
 * 【exportについて】
 * export をつけることで、他のファイルからこのコンポーネントをimportできます。
 * ルーター（App.tsx等）からこのページを読み込んで表示するために必要です。
 *
 * 【関数コンポーネントとは？】
 * Reactでは、UIを「関数」として定義します。
 * 関数がJSX（HTMLのような構文）を返すと、それが画面に表示されます。
 */
export function LoginPage() {
  // ---------------------------------------------------------------------------
  // 状態（State）の定義
  // ---------------------------------------------------------------------------

  /**
   * フォームの入力値とローディング状態をuseStateで管理
   *
   * useState("") の "" は「初期値」（最初は空文字列）
   * useState(false) の false は、最初はローディング中ではないことを意味します
   *
   * [username, setUsername] は「分割代入（destructuring）」という書き方で、
   * username が現在の値、setUsername が値を変更する関数です。
   *
   * 【なぜuseStateを使う？】
   * 通常のlet変数では、値を変えても画面が更新されません。
   * useStateを使うと、setUsername("新しい値")を呼ぶたびに画面が自動更新されます。
   */
  const [username, setUsername] = useState("");     // ユーザー名の入力値
  const [password, setPassword] = useState("");     // パスワードの入力値
  const [loading, setLoading] = useState(false);    // ログイン処理中かどうかのフラグ

  // ---------------------------------------------------------------------------
  // フック（Hooks）の初期化
  // ---------------------------------------------------------------------------

  /**
   * useNavigate() - 画面遷移用の関数を取得
   * navigate("/") を呼ぶと、ホーム画面（ダッシュボード）に移動します。
   */
  const navigate = useNavigate();

  /**
   * useAuthStore を使って、ストアから「関数」を取得
   *
   * setTokens - アクセストークンを保存する関数
   *   (s) => s.setTokens は「ストアの中からsetTokens関数だけを取り出す」という意味
   *
   * setUser - ログインしたユーザーの情報を保存する関数
   *
   * 【トークンとは？】
   * サーバーが発行する「認証済みの証明書」のようなもの。
   * APIにアクセスするたびにこのトークンを送信して「ログイン済み」を証明します。
   */
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  // ---------------------------------------------------------------------------
  // イベントハンドラー
  // ---------------------------------------------------------------------------

  /**
   * handleLogin - フォーム送信時に呼ばれる非同期関数
   *
   * 【async/awaitとは？】
   * async: この関数は「非同期処理を含む」ことを宣言
   * await: 非同期処理（API通信など）が完了するまで「待つ」
   * サーバーとの通信は時間がかかるため、非同期処理として実行します。
   *
   * 【React.FormEvent型とは？】
   * フォームのsubmitイベントの型定義です。TypeScriptで型を指定することで、
   * イベントオブジェクトのプロパティやメソッドの入力補完が効きます。
   *
   * 【処理の流れ】
   * 1. e.preventDefault() でページリロードを防止
   * 2. ローディング状態をON
   * 3. APIにログインリクエストを送信
   * 4. 成功: トークン保存 → ユーザー情報取得 → 画面遷移
   * 5. 失敗: エラーメッセージ表示
   * 6. 最後に必ずローディング状態をOFF
   */
  const handleLogin = async (e: React.FormEvent) => {
    /**
     * e.preventDefault() - ブラウザのデフォルト動作を無効化
     * 通常、フォーム送信するとページがリロードされますが、
     * Reactアプリでは自分でAPI通信を行うため、リロードを防止します。
     */
    e.preventDefault();

    /** ローディング状態をONにして、ボタンを無効化（二重送信防止） */
    setLoading(true);

    try {
      /**
       * 1. ログインAPI呼び出し
       * サーバーにユーザー名とパスワードを送信し、トークンを取得します。
       * { data } は「分割代入」で、レスポンスの中からdata部分だけを取り出します。
       */
      const { data } = await authApi.login(username, password);

      /**
       * 2. トークンをストアに保存
       * 取得したトークンをZustandストアに保存します。
       * これにより、他のAPI呼び出しでも認証トークンが自動的に使われます。
       */
      setTokens(data);

      /**
       * 3. ユーザー情報を取得して保存
       * authApi.me() は「現在ログインしているユーザーの情報」を取得するAPIです。
       * 取得した情報（ユーザー名、メール、権限など）をストアに保存します。
       */
      const me = await authApi.me();
      setUser(me.data);

      /**
       * 4. 成功通知を表示して、ダッシュボードに遷移
       * toast.success() で緑色の成功メッセージを表示
       * navigate("/") でホーム画面（ダッシュボード）に移動
       */
      toast.success("Logged in");
      navigate("/");
    } catch {
      /**
       * エラーが発生した場合（認証失敗、ネットワークエラーなど）
       * toast.error() で赤色のエラーメッセージを表示
       *
       * 【catchブロック】
       * try内のどこかでエラーが発生すると、処理がここにジャンプします。
       */
      toast.error("Invalid credentials");
    } finally {
      /**
       * finallyブロック - 成功・失敗に関わらず必ず実行される
       * ローディング状態を必ずOFFに戻して、ボタンを再び有効にします。
       *
       * 【なぜfinallyが必要？】
       * tryでもcatchでもsetLoading(false)を書くと重複になります。
       * finallyなら1箇所で確実に実行されます。
       */
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // JSX（画面の描画部分）
  // ---------------------------------------------------------------------------

  /**
   * 【returnされるJSXの構造】
   *
   * JSX（JavaScript XML）は、HTMLに似た構文でUIを記述する方法です。
   * ReactではこのJSXを使って画面の見た目を定義します。
   *
   * 【Tailwind CSSクラスの説明】
   * flex - Flexboxレイアウトを適用（要素を柔軟に配置）
   * min-h-screen - 最小の高さを画面全体に設定（100vh）
   * items-center - Flexbox内の要素を縦方向の中央に配置
   * justify-center - Flexbox内の要素を横方向の中央に配置
   * bg-background - 背景色にテーマの背景色を使用
   * p-4 - 内側の余白（padding）を16px
   *
   * つまり、画面の中央にカードを配置するレイアウトです。
   */
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      {/**
       * Cardコンポーネント - ログインフォームを囲むカード
       * w-full - 幅100%（親要素いっぱいに広がる）
       * max-w-sm - 最大幅384px（小さめのカードサイズ）
       */}
      <Card className="w-full max-w-sm">
        {/**
         * CardHeader - カードのヘッダー部分（タイトルやアイコン）
         * text-center - テキストを中央揃え
         */}
        <CardHeader className="text-center">
          {/**
           * ロボットアイコンの丸い背景
           * mx-auto - 左右のマージンを自動にして中央揃え
           * mb-2 - 下のマージンを8px
           * flex h-12 w-12 - 48x48pxのFlexboxコンテナ
           * items-center justify-center - アイコンを中央に配置
           * rounded-full - 完全な円形にする
           * bg-primary/10 - プライマリカラーの10%透明度の背景色
           */}
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            {/** Botアイコン: h-6 w-6は24x24px、text-primaryはテーマ主色 */}
            <Bot className="h-6 w-6 text-primary" />
          </div>
          {/** カードのタイトル */}
          <CardTitle>Robot AI</CardTitle>
          {/**
           * サブタイトル
           * text-sm - 小さめのフォントサイズ
           * text-muted-foreground - 薄い色のテキスト（控えめな表示）
           */}
          <p className="text-sm text-muted-foreground">Sign in to continue</p>
        </CardHeader>

        <CardContent>
          {/**
           * フォーム要素
           * onSubmit={handleLogin} - フォーム送信時にhandleLogin関数を呼び出す
           * space-y-4 - 子要素間に16pxの縦方向の間隔
           *
           * 【フォームのonSubmitイベント】
           * ユーザーがEnterキーを押すか、送信ボタンをクリックすると発火します。
           */}
          <form onSubmit={handleLogin} className="space-y-4">
            {/**
             * ユーザー名入力欄
             * space-y-2 - LabelとInputの間に8pxの間隔
             * htmlFor="username" - ラベルとInputの紐付け
             *   ラベルをクリックすると対応するInputにフォーカスが当たります
             */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              {/**
               * Input（テキスト入力欄）のプロパティ:
               * id="username" - 要素のID（LabelのhtmlForと紐付け）
               * value={username} - 表示する値（useStateの値と連動）
               * onChange - 入力変更時に呼ばれる関数
               *   (e) => setUsername(e.target.value) で入力値をuseStateに反映
               * placeholder - 入力欄が空の時に薄く表示されるヒントテキスト
               * required - 必須入力（空欄では送信不可）
               * autoFocus - ページ表示時にこの入力欄に自動フォーカス
               *
               * 【制御されたコンポーネント（Controlled Component）】
               * value とonChange を組み合わせることで、
               * Reactが入力欄の値を完全に管理する「制御されたコンポーネント」になります。
               */}
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                autoFocus
              />
            </div>

            {/** パスワード入力欄 */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              {/**
               * type="password" - 入力した文字が●●●のように隠される
               * セキュリティのため、パスワードは画面上で見えないようにします。
               */}
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            {/**
             * 送信ボタン
             * type="submit" - クリックするとフォームのonSubmitイベントが発火
             * className="w-full" - ボタン幅を100%に
             * disabled={loading} - ローディング中はボタン無効化（二重送信防止）
             *
             * {loading ? "Signing in..." : "Sign in"}
             * → 三項演算子: loadingがtrueなら"Signing in..."、falseなら"Sign in"を表示
             */}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          {/**
           * サインアップページへのリンク
           * mt-4 - 上のマージン16px
           *
           * Don&apos;t は「Don't」のHTMLエスケープ表記です。
           * {" "} はテキスト間にスペースを入れるReactの書き方です。
           *
           * <Link to="/signup"> - サインアップページへ遷移
           * font-medium - フォントの太さを中程度に
           * hover:underline - マウスホバー時に下線を表示
           */}
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link
              to="/signup"
              className="font-medium text-primary hover:underline"
            >
              Sign up
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
