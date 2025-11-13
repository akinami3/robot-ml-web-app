"""LLM client adapter supporting streaming responses."""

from __future__ import annotations

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class LLMClientAdapter:
    """Simple HTTP based client for external LLM providers."""

    def __init__(self) -> None:
        self._base_url = settings.llm_api_base or "https://api.openai.com/v1"
        self._api_key = settings.llm_api_key or ""
        self._client = httpx.AsyncClient(timeout=30.0)

    async def generate(self, *, prompt: str) -> str:
        if not self._api_key:
            logger.warning("llm_client.missing_api_key")
            return "LLM API key is not configured."

        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": "gpt-4o-mini", "prompt": prompt}
        response = await self._client.post(f"{self._base_url}/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("text", "")

    async def stream_response(self, *, prompt: str):
        logger.info("llm_client.stream_response.not_implemented", prompt_len=len(prompt))
        yield ""

    async def close(self) -> None:
        await self._client.aclose()
