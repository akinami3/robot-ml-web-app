# Step 8: 認証・認可 🔐

> **ブランチ**: `step/08-authentication`
> **前のステップ**: `step/07-database`
> **次のステップ**: `step/09-react-migration`

---

## このステップで学ぶこと

1. **JWT（JSON Web Token）** — トークンの構造（Header.Payload.Signature）、HS256 署名
2. **パスワードハッシュ** — bcrypt によるソルト付きハッシュ化
3. **RBAC** — ロールベースアクセス制御（Admin / Operator / Viewer）
4. **トークンリフレッシュ** — Access Token（短寿命）+ Refresh Token（長寿命）
5. **FastAPI DI チェーン** — `Depends()` を連鎖させた認証・認可の実装

---

## 概要

ユーザー認証（ログイン・サインアップ）と、ロール（権限）に基づくアクセス制御を
バックエンドとフロントエンドの両方に追加するステップ。
JWT トークンによるステートレス認証と、bcrypt によるパスワードの安全な保存を実装する。
初期管理者ユーザー（admin / admin123）が自動作成される。

---

## 学習ポイント

### JWT 認証フロー

```
1. ログイン
   ブラウザ ── POST /auth/login ──► バックエンド
               { email, password }
                                    パスワード検証（bcrypt）
   ブラウザ ◄── 200 ──────────────── { access_token, refresh_token }

2. API リクエスト
   ブラウザ ── GET /api/v1/robots ─► バックエンド
               Authorization: Bearer <access_token>
                                    JWT 検証 → ユーザー取得
   ブラウザ ◄── 200 ──────────────── [robots...]

3. トークン更新
   ブラウザ ── POST /auth/refresh ─► バックエンド
               { refresh_token }
   ブラウザ ◄── 200 ──────────────── { access_token（新しい） }
```

### RBAC（ロールベースアクセス制御）

| ロール | ロボット一覧 | ロボット登録 | ロボット削除 | ユーザー管理 |
|--------|:----------:|:----------:|:----------:|:----------:|
| Viewer | ✅ | ❌ | ❌ | ❌ |
| Operator | ✅ | ✅ | ❌ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ |

### セキュリティの仕組み
- **bcrypt**: パスワードをハッシュ化して保存（平文を保存しない）
- **JWT 署名**: トークンの改ざんを検出（SECRET_KEY で署名）
- **短寿命 Access Token**: 30 分で失効（漏洩リスク低減）
- **サイレントリフレッシュ**: 401 応答時に自動で Refresh Token を使って更新

---

## ファイル構成

```
backend/
  app/
    core/
      security.py                          ← 🆕 JWT 生成・検証、パスワードハッシュ
    domain/
      entities/
        user.py                            ← UserRole 列挙型追加
      repositories/
        user_repo.py                       ← 🆕 UserRepository インターフェース
    infrastructure/
      database/
        models.py                          ← UserModel 追加
        repositories/
          user_repo.py                     ← 🆕 SQLAlchemy 実装
    api/v1/
      auth.py                              ← 🆕 ログイン・登録・リフレッシュ
      users.py                             ← 🆕 ユーザー管理（Admin のみ）
      dependencies.py                      ← 認証 DI チェーン追加
      robots.py                            ← 認証保護追加
  alembic/versions/                        ← 🆕 users テーブルマイグレーション

keys/                                      ← 🆕 シークレットキー管理

frontend/
  js/
    api.js                                 ← Authorization ヘッダー自動付与
    app.js                                 ← ルートガード + ログアウト
    pages/
      login.js                             ← 🆕 ログインページ
      signup.js                            ← 🆕 サインアップページ

docker-compose.yml                         ← SECRET_KEY 環境変数追加
```

---

## 起動方法

```bash
docker compose up --build
```

### 初期管理者でログイン

| フィールド | 値 |
|-----------|-----|
| Email | admin@example.com |
| Password | admin123 |

### 試してみる

1. http://localhost:3000 → ログインページにリダイレクト
2. 初期管理者でログイン → ダッシュボードが表示される
3. 「サインアップ」で新しいユーザーを作成（Viewer ロール）
4. Viewer でログイン → ロボット登録ボタンが非表示になることを確認
5. DevTools → Application → Local Storage でトークンを確認

---

## Step 7 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| 認証 | JWT トークン（Access + Refresh）方式 |
| パスワード | bcrypt ハッシュ化 |
| 認可 | RBAC（Admin / Operator / Viewer） |
| API 保護 | 全エンドポイントに認証必須化 |
| フロント | ログイン/サインアップページ、ルートガード |
| DI | `require_role()` 高階関数による権限チェック |
| ファイル数 | 22 files changed, +2,198 / -737 |

---

## 🏋️ チャレンジ課題

1. **トークンの中身を見よう**: https://jwt.io/ で Access Token をデコードして構造を確認
2. **権限を試そう**: Viewer で POST /api/v1/robots を呼ぶと 403 が返ることを確認
3. **トークンの有効期限**: Access Token の期限を 1 分に変更して、自動リフレッシュを観察
4. **パスワード変更 API**: PUT /auth/password エンドポイントを追加してみよう

---

## 次のステップへ

Step 9 では Vanilla JS フロントエンドを **React + TypeScript** に全面移行します:

```bash
git checkout step/09-react-migration
```
