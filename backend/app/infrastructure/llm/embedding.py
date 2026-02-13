"""Embedding service using Ollama's nomic-embed-text model."""

from __future__ import annotations

import structlog
from typing import Any

import httpx

logger = structlog.get_logger()


class EmbeddingService:
    """Generate text embeddings using Ollama."""

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "nomic-embed-text",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            response = await self._client.post(
                "/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except httpx.HTTPError as e:
            logger.error("embedding_error", error=str(e))
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Ollama doesn't natively support batch embedding,
        so we call embed() for each text sequentially.
        """
        embeddings = []
        for text in texts:
            emb = await self.embed(text)
            embeddings.append(emb)
        return embeddings
