from __future__ import annotations

import logging
from typing import Sequence

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        logger.debug("Embedding %d texts using %s", len(texts), self._model_name)
        # 実装は後で差し替える前提。ここでは長さベースのダミーベクトルを返す。
        return [[float(len(text))] * 3 for text in texts]
