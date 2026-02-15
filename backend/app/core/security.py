"""Security utilities - JWT tokens, password hashing."""

# =============================================================================
# セキュリティユーティリティ - JWTトークンとパスワードハッシュ化
# =============================================================================
#
# 【JWTとは？】
#   JWT（JSON Web Token）は、ユーザー認証に使われる「デジタルパスポート」のようなものです。
#   ユーザーがログインすると、サーバーがJWTトークン（暗号化された文字列）を発行します。
#   以降のリクエストでは、このトークンを提示することで「自分が誰か」を証明できます。
#   トークンには有効期限があり、期限切れになると再ログインが必要です。
#
# 【パスワードハッシュ化とは？】
#   パスワードをそのままデータベースに保存するのは非常に危険です。
#   もしデータベースが漏洩したら、全ユーザーのパスワードが丸見えになります。
#   「ハッシュ化」とは、パスワードを元に戻せない形に変換することです。
#   例: "mypassword" → "$2b$12$LJ3..." （元のパスワードに戻すことは不可能）
#   ログイン時は、入力されたパスワードを同じ方法でハッシュ化し、
#   保存済みのハッシュと比較することで正しいかどうかを判定します。
#
# 【bcryptとは？】
#   bcryptは、パスワードハッシュ化のための業界標準アルゴリズムです。
#   特徴:
#   - 「ソルト」（ランダムな文字列）を自動的に追加するため、
#     同じパスワードでも毎回異なるハッシュ値が生成されます。
#   - 計算コストを調整でき、コンピュータの性能向上に合わせて
#     ハッシュ化を遅くすることで、ブルートフォース攻撃に対抗できます。
#
# 【RS256 vs HS256（署名アルゴリズム）】
#   HS256（HMAC-SHA256）:
#     - 共通鍵方式: 1つの秘密鍵で署名と検証の両方を行う
#     - シンプルで高速だが、鍵を共有する必要がある
#     - 小規模なアプリケーション向き
#   RS256（RSA-SHA256）:
#     - 公開鍵方式: 秘密鍵で署名し、公開鍵で検証する
#     - 秘密鍵を持つサーバーだけがトークンを発行でき、
#       公開鍵を持つ誰でもトークンを検証できる
#     - マイクロサービスなど、複数サービス間での認証に適している
#   このアプリでは、RS256の鍵があればRS256を、なければHS256を使います。
#
# 【アクセストークン vs リフレッシュトークン】
#   アクセストークン:
#     - APIリクエストの認証に使う短命なトークン（通常15分程度）
#     - 有効期限が短いため、漏洩しても被害を最小限に抑えられる
#   リフレッシュトークン:
#     - アクセストークンを再発行するための長命なトークン（通常7日程度）
#     - アクセストークンが期限切れになったとき、再ログインせずに
#       新しいアクセストークンを取得するために使う
#   この2つを組み合わせることで、セキュリティと利便性を両立しています。
# =============================================================================

from datetime import UTC, datetime, timedelta
# timedelta（タイムデルタ）: 時間の「差分」を表すオブジェクト
# 例: timedelta(minutes=15) → 15分間
#      timedelta(days=7)     → 7日間
# トークンの有効期限を計算するために使います。
# 「現在時刻 + timedelta(minutes=15)」で「15分後」を表現できます。

from typing import Any

from jose import JWTError, jwt
# jose: JWTトークンのエンコード（作成）・デコード（解読）を行うライブラリ
# JWTError: トークンが無効・期限切れなどの場合に発生するエラー

from passlib.context import CryptContext
# passlib: パスワードのハッシュ化と検証を簡単に行えるライブラリ
# CryptContext: 使うハッシュアルゴリズムの設定を管理するクラス

from app.config import get_settings

