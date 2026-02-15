"""RAG (Retrieval-Augmented Generation) endpoints."""
# =============================================================================
# RAG（Retrieval-Augmented Generation）エンドポイント
# =============================================================================
#
# RAGとは？
# ---------
# RAG（検索拡張生成）は、AIが質問に答えるとき、
# まず関連するドキュメントを「検索」してから、その情報をもとに「回答を生成」する仕組みです。
#
# 通常のLLM（大規模言語モデル）は学習済みの知識だけで回答しますが、
# RAGを使うと、自分がアップロードしたドキュメントの内容をもとに回答できます。
#
# RAGの処理フロー:
#   【ドキュメント登録時】
#     アップロード → テキスト抽出 → チャンク分割 → ベクトル埋め込み → データベースに保存
#
#   【質問時】
#     質問 → 質問をベクトル化 → 類似ドキュメント検索 → LLMに質問+文脈を渡す → 回答生成
# =============================================================================

from __future__ import annotations

import structlog
from typing import Annotated
from uuid import UUID

# --- FastAPIの主要クラスをインポート ---
# APIRouter: エンドポイントをグループ化するルーター
# Depends: 依存性注入（DI）に使う仕組み
# File: ファイルアップロードのパラメータ定義
# HTTPException: HTTPエラーレスポンスを返すための例外
# UploadFile: アップロードされたファイルを扱うクラス
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

# StreamingResponse: データを少しずつストリーミングで返すレスポンス
# SSE（Server-Sent Events）でリアルタイムにトークンを返すために使います
from fastapi.responses import StreamingResponse

from ....config import get_settings
from ....domain.entities.audit_log import AuditAction
from ....domain.services.rag_service import RAGService
from ....infrastructure.llm.embedding import EmbeddingService
from ....infrastructure.llm.ollama_client import OllamaClient
from ..dependencies import AuditSvc, CurrentUser, RagRepo
from ..schemas import RAGDocumentResponse, RAGQueryRequest, RAGQueryResponse

# structlogでロガーを取得（構造化ログを出力できる）
logger = structlog.get_logger()

# "/rag" プレフィックス付きのルーターを作成
# tags=["rag"] はOpenAPIドキュメント（Swagger UI）でグループ表示するためのタグ
router = APIRouter(prefix="/rag", tags=["rag"])


# =============================================================================
# 依存性注入（DI）の設定
# =============================================================================
# get_rag_service は RAGService のインスタンスを生成するファクトリ関数です。
# FastAPIのDepends()を使い、エンドポイント関数の引数に自動的に注入されます。
#
# この仕組みにより：
#   - 設定値（URLやモデル名）を一箇所で管理できる
#   - テスト時にモックに差し替えやすい
#   - Ollamaクライアントや埋め込みサービスの初期化を隠蔽できる
# =============================================================================
def get_rag_service(rag_repo: RagRepo) -> RAGService:
    settings = get_settings()
    # Ollama LLMクライアント: テキスト生成（回答生成）に使用
    ollama = OllamaClient(
        base_url=settings.ollama_url,
        model=settings.llm_model,
    )
    # 埋め込み（Embedding）サービス: テキストをベクトルに変換するために使用
    # ベクトル化されたテキスト同士の「類似度」を計算して、関連ドキュメントを検索します
    embedding = EmbeddingService(
        base_url=settings.ollama_url,
        model=settings.embedding_model,
    )
    return RAGService(
        rag_repo=rag_repo,
        embedding_provider=embedding,
        llm_provider=ollama,
        # chunk_size: ドキュメントを分割するときの1チャンクあたりの文字数
        chunk_size=settings.rag_chunk_size,
        # chunk_overlap: チャンク間で重複させる文字数（文脈の連続性を保つため）
        chunk_overlap=settings.rag_chunk_overlap,
    )


# Annotated + Depends で型エイリアスを定義
# エンドポイント関数で「rag_svc: RagSvc」と書くだけでDI注入される
RagSvc = Annotated[RAGService, Depends(get_rag_service)]


