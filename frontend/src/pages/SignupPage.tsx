/**
 * ============================================================================
 * SignupPage.tsx - 新規アカウント登録ページコンポーネント
 * ============================================================================
 *
 * 【ファイルの概要】
 * ユーザーが新しいアカウントを作成するためのページです。
 * ユーザー名、メールアドレス、パスワード（確認含む）を入力して登録します。
 * 登録成功後は自動的にログインしてダッシュボードに遷移します。
 *
 * 【このページの役割】
 * 1. ユーザー名、メール、パスワード、パスワード確認の入力フォームを表示
 * 2. パスワードの一致チェック（フロントエンドバリデーション）
 * 3. 登録APIの呼び出しとエラーハンドリング
 * 4. 登録後の自動ログイン処理
 *
 * 【LoginPageとの違い】
 * - フォームの入力項目が多い（メール、パスワード確認が追加）
 * - パスワード一致チェックのバリデーション（フロントエンド側）あり
 * - 登録後に自動ログインするフロー
 * - エラーハンドリングが複雑（Pydanticバリデーションエラー対応）
 *
 * 【使われているデザインパターン】
 * - フォーム制御パターン（Controlled Component）
 * - フロントエンドバリデーション（パスワード一致、最小文字数チェック）
 * - エラー型の推論（unknown型からの安全なキャスト）
 * - 自動ログインフロー（登録 → ログイン → ユーザー情報取得）
 *
 * 【画面構成】
 * ┌─────────────────────────────┐
 * │     🤖 Robot AI              │
 * │    Create a new account     │
 * │                             │
 * │  Username: [____________]   │
 * │  Email:    [____________]   │
 * │  Password: [____________]   │
 * │  Confirm:  [____________]   │
 * │                             │
 * │     [ Sign up ボタン ]       │
 * │                             │
 * │  Already have an account?   │
 * │  Sign in (リンク)            │
 * └─────────────────────────────┘
 */

// =============================================================================
// インポート部分
// =============================================================================

/**
 * useState - Reactの状態管理フック
 * このページでは5つの状態を管理:
 *   username, email, password, confirmPassword, loading
 * 【ポイント】入力フォームの各欄に対して1つずつstateを用意するのが基本パターンです。
 */
import { useState } from "react";

/**
 * useNavigate - プログラムからの画面遷移（登録成功後にダッシュボードへ飛ぶ）
 * Link - ページ内リンク（「ログインページはこちら」のリンク用）
 */
import { useNavigate, Link } from "react-router-dom";

/**
 * Bot - ロボットアイコン（ヘッダーに表示）
 * lucide-reactは軽量なSVGアイコンライブラリです。
 */
import { Bot } from "lucide-react";

/**
 * UIコンポーネントのインポート
 * 複数行に分けてインポートすることで、見やすくしています。
 * 
 * Button - 送信ボタン
 * Input - テキスト入力欄
 * Label - 入力欄のラベル文字
 * Card系 - カード型レイアウト部品
 *
 * 【マルチラインインポート】
 * インポートが多い場合、このように改行して書くとコードが読みやすくなります。
 */
