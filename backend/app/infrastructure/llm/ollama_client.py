"""Ollama LLM client for chat generation."""

from __future__ import annotations

import structlog
from typing import AsyncIterator

import httpx

logger = structlog.get_logger()


class OllamaClient:
    """Client for Ollama local LLM API."""

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "llama3",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def generate(self, prompt: str, context: str = "") -> str:
        """Generate a response from the LLM."""
        system_prompt = (
            "You are a helpful robot AI assistant. You help operators understand "
            "robot systems, sensor data, and provide technical guidance. "
            "Answer concisely and accurately."
        )
        if context:
            system_prompt += (
                f"\n\nUse the following context to answer:\n{context}"
            )

        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            logger.error("ollama_generation_error", error=str(e))
            return f"Error generating response: {e}"

    async def generate_stream(
        self, prompt: str, context: str = ""
    ) -> AsyncIterator[str]:
        """Stream response tokens from the LLM."""
        system_prompt = (
            "You are a helpful robot AI assistant. You help operators understand "
            "robot systems, sensor data, and provide technical guidance."
        )
        if context:
            system_prompt += f"\n\nContext:\n{context}"

        try:
            async with self._client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                import json

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            logger.error("ollama_stream_error", error=str(e))
            yield f"Error: {e}"

    async def health_check(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[dict]:
        """List available models."""
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except httpx.HTTPError as e:
            logger.error("ollama_list_models_error", error=str(e))
            return []
