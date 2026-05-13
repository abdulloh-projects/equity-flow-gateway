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

_OFF_TOPIC_REPLY = (
    "I can only answer questions about the Equity Flow platform. "
    "Please ask me something about investing, startups, campaigns, or how the platform works."
)


_EQUITY_KEYWORDS = {
    "equity",
    "startup",
    "startups",
    "invest",
    "investor",
    "investors",
    "investment",
    "campaign",
    "campaigns",
    "fund",
    "funding",
    "founder",
    "founders",
    "raise",
    "capital",
    "crowdfund",
    "crowdfunding",
    "pitch",
    "valuation",
    "revenue",
    "venture",
    "seed",
    "series",
    "portfolio",
    "roi",
    "returns",
    "due diligence",
    "term sheet",
    "cap table",
    "equity flow",
    "equityflow",
    "platform",
    "dashboard",
    "register",
    "login",
    "sign up",
    "signup",
    "account",
    "bank info",
    "mfo",
    "document",
    "api",
    "endpoint",
    "stock",
    "share",
    "shares",
    "dividend",
    "ipo",
    "round",
    "angel",
    "pre-seed",
    "runway",
    "burn rate",
    "gross margin",
    "active customers",
    "min investment",
}


def _is_equity_related(message: str) -> bool:
    text = message.lower()
    return any(kw in text for kw in _EQUITY_KEYWORDS)


_SYSTEM_PROMPT = """You are the official assistant for **Equity Flow** — an equity crowdfunding platform that connects startups with investors.

You ONLY answer questions about Equity Flow: how the platform works, how to invest, how to list a startup, campaigns, documents, bank info, account settings, and similar platform topics.

STRICT RULES:
- If the question is NOT related to Equity Flow or equity crowdfunding, respond with exactly: "I can only answer questions about the Equity Flow platform. Please ask me something about investing, startups, or how the platform works."
- Do NOT answer general knowledge questions, coding questions, math, science, politics, entertainment, or any topic unrelated to the platform.
- Do NOT offer general guidance or go off-topic under any circumstance.
- Answer only using the context provided below and established equity crowdfunding concepts.
- Do not invent field names, endpoint paths, or business rules not present in the context.
- Keep responses clear, concise, and professional.
- When referencing API endpoints, format them as code: `POST /api/auth/login`.

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
        if not _is_equity_related(message):
            if session_id is None:
                session_id = str(uuid.uuid4())
            return {
                "response": _OFF_TOPIC_REPLY,
                "session_id": session_id,
                "sources": [],
            }

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

        messages: List[Dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)}
        ]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": message})

        logger.debug("Calling %s with %d messages", self.llm_model, len(messages))
        raw = self._llm.chat(model=self.llm_model, messages=messages)
        reply: str = raw.message.content

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        if len(history) > 20:
            _conversation_store[session_id] = history[-20:]

        sources = sorted({doc["source"] for doc in relevant})
        return {"response": reply, "session_id": session_id, "sources": sources}

    def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        n_context_docs: int = 4,
    ):
        """
        Same as chat() but yields token strings one at a time via Ollama streaming.
        Yields tuples (token: str, session_id: str | None, sources: list | None).
        sources is non-None only on the final sentinel tuple.
        """
        if not _is_equity_related(message):
            if session_id is None:
                session_id = str(uuid.uuid4())
            yield (_OFF_TOPIC_REPLY, session_id, None)  # emit as a token
            yield ("", session_id, [])  # then the done sentinel
            return

        self._ensure_ready()

        if session_id is None:
            session_id = str(uuid.uuid4())

        history = _conversation_store.setdefault(session_id, [])

        query_vec = self._embedder.embed(message)
        relevant = self._store.search(query_vec, n_results=n_context_docs)
        context = "\n\n---\n\n".join(
            f"[{doc['title']}]\n{doc['text']}" for doc in relevant
        )

        messages: List[Dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)}
        ]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": message})

        full_reply = ""
        stream = self._llm.chat(model=self.llm_model, messages=messages, stream=True)
        for chunk in stream:
            token = chunk.message.content or ""
            full_reply += token
            yield (token, session_id, None)

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": full_reply})
        if len(history) > 20:
            _conversation_store[session_id] = history[-20:]

        sources = sorted({doc["source"] for doc in relevant})
        yield ("", session_id, sources)

    def clear_session(self, session_id: str) -> bool:
        """Delete conversation history for *session_id*. Returns True if found."""
        if session_id in _conversation_store:
            del _conversation_store[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        return list(_conversation_store.keys())
