import asyncio
import logging

from apps.schemas.chatbot_schema import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    InitResponse,
)
from apps.services.rag_service import RAGService
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chatbot"])

_rag: RAGService | None = None


def _get_rag() -> RAGService:
    global _rag
    if _rag is None:
        _rag = RAGService()
    return _rag


# ── Chat ──────────────────────────────────────────────────────────────────────


@router.post("/", response_model=ChatResponse, summary="Ask the Equity Flow assistant")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the RAG-powered Qwen chatbot.

    - **message**: your question (1–2000 chars)
    - **session_id**: optional; omit to start a new conversation or pass an
      existing id to continue one.

    The assistant retrieves relevant knowledge-base chunks, then uses Qwen to
    compose a grounded answer.  Sources (filenames) are included in the response.
    """
    try:
        result = await asyncio.to_thread(
            _get_rag().chat,
            request.message,
            request.session_id,
        )
        return ChatResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Knowledge-base management ─────────────────────────────────────────────────


@router.post(
    "/init",
    response_model=InitResponse,
    summary="Index (or re-index) the knowledge base",
)
async def init_knowledge_base(force: bool = False) -> InitResponse:
    """
    Embed all markdown files in `src/apps/rag/knowledge/` and store them in
    ChromaDB.  Safe to call multiple times — uses upsert by default.

    Pass `?force=true` to wipe the collection and rebuild from scratch.
    """
    try:
        count = await asyncio.to_thread(_get_rag().initialize_knowledge_base, force)
        return InitResponse(
            message="Knowledge base ready." if not force else "Knowledge base rebuilt.",
            chunks_indexed=count,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Init error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Session management ────────────────────────────────────────────────────────


@router.delete("/session/{session_id}", summary="Clear a conversation session")
async def clear_session(session_id: str) -> dict:
    """Delete the stored conversation history for the given session."""
    cleared = _get_rag().clear_session(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"message": f"Session '{session_id}' cleared."}


# ── Health ────────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse, summary="Ollama health check")
async def health() -> HealthResponse:
    """Verify that the Ollama service is reachable and list available models."""
    try:
        rag = _get_rag()
        models_info = await asyncio.to_thread(rag._llm.list)
        model_names = [m.model for m in models_info.models]
        return HealthResponse(
            status="ok",
            detail=f"Ollama reachable. Models: {', '.join(model_names) or 'none pulled yet'}",
        )
    except Exception as exc:
        return HealthResponse(status="error", detail=str(exc))
