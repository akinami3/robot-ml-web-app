# ============================================================
# RAGサービス（RAG Service）
# ============================================================
# RAG（Retrieval-Augmented Generation: 検索拡張生成）の
# ビジネスロジックを担当するサービスクラスです。
#
# 【RAGとは？】
# LLM（大規模言語モデル）に、データベースから検索した関連文書を
# コンテキストとして渡すことで、より正確な回答を生成する技術。
#
# 【全体の処理フロー】
# ▼ ドキュメント取り込み（ingest）:
#   アップロード → テキスト分割 → ベクトル化 → DB保存
#
# ▼ 質問応答（query）:
#   質問 → ベクトル化 → 類似検索 → コンテキスト構築 → LLM生成
#
# 【Protocol（プロトコル）とは？】
# Python のダックタイピングを型安全に行うための仕組み。
# 「このメソッドを持っていれば OK」という条件を定義します。
# Java のインターフェースに似ていますが、明示的な継承は不要です。
# ============================================================
"""RAG service - domain logic for retrieval-augmented generation."""

from __future__ import annotations

import structlog
# Protocol: 構造的部分型（ダックタイピング）のための型ヒント
from typing import Any, Protocol
from uuid import UUID

# RAG関連のエンティティ（ドキュメントとチャンク）
from ..entities.rag_document import DocumentChunk, RAGDocument
# RAGリポジトリのインターフェース
from ..repositories.rag_repository import RAGRepository

logger = structlog.get_logger()


# ============================================================
# プロトコル定義（Protocol）
# ============================================================
# 以下の2つのプロトコルは、外部サービスへのインターフェースを定義します。
# 実際の実装は infrastructure 層にあります（OllamaClient, EmbeddingService）。

class EmbeddingProvider(Protocol):
    """
    テキストをベクトル（数値の配列）に変換するサービスのプロトコル。

    【ベクトル埋め込みとは？】
    テキストの「意味」を768次元の数値配列に変換すること。
    意味が似たテキストは、ベクトル空間で近い位置に配置されます。
    例: "犬が走る" と "ワンちゃんが駆ける" は近いベクトルになる。
    """

    async def embed(self, text: str) -> list[float]:
        """1つのテキストをベクトルに変換する。"""
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """複数のテキストを一括でベクトルに変換する（効率的）。"""
        ...


class LLMProvider(Protocol):
    """
    LLM（大規模言語モデル）への問い合わせインターフェース。

    【Ollama を使用】
    ローカルで動作する Llama 3 モデルに問い合わせます。
    generate: 一括で回答を生成
    generate_stream: トークンごとにストリーミング生成
    """

    async def generate(self, prompt: str, context: str = "") -> str:
        """プロンプトに対する回答を一括で生成する。"""
        ...

    async def generate_stream(self, prompt: str, context: str = ""):
        """プロンプトに対する回答をトークンごとにストリーミング生成する。"""
        ...


# ============================================================
# テキスト分割クラス（TextSplitter）
# ============================================================
class TextSplitter:
    """
    テキストを小さなチャンク（断片）に分割するユーティリティクラス。

    【なぜテキストを分割するのか？】
    1. LLM にはトークン数の制限がある（長すぎる文書は処理できない）
    2. 短いチャンクの方が、ベクトル検索の精度が高い
    3. 関連する部分だけをピンポイントで取得できる

    【オーバーラップとは？】
    隣接するチャンク同士が、一部の文を共有すること。
    チャンクの境界で文脈が途切れるのを防ぐため。
    例（overlap=50文字）:
      チャンク1: "...最後の50文字"
      チャンク2: "最後の50文字...新しい内容..."
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        """
        Args:
            chunk_size: 各チャンクの最大文字数（デフォルト: 500文字）
            overlap: チャンク間の重複文字数（デフォルト: 50文字）
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[str]:
        """
        テキストをチャンクのリストに分割する。

        【分割アルゴリズム】
        1. テキストが chunk_size 以下なら分割せずそのまま返す
        2. chunk_size ごとに分割するが、文の途中で切れないように
           段落区切り(\n\n) → 行区切り(\n) → 文区切り(. ) → 空白( )
           の順で適切な分割点を探す
        3. overlap 分だけ前のチャンクと重複させる

        Args:
            text: 分割するテキスト
        Returns:
            チャンクのリスト
        """
        # テキストが十分短い場合は分割不要
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size

            # テキストの途中の場合、自然な区切り位置を探す
            if end < len(text):
                # 優先順位の高い区切り文字から順に探す
                for sep in ["\n\n", "\n", ". ", " "]:
                    # rfind: 右側（末尾側）から区切り文字を探す
                    last_sep = text[start:end].rfind(sep)
                    # チャンクの半分より後ろに区切り位置がある場合のみ採用
                    # （あまりに前で切ると短すぎるチャンクになるため）
                    if last_sep > self.chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break

            # チャンクを追加（前後の空白を除去）
            chunks.append(text[start:end].strip())
            # 次のチャンクの開始位置（overlap 分だけ戻る）
            start = end - self.overlap

        # 空のチャンクを除去して返す
        return [c for c in chunks if c]