# --- パスワードハッシュ化の設定 ---
# schemes=["bcrypt"]: ハッシュアルゴリズムとしてbcryptを使用
# deprecated="auto": 古いアルゴリズムでハッシュされたパスワードを自動的に検出
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """パスワードをハッシュ化する。
    
    新規ユーザー登録時に呼ばれる関数です。
    平文パスワード → bcryptハッシュ値 に変換します。
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """入力されたパスワードが正しいか検証する。
    
    ログイン時に呼ばれる関数です。
    ユーザーが入力したパスワード（plain_password）をハッシュ化し、
    データベースに保存されているハッシュ値（hashed_password）と比較します。
    一致すればTrue、不一致ならFalseを返します。
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_tokens(
    *,
    user_id: str,
    role: str,
    private_key: str | None = None,
    access_expire_minutes: int = 15,
    refresh_expire_days: int = 7,
) -> dict[str, str]:
    """Create both access and refresh tokens."""
    # アクセストークンとリフレッシュトークンの両方を一度に作成する関数

    settings = get_settings()

    # 秘密鍵が渡されていればそれを使い、なければ設定の共通鍵を使う
    key = private_key if private_key else settings.secret_key

    # 秘密鍵（RS256用）があればRS256、なければHS256アルゴリズムを使用
    algorithm = settings.jwt_algorithm if private_key else "HS256"

    # 現在のUTC時刻を取得（全世界共通の基準時刻）
    now = datetime.now(UTC)

    # --- トークンのペイロード（中身）構造 ---
    # "sub" (subject): トークンの対象者（ユーザーID）
    # "role": ユーザーの役割（admin, userなど）→ 権限管理に使用
    # "exp" (expiration): トークンの有効期限
    # "type": トークンの種類（access または refresh）
    access_payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(minutes=access_expire_minutes),
        "type": "access",
    }
    refresh_payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(days=refresh_expire_days),
        "type": "refresh",
    }

    # jwt.encode(): ペイロードを秘密鍵で署名し、JWTトークン文字列を生成
    return {
        "access_token": jwt.encode(access_payload, key, algorithm=algorithm),
        "refresh_token": jwt.encode(refresh_payload, key, algorithm=algorithm),
    }


def create_access_token(data: dict[str, Any]) -> str:
    """アクセストークンを単独で作成する関数。
    
    dataには通常 {"sub": user_id, "role": role} が含まれます。
    有効期限（exp）とトークン種別（type）は自動的に追加されます。
    """
    settings = get_settings()
    to_encode = data.copy()  # 元のデータを変更しないようにコピー
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})

    # RS256用の秘密鍵があるかチェック
    private_key = settings.jwt_private_key
    if private_key is None:
        # 秘密鍵がなければ、共通鍵でHS256署名
        return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

    # 秘密鍵があれば、RS256（公開鍵暗号方式）で署名
    return jwt.encode(to_encode, private_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    """リフレッシュトークンを単独で作成する関数。
    
    アクセストークンと同様の仕組みですが、有効期限が長い（デフォルト7日）です。
    アクセストークンが期限切れになったとき、このトークンを使って
    新しいアクセストークンを取得します。
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})

    private_key = settings.jwt_private_key
    if private_key is None:
        return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

    return jwt.encode(to_encode, private_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, public_key: str | None = None) -> dict[str, Any] | None:
    """トークンをデコード（解読）して中身を取り出す関数。
    
    受け取ったJWTトークンの署名を検証し、ペイロード（中身）を返します。
    - 署名が正しく、有効期限内であれば → ペイロード（辞書型）を返す
    - 署名が不正、または期限切れの場合 → Noneを返す
    
    RS256の場合は公開鍵で検証し、HS256の場合は共通鍵で検証します。
    """
    settings = get_settings()
    try:
        # 公開鍵が渡されていればそれを使い、なければ設定から取得
        key = public_key if public_key else settings.jwt_public_key
        if key is None:
            # 公開鍵がなければ、共通鍵（HS256）でデコード
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        else:
            # 公開鍵があれば、RS256でデコード
            payload = jwt.decode(token, key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        # トークンが無効または期限切れの場合はNoneを返す
        return None
