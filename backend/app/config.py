# =============================================================================
# Step 12: アプリケーション設定（RAG対応版）
# =============================================================================
#
# 【Step 8 からの変更点（Step 12）】
# RAG（Retrieval-Augmented Generation）関連の設定を追加:
#   - OLLAMA_URL: Ollama LLM サーバーのURL
#   - LLM_MODEL: 使用する言語モデル名
#   - EMBEDDING_MODEL: テキスト埋め込みモデル名
#   - RAG_CHUNK_SIZE: ドキュメント分割サイズ
#   - RAG_CHUNK_OVERLAP: チャンク間のオーバーラップ
#
# 【RAG とは？（初心者向け）】
# RAG = Retrieval-Augmented Generation（検索拡張生成）
# LLM（大規模言語モデル）が回答を生成する前に、関連ドキュメントを検索して
# そのコンテキストをプロンプトに含める手法。
# これにより、LLM は自分の学習データにない情報も回答できるようになる。
#
# 【Ollama とは？】
# ローカルで LLM を動かせるオープンソースツール。
# llama3, mistral, nomic-embed-text など多数のモデルをサポート。
# Docker コンテナとして簡単にデプロイ可能。
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

        # --- RAG / LLM 設定（Step 12 追加） ---
        #
        # 【Ollama の URL】
        # Docker Compose 環境では "http://ollama:11434" でアクセス
        # ローカル開発では "http://localhost:11434"
        #
        self.ollama_url: str = os.environ.get(
            "OLLAMA_URL", "http://ollama:11434"
        )

        # 【使用する言語モデル】
        # llama3: Meta の Llama 3 — 高品質な汎用モデル
        # その他: mistral, gemma, phi3 など
        self.llm_model: str = os.environ.get("LLM_MODEL", "llama3")

        # 【埋め込み（Embedding）モデル】
        # nomic-embed-text: テキストを768次元ベクトルに変換するモデル
        # 💡 埋め込みとは: テキストを数値ベクトルに変換する処理
        #    「犬」→ [0.12, -0.45, 0.78, ...] のようなベクトルに変換
        #    意味が近い単語ほどベクトルが近くなる
        self.embedding_model: str = os.environ.get(
            "EMBEDDING_MODEL", "nomic-embed-text"
        )

        # 【チャンク分割の設定】
        # ドキュメントを小さな断片（チャンク）に分割する際の設定:
        # - chunk_size: 1チャンクの最大文字数（大きいと文脈が広い、小さいと精度が高い）
        # - chunk_overlap: チャンク間の重複文字数（重複があると文脈の切れ目を防げる）
        #
        # 例: chunk_size=500, overlap=50 の場合:
        #   チャンク1: 文字 0〜500
        #   チャンク2: 文字 450〜950  ← 50文字分が重複
        #   チャンク3: 文字 900〜1400
        self.rag_chunk_size: int = int(
            os.environ.get("RAG_CHUNK_SIZE", "500")
        )
        self.rag_chunk_overlap: int = int(
            os.environ.get("RAG_CHUNK_OVERLAP", "50")
        )


# シングルトンインスタンス
settings = Settings()


def get_settings() -> Settings:
    """
    設定シングルトンを返す関数

    【なぜ関数でラップするのか？】
    FastAPI の Depends() で使うため。
    Depends(get_settings) と書くと、エンドポイントの引数に自動注入される。
    テスト時にはこの関数をオーバーライドしてモック設定を注入できる。
    """
    return settings
