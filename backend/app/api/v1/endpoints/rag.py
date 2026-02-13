"""RAG (Retrieval-Augmented Generation) endpoints."""

from __future__ import annotations

import structlog
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ....config import get_settings
from ....domain.entities.audit_log import AuditAction
from ....domain.services.rag_service import RAGService
from ....infrastructure.llm.embedding import EmbeddingService
from ....infrastructure.llm.ollama_client import OllamaClient
from ..dependencies import AuditSvc, CurrentUser, RagRepo
from ..schemas import RAGDocumentResponse, RAGQueryRequest, RAGQueryResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/rag", tags=["rag"])


def get_rag_service(rag_repo: RagRepo) -> RAGService:
    settings = get_settings()
    ollama = OllamaClient(
        base_url=settings.ollama_url,
        model=settings.llm_model,
    )
    embedding = EmbeddingService(
        base_url=settings.ollama_url,
        model=settings.embedding_model,
    )
    return RAGService(
        rag_repo=rag_repo,
        embedding_provider=embedding,
        llm_provider=ollama,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )


RagSvc = Annotated[RAGService, Depends(get_rag_service)]


@router.post("/documents", response_model=RAGDocumentResponse, status_code=201)
async def upload_document(
    current_user: CurrentUser,
    rag_svc: RagSvc,
    audit_svc: AuditSvc,
    file: UploadFile = File(...),
):
    allowed_types = {"text/plain", "application/pdf", "text/markdown", "text/csv"}
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    content = await file.read()

    # Simple text extraction (PDF would need pypdf)
    if file.content_type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to parse PDF: {e}"
            )
    else:
        text = content.decode("utf-8", errors="replace")

    doc = await rag_svc.ingest_document(
        title=file.filename or "Untitled",
        content=text,
        source=file.filename or "upload",
        owner_id=current_user.id,
        file_type=file.content_type or "text/plain",
        file_size=len(content),
    )

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DOCUMENT_UPLOAD,
        resource_type="rag_document",
        resource_id=str(doc.id),
        details={"filename": file.filename, "chunks": doc.chunk_count},
    )

    return RAGDocumentResponse(
        id=doc.id,
        title=doc.title,
        source=doc.source,
        file_type=doc.file_type,
        file_size=doc.file_size,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
    )


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

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DOCUMENT_DELETE,
        resource_type="rag_document",
        resource_id=str(doc_id),
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    body: RAGQueryRequest,
    current_user: CurrentUser,
    rag_svc: RagSvc,
    audit_svc: AuditSvc,
):
    result = await rag_svc.query(
        question=body.question,
        top_k=body.top_k,
        min_similarity=body.min_similarity,
    )

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.RAG_QUERY,
        resource_type="rag",
        details={"question": body.question[:200]},
    )

    return RAGQueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        context_used=result["context_used"],
    )


@router.post("/query/stream")
async def query_rag_stream(
    body: RAGQueryRequest,
    current_user: CurrentUser,
    rag_svc: RagSvc,
):
    """Stream RAG query response using Server-Sent Events."""

    async def event_generator():
        async for token in rag_svc.query_stream(
            question=body.question,
            top_k=body.top_k,
            min_similarity=body.min_similarity,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