# ============================================================
# RAGサービスクラス（メインロジック）
# ============================================================
class RAGService:
    """
    RAGの全機能を提供するサービスクラス。

    主な機能：
    1. ingest_document: ドキュメントの取り込み（分割→埋め込み→保存）
    2. query: 質問応答（検索→コンテキスト構築→LLM生成）
    3. query_stream: ストリーミング質問応答
    4. delete_document: ドキュメントの削除（チャンクも含む）
    5. list_documents: ドキュメント一覧の取得
    """

    def __init__(
        self,
        rag_repo: RAGRepository,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        """
        コンストラクタ。3つの依存サービスを注入する。

        Args:
            rag_repo: RAGリポジトリ（データベースアクセス）
            embedding_provider: テキスト→ベクトル変換サービス
            llm_provider: LLM（大規模言語モデル）サービス
            chunk_size: テキスト分割のチャンクサイズ
            chunk_overlap: チャンク間のオーバーラップ文字数
        """
        self._repo = rag_repo
        self._embedder = embedding_provider
        self._llm = llm_provider
        # TextSplitter を初期化（テキスト分割用）
        self._splitter = TextSplitter(chunk_size, chunk_overlap)

    async def ingest_document(
        self,
        title: str,
        content: str,
        source: str,
        owner_id: UUID,
        file_type: str = "text",
        file_size: int = 0,
        metadata: dict | None = None,
    ) -> RAGDocument:
        """
        ドキュメントを取り込む（チャンク分割→ベクトル化→DB保存）。

        【処理の全体像】
        ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ テキスト  │ → │ チャンク  │ → │ ベクトル  │ → │ DB保存   │
        │ 分割     │    │ 配列     │    │ 変換     │    │         │
        └──────────┘    └──────────┘    └──────────┘    └──────────┘

        Args:
            title: ドキュメントのタイトル
            content: ドキュメントのテキスト内容
            source: ソース情報（ファイル名等）
            owner_id: アップロードしたユーザーのID
            file_type: ファイルの種類（text/plain, application/pdf等）
            file_size: ファイルサイズ（バイト）
            metadata: 追加のメタデータ（省略可）
        Returns:
            作成されたRAGドキュメント
        """
        # ステップ1: テキストをチャンクに分割
        chunk_texts = self._splitter.split(content)

        # ステップ2: 全チャンクを一括でベクトルに変換
        # embed_batch は複数テキストを効率的にベクトル化する
        embeddings = await self._embedder.embed_batch(chunk_texts)

        # ステップ3: ドキュメントエンティティを作成
        doc = RAGDocument(
            title=title,
            content=content[:1000],  # プレビュー用に先頭1000文字だけ保存
            source=source,
            owner_id=owner_id,
            file_type=file_type,
            file_size=file_size,
            chunk_count=len(chunk_texts),  # チャンク数を記録
            metadata=metadata or {},
        )
        created_doc = await self._repo.create(doc)

        # ステップ4: チャンクエンティティを作成してDB保存
        # zip(): 2つのリストを同時にループする関数
        # enumerate(): インデックス番号（0, 1, 2, ...）も取得する関数
        chunks = [
            DocumentChunk(
                document_id=created_doc.id,  # 親ドキュメントへの参照
                content=text,                # チャンクのテキスト内容
                embedding=emb,               # ベクトル埋め込み（768次元）
                chunk_index=i,               # チャンクの順番
                token_count=len(text.split()),  # 大まかなトークン数
            )
            for i, (text, emb) in enumerate(zip(chunk_texts, embeddings))
        ]
        # 一括保存（バルクインサート）
        await self._repo.create_chunks_bulk(chunks)

        logger.info(
            "document_ingested",
            doc_id=str(created_doc.id),
            title=title,
            chunks=len(chunks),
        )
        return created_doc

    async def query(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ) -> dict[str, Any]:
        """
        質問に対してRAGで回答を生成する。

        【処理フロー】
        1. 質問文をベクトルに変換
        2. ベクトル類似度で関連チャンクを検索
        3. チャンクがなければ、LLMに直接質問
        4. チャンクがあれば、コンテキスト付きでLLMに質問

        Args:
            question: ユーザーからの質問文
            top_k: 検索する類似チャンクの最大数（デフォルト: 5）
            min_similarity: 最低類似度の閾値（デフォルト: 0.7）
        Returns:
            回答を含む辞書:
            - answer: LLMが生成した回答テキスト
            - sources: 参照したチャンクの情報リスト
            - context_used: コンテキストを使用したか（True/False）
        """
        # ステップ1: 質問文をベクトルに変換
        query_embedding = await self._embedder.embed(question)

        # ステップ2: 類似チャンクを検索
        results = await self._repo.search_similar_chunks(
            embedding=query_embedding,
            limit=top_k,
            min_similarity=min_similarity,
        )

        # ステップ3: 関連チャンクが見つからない場合
        # → コンテキストなしでLLMに直接質問する
        if not results:
            answer = await self._llm.generate(question)
            return {
                "answer": answer,
                "sources": [],         # 参照元なし
                "context_used": False,  # コンテキスト未使用
            }

        # ステップ4: コンテキストを構築
        context_parts = []
        sources = []
        for chunk, similarity in results:
            context_parts.append(chunk.content)
            # 参照元情報を記録
            sources.append(
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "similarity": similarity,       # 類似度スコア
                    "preview": chunk.content[:200],  # プレビュー（先頭200文字）
                }
            )

        # チャンクを「---」区切りで連結してコンテキスト文字列を作る
        context = "\n\n---\n\n".join(context_parts)

        # ステップ5: コンテキスト付きプロンプトを作成してLLMに送信
        # このプロンプトの形式がRAGの核心部分
        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        answer = await self._llm.generate(prompt, context)

        return {
            "answer": answer,
            "sources": sources,
            "context_used": True,  # コンテキスト使用済み
        }

    async def query_stream(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ):
        """
        ストリーミング版の質問応答。

        【通常版との違い】
        - query(): 全回答を一括で生成してから返す
        - query_stream(): トークンごとにリアルタイムで返す（yield）

        【yield とは？】
        「async for token in ...」で1つずつ値を返すジェネレータ。
        return は関数を終了するが、yield は値を返した後も関数が継続する。
        ChatGPTのように文字が1文字ずつ表示される仕組みに使われる。

        Args:
            question: ユーザーからの質問文
            top_k: 検索する類似チャンクの最大数
            min_similarity: 最低類似度の閾値
        Yields:
            LLMが生成する回答のトークン（文字列の断片）
        """
        # 質問をベクトル化して類似チャンクを検索
        query_embedding = await self._embedder.embed(question)
        results = await self._repo.search_similar_chunks(
            embedding=query_embedding,
            limit=top_k,
            min_similarity=min_similarity,
        )

        # コンテキストの構築
        context = ""
        if results:
            context_parts = [chunk.content for chunk, _ in results]
            context = "\n\n---\n\n".join(context_parts)

        # プロンプトの作成（コンテキストがあれば付加、なければ質問のみ）
        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        ) if context else question

        # LLMからトークンをストリーミングで受信して、そのまま呼び出し元に yield
        async for token in self._llm.generate_stream(prompt, context):
            yield token

    async def delete_document(self, doc_id: UUID) -> bool:
        """
        ドキュメントとその全チャンクを削除する。

        【削除順序が重要】
        先にチャンク（子）を削除してから、ドキュメント（親）を削除する。
        親を先に削除すると、チャンクが孤立してしまう（データの不整合）。

        Args:
            doc_id: 削除するドキュメントのID
        Returns:
            削除に成功したら True
        """
        # まずチャンク（子）を削除
        await self._repo.delete_chunks_by_document(doc_id)
        # 次にドキュメント（親）を削除
        return await self._repo.delete(doc_id)

    async def list_documents(self, owner_id: UUID) -> list[RAGDocument]:
        """
        ユーザーが所有するドキュメント一覧を取得する。

        Args:
            owner_id: ドキュメント所有者のID
        Returns:
            ドキュメントのリスト
        """
        return await self._repo.get_by_owner(owner_id)
