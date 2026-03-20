# ============================================================
# ベクトル埋め込みサービス（Embedding Service）
# ============================================================
# テキストをベクトル（数値の配列）に変換するサービスです。
# Ollama の nomic-embed-text モデルを使用します。
#
# 【ベクトル埋め込み（Embedding）とは？】
# テキストの「意味」を768個の数値の配列に変換する技術。
# 
# 例: "ロボットが走る" → [0.12, -0.45, 0.78, ..., 0.33]（768個の数値）
#
# 意味が似た文章は、ベクトル空間で「近い」位置に配置されます。
# これにより、キーワード一致ではなく「意味」で検索が可能になります。
#
# 【nomic-embed-text モデル】
# 高品質で軽量なテキスト埋め込みモデル。
# 768次元のベクトルを出力し、Ollama でローカル実行可能。
#
# 【httpx とは？】
# Python の HTTP クライアントライブラリ。
# requests ライブラリの非同期版として使用。
# Ollama の REST API に HTTP リクエストを送信します。
# ============================================================
"""Embedding service using Ollama's nomic-embed-text model."""

from __future__ import annotations

import structlog
from typing import Any

# httpx: 非同期対応の HTTP クライアント
import httpx

logger = structlog.get_logger()


class EmbeddingService:
    """
    Ollama を使ってテキストのベクトル埋め込みを生成するサービス。

    【使用場所】
    - RAGService の ingest_document: ドキュメントチャンクのベクトル化
    - RAGService の query: 質問文のベクトル化
    """

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "nomic-embed-text",
        timeout: float = 60.0,
    ) -> None:
        """
        コンストラクタ。

        Args:
            base_url: Ollama サーバーの URL
                Docker Compose では "ollama" がサービス名
                11434 は Ollama のデフォルトポート
            model: 使用する埋め込みモデル名
            timeout: HTTP リクエストのタイムアウト（秒）
        """
        self.base_url = base_url.rstrip("/")  # 末尾の / を除去
        self.model = model
        # 非同期 HTTP クライアントを初期化
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        """HTTP クライアントを閉じてリソースを解放する。"""
        await self._client.aclose()

    async def embed(self, text: str) -> list[float]:
        """
        1つのテキストをベクトルに変換する。

        【Ollama API の呼び出し】
        POST /api/embeddings にモデル名とテキストを送信すると、
        768次元のベクトル（浮動小数点数のリスト）が返される。

        Args:
            text: ベクトル化するテキスト
        Returns:
            768次元の浮動小数点数リスト
        Raises:
            RuntimeError: API 呼び出しに失敗した場合
        """
        try:
            # Ollama の埋め込み API にリクエストを送信
            response = await self._client.post(
                "/api/embeddings",
                json={
                    "model": self.model,   # 使用するモデル名
                    "prompt": text,        # 埋め込みたいテキスト
                },
            )
            # raise_for_status(): HTTPエラー（4xx, 5xx）の場合に例外を発生
            response.raise_for_status()
            # JSON レスポンスからベクトルを取得
            data = response.json()
            return data.get("embedding", [])
        except httpx.HTTPError as e:
            logger.error("embedding_error", error=str(e))
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        複数のテキストを一括でベクトルに変換する。

        【注意】
        Ollama 自体はバッチ埋め込み API を持っていないため、
        内部的には embed() を順次呼び出しています。
        将来的にバッチ API が追加されれば、ここを最適化できます。

        Args:
            texts: ベクトル化するテキストのリスト
        Returns:
            各テキストに対応するベクトルのリスト
        """
        embeddings = []
        for text in texts:
            emb = await self.embed(text)  # 1つずつベクトル化
            embeddings.append(emb)
        return embeddings
