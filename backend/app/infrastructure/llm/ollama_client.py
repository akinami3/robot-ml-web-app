# ============================================================
# Ollama LLM クライアント（Ollama Client）
# ============================================================
# Ollama で動作するローカル LLM（大規模言語モデル）と
# 通信するクライアントクラスです。
#
# 【Ollama とは？】
# LLM をローカルマシンで簡単に実行するためのツール。
# Llama 3 などの高性能な言語モデルを Docker で実行できます。
# クラウドサービス（OpenAI等）に依存せず、プライバシーを保護。
#
# 【このクライアントの機能】
# 1. generate(): 一括で回答を生成（質問 → 回答テキスト）
# 2. generate_stream(): トークンごとにストリーミング生成
#    → ChatGPTのように1文字ずつ表示される仕組み
# 3. health_check(): Ollama サービスの稼働確認
# 4. list_models(): 利用可能なモデル一覧の取得
#
# 【Ollama Chat API の使い方】
# POST /api/chat に以下の JSON を送信:
# {
#   "model": "llama3",
#   "messages": [
#     {"role": "system", "content": "システムプロンプト"},
#     {"role": "user", "content": "ユーザーの質問"}
#   ],
#   "stream": true/false
# }
# ============================================================
"""Ollama LLM client for chat generation."""

from __future__ import annotations

import structlog
# AsyncIterator: 非同期イテレータの型ヒント（async for で使える）
from typing import AsyncIterator

import httpx

logger = structlog.get_logger()


class OllamaClient:
    """
    Ollama ローカル LLM API のクライアント。

    RAGService の LLMProvider プロトコルを実装。
    """

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "llama3",
        timeout: float = 120.0,
    ) -> None:
        """
        コンストラクタ。

        Args:
            base_url: Ollama サーバーの URL
            model: 使用する LLM モデル名（デフォルト: llama3）
            timeout: HTTP リクエストのタイムアウト（秒）
                LLM の生成は時間がかかるため、120秒と長めに設定
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        """HTTP クライアントを閉じてリソースを解放する。"""
        await self._client.aclose()

    async def generate(self, prompt: str, context: str = "") -> str:
        """
        LLM に質問して回答を生成する（一括方式）。

        【システムプロンプトとは？】
        LLM の「人格」や「役割」を設定するテキスト。
        ユーザーの質問の前に、LLM がどう振る舞うべきかを指示する。
        ここでは「ロボットAIアシスタント」として設定。

        【コンテキスト付き質問（RAG）】
        context が指定された場合、システムプロンプトにコンテキストを追加。
        LLM はこのコンテキストを参考にして回答を生成する。

        Args:
            prompt: ユーザーの質問文
            context: 参考にすべきコンテキスト（RAG検索結果、省略可）
        Returns:
            LLM が生成した回答テキスト
        """
        # システムプロンプト（LLMの役割設定）
        system_prompt = (
            "You are a helpful robot AI assistant. You help operators understand "
            "robot systems, sensor data, and provide technical guidance. "
            "Answer concisely and accurately."
        )
        # コンテキストがある場合はシステムプロンプトに追加
        if context:
            system_prompt += (
                f"\n\nUse the following context to answer:\n{context}"
            )

        try:
            # Ollama Chat API にリクエストを送信
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        # system ロール: LLMの動作指示
                        {"role": "system", "content": system_prompt},
                        # user ロール: ユーザーの質問
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,  # ストリーミングなし（一括で回答を返す）
                },
            )
            response.raise_for_status()
            data = response.json()
            # レスポンスから回答テキストを取得
            # data["message"]["content"] に回答が入っている
            return data.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            logger.error("ollama_generation_error", error=str(e))
            return f"Error generating response: {e}"

    async def generate_stream(
        self, prompt: str, context: str = ""
    ) -> AsyncIterator[str]:
        """
        LLM の回答をトークンごとにストリーミング生成する。

        【ストリーミングとは？】
        通常の API は全ての回答が完成してから返すが、
        ストリーミングではトークン（単語の断片）ごとに
        リアルタイムで返す。ChatGPT の表示と同じ仕組み。

        【yield とは？】
        return は関数を終了するが、yield は値を返した後も
        関数が続行する。async for で1つずつ値を取り出せる。

        Args:
            prompt: ユーザーの質問文
            context: 参考にすべきコンテキスト（省略可）
        Yields:
            LLM が生成する回答のトークン（文字列の断片）
        """
        system_prompt = (
            "You are a helpful robot AI assistant. You help operators understand "
            "robot systems, sensor data, and provide technical guidance."
        )
        if context:
            system_prompt += f"\n\nContext:\n{context}"

        try:
            # self._client.stream(): ストリーミングHTTPリクエスト
            # async with: レスポンスを受信し続けるコンテキスト
            async with self._client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": True,  # ストリーミング有効
                },
            ) as response:
                response.raise_for_status()
                import json

                # aiter_lines(): レスポンスを1行ずつ非同期で読み取る
                # 各行は JSON 形式: {"message": {"content": "Hello"}, "done": false}
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            # トークン（テキストの断片）を取得
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content  # トークンを呼び出し元に返す
                            # "done": true で生成完了
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue  # 不正な JSON はスキップ
        except httpx.HTTPError as e:
            logger.error("ollama_stream_error", error=str(e))
            yield f"Error: {e}"

    async def health_check(self) -> bool:
        """
        Ollama サービスの稼働確認。

        GET /api/tags エンドポイントにアクセスして、
        レスポンスコード 200 が返ればサービスは健全。

        Returns:
            サービスが稼働していれば True
        """
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[dict]:
        """
        利用可能な LLM モデルの一覧を取得する。

        Ollama で利用できるモデル（llama3, nomic-embed-text 等）の
        リストを返す。

        Returns:
            モデル情報の辞書のリスト
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except httpx.HTTPError as e:
            logger.error("ollama_list_models_error", error=str(e))
            return []
