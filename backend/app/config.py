# =============================================================================
# Step 7: アプリケーション設定 — 環境変数からの読み取り
# =============================================================================
#
# 【なぜ設定ファイルが必要？】
# Step 6 まではハードコーディング（コードに直接値を書く）だった。
# しかし、データベースの接続先は環境（開発/本番）で異なる。
# 環境変数から読み取ることで、コードを変更せずに設定を変えられる。
#
# 【Pydantic Settings とは？】
# Pydantic の BaseSettings を使うと、環境変数を自動で読み取り、
# 型変換・バリデーションをしてくれる。
#
#   環境変数 DATABASE_URL="postgresql+asyncpg://..."
#   → settings.database_url に自動的にセットされる
#
# 【12-Factor App の原則】
# "設定を環境変数に格納する" は、モダンな Web アプリケーションの
# ベストプラクティスの一つ（12-Factor App の「III. Config」）。
# https://12factor.net/ja/config
#
# =============================================================================

import os


# =============================================================================
# Settings クラス
# =============================================================================
#
# 【Pydantic BaseSettings を使わない理由】
# Step 7 では依存を少なくするため、os.environ を直接使う。
# Step 13（本番品質）で pydantic-settings に移行する。
#
class Settings:
    """
    アプリケーション設定

    【各設定値の説明】
    DATABASE_URL:
      PostgreSQL への接続 URL。
      形式: postgresql+asyncpg://ユーザー:パスワード@ホスト:ポート/DB名

      asyncpg は Python の非同期 PostgreSQL ドライバー。
      SQLAlchemy の AsyncSession と組み合わせて使用する。

    DEBUG:
      デバッグモード。True の場合、詳細なエラー情報を返す。
    """

    def __init__(self) -> None:
        # --- データベース URL ---
        # 環境変数 DATABASE_URL があればそれを使い、
        # なければデフォルト値（Docker Compose の設定に合わせた値）を使う。
        self.database_url: str = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://robot:robot@db:5432/robotdb",
        )

        # --- 同期版 URL（Alembic マイグレーション用） ---
        # Alembic は非同期ドライバー (asyncpg) をサポートしないため、
        # 同期版ドライバー (psycopg2) の URL も用意する。
        self.database_url_sync: str = os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql://robot:robot@db:5432/robotdb",
        )

        # デバッグモード
        self.debug: bool = os.environ.get("DEBUG", "false").lower() == "true"

        # サーバー設定
        self.host: str = os.environ.get("HOST", "0.0.0.0")
        self.port: int = int(os.environ.get("PORT", "8000"))


# =============================================================================
# シングルトンインスタンス
# =============================================================================
#
# 【シングルトンパターンとは？】
# アプリケーション全体で1つだけインスタンスが存在することを保証する。
# 設定は全コンポーネントで同じ値を参照すべきため、シングルトンが適切。
#
# Python のモジュールレベル変数は、最初に import された時だけ実行される。
# → 自然にシングルトンになる。
#
settings = Settings()
