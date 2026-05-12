import asyncio
import logging
from contextlib import asynccontextmanager

from apps.api.api import router as api_router
from apps.db import init_db
from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _init_rag_background() -> None:
    """
    Initialize the RAG knowledge base in the background so the server
    starts immediately.  Failures are logged but do not crash the app —
    the chatbot will retry on the first request.
    """
    try:
        # Import lazily so tests that don't need Ollama/Chroma still work
        from apps.services.rag_service import RAGService

        count = await asyncio.to_thread(RAGService().initialize_knowledge_base)
        logger.info("RAG knowledge base ready: %d chunks indexed.", count)
    except Exception as exc:
        logger.warning(
            "RAG initialization skipped (Ollama may not be running yet): %s", exc
        )


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    init_db()
    asyncio.create_task(_init_rag_background())
    yield


app = FastAPI(
    title="Equity Flow API Gateway",
    description=(
        "API Gateway for Equity Flow Microservices. "
        "Includes a RAG-powered chatbot assistant (Qwen via Ollama)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

origins = config(
    "ORIGINS",
    default=[],
    cast=lambda v: [s.strip() for s in v.split(",")] if isinstance(v, str) else v,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