# =============================================================================
# ドキュメントアップロード エンドポイント
# =============================================================================
# POST /rag/documents
#
# UploadFile を使ったファイルアップロードの流れ:
#   1. クライアントが multipart/form-data でファイルを送信
#   2. FastAPIが UploadFile オブジェクトとして受け取る
#   3. file.read() でファイル内容をバイト列として読み込む
#   4. テキストを抽出してRAGパイプラインに投入
#
# ドキュメント取り込み（Ingestion）フロー:
#   アップロード → テキスト抽出 → チャンク分割 → 埋め込みベクトル生成 → DB保存
# =============================================================================
@router.post("/documents", response_model=RAGDocumentResponse, status_code=201)
async def upload_document(
    current_user: CurrentUser,
    rag_svc: RagSvc,
    audit_svc: AuditSvc,
    # File(...)はファイルが必須であることを示す
    # UploadFileにはfilename, content_type, read()などの属性・メソッドがある
    file: UploadFile = File(...),
):
    # --- ファイルタイプのバリデーション ---
    # allowed_types: アップロードを許可するMIMEタイプのセット（集合）
    # セキュリティのため、許可されたファイル形式のみ受け付けます
    #   - text/plain: プレーンテキスト（.txt）
    #   - application/pdf: PDFファイル（.pdf）
    #   - text/markdown: マークダウン（.md）
    #   - text/csv: CSVファイル（.csv）
    allowed_types = {"text/plain", "application/pdf", "text/markdown", "text/csv"}
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # ファイルの全内容をバイト列として読み込む
    content = await file.read()

    # --- PDFからのテキスト抽出 ---
    # PDFはバイナリ形式なので、専用ライブラリ（pypdf）でテキストを取り出す必要がある
    # テキストファイルの場合は単純にUTF-8でデコードするだけでOK
    # Simple text extraction (PDF would need pypdf)
    if file.content_type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io

            # バイト列をファイルライクオブジェクトに変換してPDFリーダーに渡す
            reader = PdfReader(io.BytesIO(content))
            # 全ページのテキストを改行で連結
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to parse PDF: {e}"
            )
    else:
        # テキスト系ファイルはUTF-8でデコード（errors="replace"で不正な文字は置換）
        text = content.decode("utf-8", errors="replace")

    # RAGサービスにドキュメントを取り込む
    # 内部では: テキスト → チャンク分割 → 各チャンクをベクトル化 → DBに保存
    doc = await rag_svc.ingest_document(
        title=file.filename or "Untitled",
        content=text,
        source=file.filename or "upload",
        owner_id=current_user.id,
        file_type=file.content_type or "text/plain",
        file_size=len(content),
    )

    # 監査ログに記録（誰が何をしたかの追跡用）
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DOCUMENT_UPLOAD,
        resource_type="rag_document",
        resource_id=str(doc.id),
        details={"filename": file.filename, "chunks": doc.chunk_count},
    )

    # レスポンスとしてドキュメント情報を返す
    return RAGDocumentResponse(
        id=doc.id,
        title=doc.title,
        source=doc.source,
        file_type=doc.file_type,
        file_size=doc.file_size,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
    )


# =============================================================================
# ドキュメント一覧取得 エンドポイント
# =============================================================================
# GET /rag/documents
# ログインユーザーが所有するドキュメントの一覧を返す
# =============================================================================
@router.get("/documents", response_model=list[RAGDocumentResponse])
async def list_documents(
    current_user: CurrentUser,
    rag_svc: RagSvc,
):
    docs = await rag_svc.list_documents(current_user.id)
    return [
        RAGDocumentResponse(
            id=d.id,
            title=d.title,
            source=d.source,
            file_type=d.file_type,
            file_size=d.file_size,
            chunk_count=d.chunk_count,
            created_at=d.created_at,
        )
        for d in docs
    ]