import {
  Button,
  Input,
  Label,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/primitives";

/**
 * authApi - 認証関連のAPI関数群
 * .register() - 新規ユーザー登録
 * .login() - ログイン（登録後の自動ログインに使用）
 * .me() - 現在のユーザー情報取得
 */
import { authApi } from "@/services/api";

/**
 * useAuthStore - グローバル認証状態管理
 * 登録後の自動ログインで、トークンとユーザー情報を保存するために使用
 */
import { useAuthStore } from "@/stores/authStore";

/**
 * toast - トースト通知（成功・エラーメッセージの表示）
 * このページではバリデーションエラーの通知にも使います。
 */
import toast from "react-hot-toast";

// =============================================================================
// SignupPageコンポーネント
// =============================================================================

/**
 * SignupPage - 新規アカウント登録ページのメインコンポーネント
 *
 * 【LoginPageとの構造的な違い】
 * - 入力フィールドが4つ（username, email, password, confirmPassword）
 * - フロントエンド側のバリデーション（パスワード一致・長さチェック）
 * - エラーハンドリングが詳細（サーバーからのエラーメッセージを解析）
 */
export function SignupPage() {
  // ---------------------------------------------------------------------------
  // 状態（State）の定義
  // ---------------------------------------------------------------------------

  /**
   * 各入力フィールドに対応するstate
   *
   * 【LoginPageより多い理由】
   * サインアップにはメールやパスワード確認が必要なため、
   * 管理する状態が多くなります。
   */
  const [username, setUsername] = useState("");           // ユーザー名
  const [email, setEmail] = useState("");                 // メールアドレス
  const [password, setPassword] = useState("");           // パスワード
  const [confirmPassword, setConfirmPassword] = useState(""); // パスワード確認用
  const [loading, setLoading] = useState(false);          // 送信処理中フラグ

  // ---------------------------------------------------------------------------
  // フック（Hooks）の初期化
  // ---------------------------------------------------------------------------

  /** 画面遷移用（登録成功後にダッシュボードへ移動） */
  const navigate = useNavigate();

  /**
   * 認証ストアから関数を取得
   * setTokens - トークン保存（登録後の自動ログインで使用）
   * setUser - ユーザー情報保存
   */
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  // ---------------------------------------------------------------------------
  // イベントハンドラー
  // ---------------------------------------------------------------------------

  /**
   * handleSignup - サインアップフォーム送信時の処理
   *
   * 【処理の流れ】
   * 1. ページリロード防止
   * 2. パスワード一致チェック（フロントエンドバリデーション）
   * 3. パスワード長チェック
   * 4. ローディング開始
   * 5. 登録API呼び出し
   * 6. 自動ログイン（登録直後に再度ログインAPIを呼ぶ）
   * 7. ユーザー情報取得・保存
   * 8. 成功通知 → ダッシュボードへ遷移
   *
   * 【なぜ登録後に自動ログインする？】
   * ユーザーが「登録」→「ログイン画面に戻る」→「ログイン」と
   * 2回操作するのは面倒です。自動ログインでUX（使い心地）を向上させます。
   */
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    /**
     * フロントエンドバリデーション①: パスワード一致チェック
     * 2つのパスワード入力が一致しない場合、APIに送信せずにエラーを表示します。
     *
     * 【なぜフロントエンドでチェック？】
     * サーバーに送信する前に明らかなエラーを検出することで、
     * 不要なネットワーク通信を避け、素早くフィードバックを返せます。
     */
    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return; // ここで処理を中断（以降のコードは実行されない）
    }

    /**
     * フロントエンドバリデーション②: パスワード長チェック
     * 最低8文字以上を要求（セキュリティのため）
     */
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      /**
       * 1. 新規ユーザー登録APIを呼び出し
       * { username, email, password } はオブジェクトリテラルの省略記法（shorthand）:
       *   { username: username, email: email, password: password } と同じ意味です。
       */
      await authApi.register({ username, email, password });

      /**
       * 2. 登録成功後に自動ログイン
       * 登録APIはトークンを返さないことが多いため、
       * 別途ログインAPIを呼んでトークンを取得します。
       *
       * 【{ data: tokens }は「リネーム分割代入」】
       * dataプロパティを取り出して、tokens という名前に変更しています。
       *   const { data } = ... → data で使える
       *   const { data: tokens } = ... → tokens で使える（dataでは使えない）
       */
      const { data: tokens } = await authApi.login(username, password);
      setTokens(tokens);

      /** 3. ユーザー情報を取得して保存 */
      const me = await authApi.me();
      setUser(me.data);

      /** 4. 成功通知を表示し、ダッシュボードに遷移 */
      toast.success("Account created successfully");
      navigate("/");
    } catch (err: unknown) {
      /**
       * エラーハンドリング - サーバーからのエラーを詳細に解析
       *
       * 【unknown型とは？】
       * TypeScriptのcatchブロックでは、エラーの型は「unknown」です。
       * any型より安全で、使う前に型を確認する必要があります。
       *
       * 【なぜこんなに複雑？】
       * バックエンド（FastAPI/Pydantic）が返すエラー形式は複数パターンがあります:
       *  パターン1: { detail: "Username already exists" }  ← 文字列エラー
       *  パターン2: { detail: [{ msg: "..." }, ...] }      ← バリデーションエラー配列
       *  パターン3: エラーレスポンスなし                     ← ネットワークエラーなど
       *
       * 各パターンに対応するため、条件分岐で丁寧にエラーメッセージを取り出します。
       */

      /**
       * err を Axiosのエラー型としてキャスト（型変換）
       * ?.（オプショナルチェーン）を使って、各プロパティが存在するか安全に確認
       *
       * 【asキャストとは？】
       * TypeScriptに「この値はこの型として扱っていいよ」と伝える方法です。
       * 型安全性を少し緩めるため、慎重に使う必要があります。
       */
      const detail = (
        err as { response?: { data?: { detail?: unknown } } }
      )?.response?.data?.detail;

      if (typeof detail === "string") {
        /** パターン1: 文字列エラー（例: "Username already exists"） */
        toast.error(detail);
      } else if (Array.isArray(detail)) {
        /**
         * パターン2: Pydanticのバリデーションエラー（配列形式）
         * 最初のエラーメッセージだけを表示して、ユーザーに何が問題か伝えます
         * 
         * 【Pydanticとは？】
         * バックエンド（Python/FastAPI）のデータバリデーションライブラリ。
         * 入力データの型や値が不正な場合、詳細なエラー情報を配列で返します。
         */
        const msg = (detail[0] as { msg?: string })?.msg;
        toast.error(msg ?? "Validation error");
      } else {
        /** パターン3: 上記以外のエラー（汎用メッセージ） */
        toast.error("Registration failed. Please try again.");
      }
    } finally {
      /** 成功・失敗に関わらず、ローディング状態を解除 */
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // JSX（画面の描画部分）
  // ---------------------------------------------------------------------------

  /**
   * 【LoginPageとの構造の共通点】
   * - 画面中央にカードを配置するレイアウト
   * - ロボットアイコンとタイトル
   * - フォーム + 送信ボタン
   * - 代替リンク（既にアカウントがある場合はログインページへ）
   *
   * 【違い】
   * - 入力フィールドが4つに増えている
   * - minLength バリデーション属性の使用
   */
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          {/** ロボットアイコン（LoginPageと同じデザイン） */}
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <Bot className="h-6 w-6 text-primary" />
          </div>
          <CardTitle>Robot AI</CardTitle>
          <p className="text-sm text-muted-foreground">
            Create a new account
          </p>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSignup} className="space-y-4">
            {/** ユーザー名入力欄 */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="johndoe"
                required
                autoFocus
              />
            </div>

            {/**
             * メールアドレス入力欄
             * type="email" を指定すると、ブラウザが自動的に
             * メールアドレス形式のバリデーションを行います（@が含まれているか等）。
             */}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>

            {/**
             * パスワード入力欄
             * minLength={8} - HTMLのバリデーション属性
             *   ブラウザレベルで8文字未満の送信を防止します。
             *   JavaScript側でもチェックしていますが、二重で安全性を高めています。
             */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
              />
            </div>

            {/**
             * パスワード確認入力欄
             * ユーザーがパスワードを正確に入力したか確認するための欄です。
             * この値はhandleSignup内でpasswordと比較されます。
             */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
              />
            </div>

            {/** 送信ボタン（ローディング中は表示テキストが変わる） */}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating account..." : "Sign up"}
            </Button>
          </form>

          {/**
           * ログインページへのリンク
           * 既にアカウントを持っている場合はログインページに戻れるようにします。
           *
           * 【UXの配慮】
           * ユーザーが間違えてサインアップページに来た場合や、
           * 既にアカウントを持っている場合にスムーズに移動できます。
           */}
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-medium text-primary hover:underline"
            >
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
