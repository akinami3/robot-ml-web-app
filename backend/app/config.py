# =============================================================================
# Step 8: アプリケーション設定（認証対応版）
# =============================================================================
#
# 【Step 7 からの変更点】
# JWT 関連の設定を追加:
#   - SECRET_KEY: JWT 署名に使う秘密鍵
#   - ALGORITHM: 署名アルゴリズム（HS256）
#   - ACCESS_TOKEN_EXPIRE_MINUTES: アクセストークン有効期限
#   - REFRESH_TOKEN_EXPIRE_DAYS: リフレッシュトークン有効期限
#
# 【SECRET_KEY の重要性】
# この鍵が漏洩すると、誰でも有効な JWT を作成できてしまう。
# 本番環境では必ず環境変数で設定し、ソースコードに含めないこと！
# ここでは開発用のデフォルト値を設定している。
#
# =============================================================================

import os


class Settings:
    """アプリケーション設定"""

    def __init__(self) -> None:
        # --- データベース ---
        self.database_url: str = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://robot:robot@db:5432/robotdb",
        )
        self.database_url_sync: str = os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql://robot:robot@db:5432/robotdb",
        )

        # --- JWT 認証（Step 8 追加） ---
        #
        # SECRET_KEY: JWT の署名に使う秘密鍵
        # 開発環境では固定値でOK。本番では必ず環境変数で設定。
        # 生成方法: python3 -c "import secrets; print(secrets.token_hex(32))"
        #
        self.secret_key: str = os.environ.get(
            "SECRET_KEY",
            "dev-secret-key-change-in-production-please",
        )
        self.algorithm: str = "HS256"
        self.access_token_expire_minutes: int = int(
            os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.refresh_token_expire_days: int = int(
            os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # --- サーバー設定 ---
        self.debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
        self.host: str = os.environ.get("HOST", "0.0.0.0")
        self.port: int = int(os.environ.get("PORT", "8000"))


# シングルトンインスタンス
settings = Settings()
