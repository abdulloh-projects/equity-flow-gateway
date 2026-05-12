import logging
import uuid
from typing import Dict, List, Optional

import ollama
from apps.rag.document_loader import DocumentLoader
from apps.rag.embedder import OllamaEmbedder
from apps.rag.vector_store import VectorStore
from decouple import config

logger = logging.getLogger(__name__)

_conversation_store: Dict[str, List[Dict]] = {}
_kb_ready: bool = False

_SYSTEM_PROMPT = """You are an expert assistant for **Equity Flow** — an equity crowdfunding platform that connects innovative startups with investors.

Your job is to answer questions about the platform accurately and helpfully, using the context documents provided below.

Guidelines:
- Answer only based on the provided context and your knowledge of equity crowdfunding.
- If the answer is not in the context, say so and offer general guidance where appropriate.
- Keep responses clear, concise, and professional.
- When referencing API endpoints, format them as code: `POST /api/auth/login`.
- Do not invent field names, endpoint paths, or business rules not present in the context.

=== PLATFORM CONTEXT ===
{context}
========================
"""


class RAGService:
    def __init__(self) -> None:
        self.llm_model: str = config("LLM_MODEL", default="qwen2.5:3b")
        ollama_url: str = config("OLLAMA_URL", default="http://localhost:11434")

        self._llm = ollama.Client(host=ollama_url)
        self._embedder = OllamaEmbedder()
        self._store = VectorStore()
        self._loader = DocumentLoader()

    # ── Knowledge-base lifecycle ──────────────────────────────────────────────

    def initialize_knowledge_base(self, force: bool = False) -> int:
        """
        Load, chunk, embed, and index all markdown knowledge files.

        Skips work if the vector store already has data and *force* is False.
        Returns the total number of chunks indexed.
        """
        global _kb_ready

        if _kb_ready and not self._store.is_empty() and not force:
            logger.info(
                "Knowledge base already loaded (%d chunks).", self._store.count()
            )
            return self._store.count()

        if force:
            self._store.reset()

        logger.info("Loading knowledge-base documents …")
        documents = self._loader.load_documents()
        if not documents:
            raise RuntimeError(
                "No knowledge-base documents found. "
                "Add .md files to src/apps/rag/knowledge/."
            )

        chunks = self._loader.chunk_documents(documents)
        logger.info("Embedding %d chunks (this may take a moment) …", len(chunks))

        embeddings = self._embedder.embed_batch([c["text"] for c in chunks])
        self._store.add_chunks(chunks, embeddings)

        _kb_ready = True
        count = self._store.count()
        logger.info("Knowledge base ready: %d chunks indexed.", count)
        return count

    def _ensure_ready(self) -> None:
        """Initialize the knowledge base if it is not yet ready."""
        if not _kb_ready or self._store.is_empty():
            self.initialize_knowledge_base()

    # ── Chat ─────────────────────────────────────────────────────────────────

    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        n_context_docs: int = 4,
    ) -> Dict:
        """
        Answer *message* using RAG + Qwen and return a result dict.

        Parameters
        ----------
        message : str
            The user's question.
        session_id : str | None
            Pass an existing session_id to continue a conversation.
            A new UUID is created when None.
        n_context_docs : int
            Number of knowledge chunks to retrieve.

        Returns
        -------
        dict with keys: response, session_id, sources
        """
        self._ensure_ready()

        if session_id is None:
            session_id = str(uuid.uuid4())

        history = _conversation_store.setdefault(session_id, [])

        # 1. Retrieve relevant context
        query_vec = self._embedder.embed(message)
        relevant = self._store.search(query_vec, n_results=n_context_docs)

        context = "\n\n---\n\n".join(
            f"[{doc['title']}]\n{doc['text']}" for doc in relevant
        )

        # 2. Build message list for the LLM
        messages: List[Dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)}
        ]
        # Include last 6 turns (3 exchanges) for context window efficiency
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": message})

        # 3. Generate
        logger.debug("Calling %s with %d messages", self.llm_model, len(messages))
        raw = self._llm.chat(model=self.llm_model, messages=messages)
        reply: str = raw.message.content

        # 4. Persist history (cap at 20 messages ~10 exchanges)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        if len(history) > 20:
            _conversation_store[session_id] = history[-20:]

        sources = sorted({doc["source"] for doc in relevant})
        return {"response": reply, "session_id": session_id, "sources": sources}

    # ── Session management ────────────────────────────────────────────────────

    def clear_session(self, session_id: str) -> bool:
        """Delete conversation history for *session_id*. Returns True if found."""
        if session_id in _conversation_store:
            del _conversation_store[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        return list(_conversation_store.keys())