# =============================================================================
# ドキュメント削除 エンドポイント
# =============================================================================
# DELETE /rag/documents/{doc_id}
# 指定されたドキュメントとそのチャンク・ベクトルデータを削除する
# status_code=204: 成功時はレスポンスボディなし（No Content）
# =============================================================================
@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    current_user: CurrentUser,
    rag_svc: RagSvc,
    audit_svc: AuditSvc,
):
    deleted = await rag_svc.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    # 監査ログに削除操作を記録
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DOCUMENT_DELETE,
        resource_type="rag_document",
        resource_id=str(doc_id),
    )


# =============================================================================
# RAGクエリ エンドポイント（通常版）
# =============================================================================
# POST /rag/query
#
# RAGクエリの処理フロー:
#   1. ユーザーの質問（question）を受け取る
#   2. 質問文をベクトル（埋め込み）に変換する
#   3. ベクトルの類似度検索で関連チャンクを取得（top_k件）
#   4. min_similarity以上の類似度を持つチャンクだけをフィルタリング
#   5. 取得したチャンク（文脈）と質問をLLMに渡して回答を生成
#   6. 回答・出典・使用した文脈をレスポンスとして返す
# =============================================================================
@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    body: RAGQueryRequest,
    current_user: CurrentUser,
    rag_svc: RagSvc,
    audit_svc: AuditSvc,
):
    result = await rag_svc.query(
        question=body.question,
        # top_k: 類似度が高い上位何件のチャンクを取得するか
        top_k=body.top_k,
        # min_similarity: 最低限必要な類似度のしきい値（0.0〜1.0）
        min_similarity=body.min_similarity,
    )

    # 監査ログにクエリ内容を記録（質問は先頭200文字まで）
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.RAG_QUERY,
        resource_type="rag",
        details={"question": body.question[:200]},
    )

    return RAGQueryResponse(
        answer=result["answer"],        # LLMが生成した回答
        sources=result["sources"],      # 参照した出典情報
        context_used=result["context_used"],  # 実際に使用した文脈テキスト
    )


# =============================================================================
# RAGクエリ ストリーミング エンドポイント
# =============================================================================
# POST /rag/query/stream
#
# SSE（Server-Sent Events）を使ったリアルタイムストリーミングレスポンス
#
# SSEとは？
# ---------
# サーバーからクライアントへ一方向にデータをリアルタイムに送信する仕組みです。
# ChatGPTのように、回答を1トークンずつリアルタイムに表示するために使います。
#
# SSEのデータ形式:
#   "data: トークン文字列\n\n"  ← 各イベントは "data: " で始まり "\n\n" で終わる
#   "data: [DONE]\n\n"         ← ストリーム終了を示す特別なメッセージ
#
# 通常のレスポンスとの違い:
#   - 通常: 全ての回答が生成されるまで待ってから一括返却
#   - SSE: 生成されたトークンを即座に1つずつクライアントに送信（体感速度が大幅向上）
# =============================================================================
@router.post("/query/stream")
async def query_rag_stream(
    body: RAGQueryRequest,
    current_user: CurrentUser,
    rag_svc: RagSvc,
):
    """Stream RAG query response using Server-Sent Events."""

    # 非同期ジェネレーター: トークンが生成されるたびにSSE形式でyieldする
    async def event_generator():
        async for token in rag_svc.query_stream(
            question=body.question,
            top_k=body.top_k,
            min_similarity=body.min_similarity,
        ):
            # 各トークンをSSE形式で送信
            yield f"data: {token}\n\n"
        # ストリーム終了を示す特別なメッセージ
        yield "data: [DONE]\n\n"

    # StreamingResponseでSSEストリームを返す
    return StreamingResponse(
        event_generator(),
        # text/event-stream: SSE専用のMIMEタイプ
        media_type="text/event-stream",
        headers={
            # キャッシュ無効化（常に最新データを受け取るため）
            "Cache-Control": "no-cache",
            # 接続を維持（ストリーミング中に切断されないように）
            "Connection": "keep-alive",
        },
    )
