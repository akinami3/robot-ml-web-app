# ============================================================
# RAGリポジトリインターフェース（RAG Repository Interface）
# ============================================================
# RAG（Retrieval-Augmented Generation: 検索拡張生成）に関連する
# ドキュメントとチャンク（文書の断片）の保存・検索を行うリポジトリです。
#
# 【RAGの仕組み】
# 1. ドキュメントをアップロード
# 2. テキストを小さなチャンク（断片）に分割
# 3. 各チャンクをベクトル（数値の配列）に変換（埋め込み）
# 4. ベクトルをデータベースに保存
# 5. 質問時に類似ベクトルを検索して関連文書を見つける
#
# 【ベクトル類似度検索とは？】
# 文章を数百次元のベクトルに変換し、コサイン類似度で
# 意味的に近い文書を高速に検索する技術です。
# PostgreSQL の pgvector 拡張を使用しています。
# ============================================================
"""RAG repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

# RAGDocument: アップロードされた文書全体
# DocumentChunk: 文書を分割した個々の断片
from ..entities.rag_document import DocumentChunk, RAGDocument
from .base import BaseRepository


class RAGRepository(BaseRepository[RAGDocument]):
    """
    RAGリポジトリの抽象インターフェース。

    ドキュメント管理とベクトル検索のメソッドを定義。
    実装では pgvector を使ったベクトル類似度検索を行います。
    """

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> list[RAGDocument]:
        """
        オーナー（アップロードしたユーザー）のドキュメント一覧を取得。

        Args:
            owner_id: ドキュメント所有者のユーザーID
        Returns:
            該当するドキュメントのリスト
        """
        ...

    @abstractmethod
    async def create_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """
        1つのチャンクをデータベースに保存する。
        チャンクにはテキスト内容とベクトル埋め込みが含まれる。

        Args:
            chunk: 保存するチャンクオブジェクト
        Returns:
            保存されたチャンク（IDが付与された状態）
        """
        ...

    @abstractmethod
    async def create_chunks_bulk(self, chunks: list[DocumentChunk]) -> int:
        """
        複数のチャンクを一括保存する（バルクインサート）。
        ドキュメント取り込み時に使用。1つの文書から数十のチャンクが
        生成されるため、一括保存で効率化する。

        Args:
            chunks: 保存するチャンクのリスト
        Returns:
            実際に保存された件数
        """
        ...

    @abstractmethod
    async def get_chunks_by_document(
        self, document_id: UUID
    ) -> list[DocumentChunk]:
        """
        指定ドキュメントに属する全チャンクを取得する。

        Args:
            document_id: ドキュメントのID
        Returns:
            チャンクのリスト（chunk_index 順）
        """
        ...

    @abstractmethod
    async def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        ベクトル類似度検索で、質問に関連するチャンクを見つける。

        【処理の流れ】
        1. 質問文をベクトル化（embedding パラメータ）
        2. データベース内の全チャンクのベクトルとコサイン類似度を計算
        3. 類似度が高い順にソートして上位 limit 件を返す

        Args:
            embedding: 質問文のベクトル埋め込み（768次元の浮動小数点数リスト）
            limit: 返すチャンクの最大件数（デフォルト: 5）
            min_similarity: 最低類似度の閾値（0.0〜1.0、デフォルト: 0.7）
        Returns:
            (チャンク, 類似度スコア) のタプルのリスト
            例: [(chunk1, 0.92), (chunk2, 0.85), ...]
        """
        ...

    @abstractmethod
    async def delete_chunks_by_document(self, document_id: UUID) -> int:
        """
        指定ドキュメントに属する全チャンクを削除する。
        ドキュメント削除時に、関連するチャンクも一緒に削除する。

        Args:
            document_id: ドキュメントのID
        Returns:
            削除されたチャンクの件数
        """
        ...
