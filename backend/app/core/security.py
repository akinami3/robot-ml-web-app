# =============================================================================
# Step 8: セキュリティモジュール — JWT + bcrypt
# =============================================================================
#
# 【このファイルの学習ポイント】
# 1. パスワードハッシュ（bcrypt）
# 2. JWT（JSON Web Token）の生成と検証
# 3. RS256 と HS256 の違い
#
# =============================================================================
#
# 【JWT とは？】
# JSON Web Token の略。認証情報をトークン（文字列）として表現する仕組み。
#
# 構造: Header.Payload.Signature の3部分を "." で連結
#
# eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMSJ9.HMAC_SIGNATURE
# ├── Header ─────────┤├── Payload ────────┤├── Signature ──┤
#
# Header:    アルゴリズム情報 {"alg": "HS256", "typ": "JWT"}
# Payload:   ユーザー情報    {"sub": "user-id", "role": "admin", "exp": 1234}
# Signature: 改竄防止の署名
#
# 【HS256 と RS256 の違い】
# HS256 (HMAC + SHA256):
#   - 共通鍵方式: 署名と検証に同じ秘密鍵を使う
#   - シンプル、高速
#   - 秘密鍵を知っていれば誰でもトークンを作れる
#   → Step 8 ではこちらを使用（シンプルさ優先）
#
# RS256 (RSA + SHA256):
#   - 公開鍵方式: 秘密鍵で署名、公開鍵で検証
#   - 他のサービスが公開鍵だけで検証可能（秘密鍵を共有不要）
#   - マイクロサービスに適している
#   → Step 13（本番構成）で RS256 に移行
#
# 【bcrypt とは？】
# パスワードのハッシュアルゴリズム。
# MD5 や SHA256 と違い、意図的に「遅い」設計。
# ブルートフォース攻撃（総当たり）を困難にする。
#
# bcrypt の特徴:
#   1. ソルト（ランダムな文字列）を自動で付加
#      → 同じパスワードでも毎回異なるハッシュが生成される
#      → レインボーテーブル攻撃を防止
#   2. コストファクター（ストレッチング回数）を設定可能
#      → ハードウェアの進化に合わせて計算コストを上げられる
#   3. 60文字固定の出力: $2b$12$SALT(22chars)HASH(31chars)
#
# =============================================================================

from datetime import datetime, timedelta, timezone
from uuid import UUID

from passlib.context import CryptContext
from jose import JWTError, jwt

from app.config import settings


# =============================================================================
# パスワードハッシュ — passlib + bcrypt
# =============================================================================
#
# 【CryptContext とは？】
# passlib ライブラリのハッシュ管理クラス。
# 複数のハッシュアルゴリズムを扱える。
#
# schemes=["bcrypt"]: bcrypt アルゴリズムを使用
# deprecated="auto":  古いアルゴリズムを自動で非推奨にする
#   → 将来 argon2 に移行したい場合、schemes=["argon2", "bcrypt"] にして
#     bcrypt のハッシュを持つユーザーは次回ログイン時に自動で argon2 に更新される。
#
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    パスワードをハッシュ化する

    【処理の流れ】
    1. ランダムなソルト（22文字）を生成
    2. パスワード + ソルトを bcrypt でハッシュ化
    3. "$2b$12$SALT...HASH..." 形式の文字列を返す

    例:
      hash_password("mypassword")
      → "$2b$12$LJ3m4/.../..." （60文字の文字列）

    毎回異なる結果になる（ソルトがランダムだから）。
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワードを検証する

    【処理の流れ】
    1. hashed_password からソルトとコストファクターを抽出
    2. plain_password を同じソルト・コストでハッシュ化
    3. 結果を比較（一致すれば True）

    タイミング攻撃対策:
      passlib は内部で定時間比較（constant-time comparison）を行う。
      → 文字列の一致/不一致に関わらず処理時間が同じ。
      → 処理時間の差からパスワードを推測する攻撃を防ぐ。
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT トークン — python-jose
# =============================================================================
#
# 【トークンの種類】
# Access Token:  API アクセスに使用（短い有効期限: 30分）
# Refresh Token: Access Token を再発行するために使用（長い有効期限: 7日）
#
# なぜ2つある？
#   Access Token が流出しても、30分で無効になる。
#   Refresh Token があれば、ユーザーは再ログインなしで新しい Access Token を取得。
#   Refresh Token は Access Token より長生きだが、
#   不正利用が疑われたら無効化できる。
#

def create_access_token(
    user_id: UUID,
    username: str,
    role: str,
) -> str:
    """
    アクセストークンを生成する

    【Payload（ペイロード）の内容】
    sub:  Subject（主体）= ユーザー ID
    name: ユーザー名（表示用）
    role: ロール（権限判定用）
    exp:  Expiration（有効期限）= 現在時刻 + 30分
    iat:  Issued At（発行時刻）
    type: トークンの種類（access / refresh）

    【jwt.encode() の引数】
    claims: JWT の Payload（辞書）
    key:    署名に使う秘密鍵
    algorithm: 署名アルゴリズム（HS256）
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    claims = {
        "sub": str(user_id),
        "name": username,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: UUID) -> str:
    """
    リフレッシュトークンを生成する

    Access Token より長い有効期限（7日間）。
    Payload は最小限（user_id と type のみ）。
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)

    claims = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    """
    JWT トークンをデコードして Payload を返す

    【検証内容】
    1. 署名の検証: 秘密鍵で署名を再計算し、一致するか確認
    2. 有効期限の検証: exp が現在時刻を過ぎていないか確認
    3. 不正な場合は JWTError 例外が発生

    【JWTError が発生するケース】
    - トークンが改竄されている（署名が一致しない）
    - トークンの有効期限が切れている
    - トークンの形式が不正
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError as e:
        raise ValueError(f"無効なトークンです: {e}") from e
