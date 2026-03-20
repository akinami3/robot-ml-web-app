"""
RAG document domain entity.
RAGドキュメント ドメインエンティティ

このファイルでは、RAG（Retrieval-Augmented Generation）で使用するドキュメントを
表現するデータ構造を定義しています。

RAGとは:
1. ユーザーが質問する
2. 関連するドキュメント（チャンク）をベクトル検索で見つける（Retrieval = 検索）
3. 見つけたドキュメントをLLM（大規模言語モデル）に渡して回答を生成する（Generation = 生成）

この仕組みにより、アップロードしたマニュアルや技術文書を基にAIが質問に答えられるようになります。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


# --- RAGドキュメントエンティティ ---
@dataclass
class RAGDocument:
    """
    RAG用にアップロードされたドキュメントを表すデータクラス。

    1つのドキュメント（PDF、テキストファイルなど）に対応します。
    ドキュメントは分割（チャンク化）されて検索に使用されます。

    Attributes:
        title: ドキュメントのタイトル
        content: ドキュメントの全文テキスト
        source: 元ファイルのパスやURL
        owner_id: アップロードしたユーザーのID
        id: ドキュメントの一意なID
        file_type: ファイルの種類（"text", "pdf", "markdown" など）
        file_size: ファイルサイズ（バイト単位）
        chunk_count: 分割されたチャンクの数
        metadata: 追加のメタデータ（著者、バージョンなど）
    """
    # --- 必須フィールド ---
    title: str          # ドキュメントのタイトル
    content: str        # ドキュメントの全文テキスト
    source: str         # 元ファイルのパスやURL
    owner_id: UUID      # アップロードしたユーザーのID

    # --- オプションフィールド ---
    id: UUID = field(default_factory=uuid4)
    file_type: str = "text"         # ファイルの種類（デフォルトはテキスト）
    file_size: int = 0              # ファイルサイズ（バイト）
    chunk_count: int = 0            # チャンク数（分割された断片の数）
    metadata: dict = field(default_factory=dict)   # 追加メタデータ
    created_at: datetime = field(default_factory=datetime.utcnow)   # 作成日時
    updated_at: datetime = field(default_factory=datetime.utcnow)   # 更新日時


# --- ドキュメントチャンクエンティティ ---
@dataclass
class DocumentChunk:
    """
    ドキュメントを分割した1つの断片（チャンク）を表すデータクラス。

    長いドキュメントを検索しやすい大きさ（通常数百〜数千文字）に分割したものです。
    各チャンクには「埋め込みベクトル（embedding）」が付与されます。

    埋め込みベクトルとは:
    テキストの意味を数値の配列（例: [0.12, -0.34, 0.56, ...]）で表現したものです。
    意味が似たテキスト同士は、ベクトルの距離が近くなります。
    これを使って「質問に似た内容のチャンク」を高速に検索できます（ベクトル検索）。

    Attributes:
        document_id: 元ドキュメントのID
        content: チャンクのテキスト内容
        embedding: 埋め込みベクトル（768次元の浮動小数点数リスト）
        id: チャンクの一意なID
        chunk_index: 元ドキュメント内での位置（0から始まる通し番号）
        token_count: このチャンクのトークン数（LLMの入力制限管理に使用）
        metadata: 追加メタデータ
    """
    # --- 必須フィールド ---
    document_id: UUID    # どのドキュメントに属するか
    content: str         # チャンクのテキスト内容

    # --- オプションフィールド ---
    # 埋め込みベクトル: テキストの意味を数値化したもの（768次元）
    embedding: list[float] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    chunk_index: int = 0        # 元ドキュメント内の位置番号
    token_count: int = 0        # トークン数（GPT等のLLMはトークン数で入力制限がある）
    metadata: dict = field(default_factory=dict)   # 追加メタデータ
    created_at: datetime = field(default_factory=datetime.utcnow)   # 作成日時
