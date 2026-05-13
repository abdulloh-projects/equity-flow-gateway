"""
Tests for the RAG chatbot system.

Everything that touches Ollama or ChromaDB is mocked — no real
AI/vector-DB calls are made.  The test matrix covers:

  - DocumentLoader  : load_documents, chunk_documents
  - VectorStore     : add_chunks, search, count, is_empty, reset
  - OllamaEmbedder  : embed, embed_batch
  - RAGService      : initialize_knowledge_base, chat, clear_session
  - Chatbot API     : POST /api/chat/, POST /api/chat/init,
                      DELETE /api/chat/session/{id}, GET /api/chat/health
"""

import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("AUTH_URL", "localhost:50051")
os.environ.setdefault("STARTUP_URL", "localhost:50052")
os.environ.setdefault("ORIGINS", "http://localhost:3000")
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("LLM_MODEL", "qwen2.5:3b")
os.environ.setdefault("EMBED_MODEL", "nomic-embed-text")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

RAG_SVC = "apps.services.rag_service"
EMBEDDER_MOD = "apps.rag.embedder"
VECTOR_MOD = "apps.rag.vector_store"
CHAT_EP = "apps.api.endpoints.chatbot"


@pytest.fixture(scope="module")
def app():
    # Patch Chroma + Ollama before the app (and lifespan) is imported
    with (
        patch("chromadb.PersistentClient"),
        patch("ollama.Client"),
    ):
        from apps.main import app as fastapi_app

        return fastapi_app


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── helpers ──────────────────────────────────────────────────────────────────


def _fake_embedding(dim: int = 8) -> list:
    return [0.1] * dim


def _make_mock_rag(
    chat_response: dict | None = None,
    init_count: int = 10,
    clear_result: bool = True,
):
    """Return a MagicMock that stands in for a RAGService instance."""
    svc = MagicMock()
    svc.chat.return_value = chat_response or {
        "response": "This is a helpful answer.",
        "session_id": "test-session-id",
        "sources": ["platform_overview.md"],
    }
    svc.initialize_knowledge_base.return_value = init_count
    svc.clear_session.return_value = clear_result
    svc._llm = MagicMock()
    return svc


# ===========================================================================
# DocumentLoader
# ===========================================================================


class TestDocumentLoader:
    def _loader(self, tmp_path: Path):
        from apps.rag.document_loader import DocumentLoader

        return DocumentLoader(knowledge_dir=str(tmp_path))

    def test_load_documents_reads_md_files(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide\nSome content here.")
        loader = self._loader(tmp_path)
        docs = loader.load_documents()
        assert len(docs) == 1
        assert docs[0]["source"] == "guide.md"
        assert "Some content here." in docs[0]["content"]

    def test_load_documents_skips_empty_files(self, tmp_path):
        (tmp_path / "empty.md").write_text("")
        loader = self._loader(tmp_path)
        docs = loader.load_documents()
        assert docs == []

    def test_load_documents_returns_empty_when_no_files(self, tmp_path):
        loader = self._loader(tmp_path)
        assert loader.load_documents() == []

    def test_load_documents_sets_title_from_filename(self, tmp_path):
        (tmp_path / "auth_guide.md").write_text("Auth content")
        loader = self._loader(tmp_path)
        docs = loader.load_documents()
        assert docs[0]["title"] == "Auth Guide"

    def test_load_documents_loads_multiple_files(self, tmp_path):
        for name in ["a.md", "b.md", "c.md"]:
            (tmp_path / name).write_text(f"Content of {name}")
        loader = self._loader(tmp_path)
        assert len(loader.load_documents()) == 3

    def test_chunk_documents_produces_chunks(self, tmp_path):
        loader = self._loader(tmp_path)
        docs = [{"content": " ".join(["word"] * 900), "source": "x.md", "title": "X"}]
        chunks = loader.chunk_documents(docs, chunk_size=400, overlap=80)
        assert len(chunks) > 1

    def test_chunk_documents_short_doc_produces_one_chunk(self, tmp_path):
        loader = self._loader(tmp_path)
        docs = [{"content": "hello world", "source": "x.md", "title": "X"}]
        chunks = loader.chunk_documents(docs, chunk_size=400, overlap=80)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "hello world"

    def test_chunk_documents_chunk_id_format(self, tmp_path):
        loader = self._loader(tmp_path)
        docs = [{"content": "a " * 10, "source": "doc.md", "title": "Doc"}]
        chunks = loader.chunk_documents(docs, chunk_size=5, overlap=1)
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_id"] == f"doc.md__chunk{i}"

    def test_chunk_documents_overlap_shares_words(self, tmp_path):
        loader = self._loader(tmp_path)
        words = [f"w{i}" for i in range(20)]
        docs = [{"content": " ".join(words), "source": "x.md", "title": "X"}]
        chunks = loader.chunk_documents(docs, chunk_size=10, overlap=4)
        # Second chunk should start 6 words after the first
        first_last = chunks[0]["text"].split()[-4:]
        second_first = chunks[1]["text"].split()[:4]
        assert first_last == second_first

    def test_chunk_documents_preserves_source_and_title(self, tmp_path):
        loader = self._loader(tmp_path)
        docs = [{"content": "text " * 5, "source": "src.md", "title": "Src"}]
        chunks = loader.chunk_documents(docs)
        for chunk in chunks:
            assert chunk["source"] == "src.md"
            assert chunk["title"] == "Src"


# ===========================================================================
# VectorStore
# ===========================================================================


class TestVectorStore:
    def _store(self):
        """Return a VectorStore with ChromaDB fully mocked out."""
        mock_col = MagicMock()
        mock_col.count.return_value = 0
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_col

        with patch("chromadb.PersistentClient", return_value=mock_client):
            from apps.rag.vector_store import VectorStore

            store = VectorStore()

        return store, mock_col, mock_client

    def test_is_empty_when_count_is_zero(self):
        store, mock_col, _ = self._store()
        mock_col.count.return_value = 0
        assert store.is_empty() is True

    def test_is_not_empty_when_count_is_positive(self):
        store, mock_col, _ = self._store()
        mock_col.count.return_value = 5
        assert store.is_empty() is False

    def test_count_returns_collection_count(self):
        store, mock_col, _ = self._store()
        mock_col.count.return_value = 42
        assert store.count() == 42

    def test_add_chunks_calls_upsert(self):
        store, mock_col, _ = self._store()
        chunks = [{"chunk_id": "id1", "text": "hello", "source": "a.md", "title": "A"}]
        store.add_chunks(chunks, [[0.1, 0.2]])
        mock_col.upsert.assert_called_once()

    def test_add_chunks_passes_correct_ids(self):
        store, mock_col, _ = self._store()
        chunks = [
            {"chunk_id": "c1", "text": "t1", "source": "a.md", "title": "A"},
            {"chunk_id": "c2", "text": "t2", "source": "a.md", "title": "A"},
        ]
        store.add_chunks(chunks, [[0.1] * 8, [0.2] * 8])
        call_kwargs = mock_col.upsert.call_args.kwargs
        assert call_kwargs["ids"] == ["c1", "c2"]

    def test_add_chunks_batches_large_inputs(self):
        store, mock_col, _ = self._store()
        n = 250
        chunks = [
            {"chunk_id": f"id{i}", "text": f"t{i}", "source": "a.md", "title": "A"}
            for i in range(n)
        ]
        store.add_chunks(chunks, [[0.1] * 8] * n, batch_size=100)
        assert mock_col.upsert.call_count == 3  # 100 + 100 + 50

    def test_search_returns_formatted_results(self):
        store, mock_col, _ = self._store()
        mock_col.count.return_value = 3
        mock_col.query.return_value = {
            "documents": [["doc text"]],
            "metadatas": [[{"source": "a.md", "title": "A"}]],
            "distances": [[0.12]],
        }
        results = store.search([0.1] * 8, n_results=1)
        assert len(results) == 1
        assert results[0]["text"] == "doc text"
        assert results[0]["source"] == "a.md"
        assert results[0]["distance"] == 0.12

    def test_reset_deletes_and_recreates_collection(self):
        store, _, mock_client = self._store()
        store.reset()
        mock_client.delete_collection.assert_called_once()
        assert mock_client.get_or_create_collection.call_count == 2  # init + reset


# ===========================================================================
# OllamaEmbedder
# ===========================================================================


class TestOllamaEmbedder:
    def _embedder(self):
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": _fake_embedding()}

        with patch("ollama.Client", return_value=mock_client):
            from apps.rag.embedder import OllamaEmbedder

            emb = OllamaEmbedder()

        return emb, mock_client

    def test_embed_returns_vector(self):
        emb, _ = self._embedder()
        vec = emb.embed("hello world")
        assert isinstance(vec, list)
        assert all(isinstance(x, float) for x in vec)

    def test_embed_calls_ollama_with_correct_prompt(self):
        emb, mock_client = self._embedder()
        emb.embed("test prompt")
        mock_client.embeddings.assert_called_once_with(
            model=emb.model, prompt="test prompt"
        )

    def test_embed_batch_returns_one_vector_per_text(self):
        emb, mock_client = self._embedder()
        vecs = emb.embed_batch(["a", "b", "c"])
        assert len(vecs) == 3
        assert mock_client.embeddings.call_count == 3

    def test_embed_batch_empty_input(self):
        emb, _ = self._embedder()
        assert emb.embed_batch([]) == []


# ===========================================================================
# RAGService
# ===========================================================================


class TestRAGServiceInit:
    def _make_service(self):
        mock_store = MagicMock()
        mock_embedder = MagicMock()
        mock_llm = MagicMock()
        mock_loader = MagicMock()

        with (
            patch(f"{RAG_SVC}.VectorStore", return_value=mock_store),
            patch(f"{RAG_SVC}.OllamaEmbedder", return_value=mock_embedder),
            patch(f"{RAG_SVC}.ollama.Client", return_value=mock_llm),
            patch(f"{RAG_SVC}.DocumentLoader", return_value=mock_loader),
            # Reset the module-level _kb_ready flag between tests
            patch(f"{RAG_SVC}._kb_ready", False),
        ):
            from apps.services.rag_service import RAGService

            svc = RAGService()

        return svc, mock_store, mock_embedder, mock_llm, mock_loader

    def test_initialize_indexes_documents(self):
        svc, mock_store, mock_embedder, _, mock_loader = self._make_service()
        mock_store.is_empty.return_value = True
        mock_store.count.return_value = 5
        mock_loader.load_documents.return_value = [
            {"content": "hello", "source": "a.md", "title": "A"}
        ]
        mock_loader.chunk_documents.return_value = [
            {
                "chunk_id": "a.md__chunk0",
                "text": "hello",
                "source": "a.md",
                "title": "A",
            }
        ]
        mock_embedder.embed_batch.return_value = [_fake_embedding()]

        count = svc.initialize_knowledge_base()

        mock_store.add_chunks.assert_called_once()
        assert count == 5

    def test_initialize_skips_when_already_loaded(self):
        svc, mock_store, _, _, mock_loader = self._make_service()
        mock_store.is_empty.return_value = False
        mock_store.count.return_value = 10

        import apps.services.rag_service as rag_mod

        rag_mod._kb_ready = True  # simulate already initialized

        count = svc.initialize_knowledge_base()

        mock_loader.load_documents.assert_not_called()
        assert count == 10

        rag_mod._kb_ready = False  # restore

    def test_initialize_raises_when_no_documents(self):
        svc, mock_store, _, _, mock_loader = self._make_service()
        mock_store.is_empty.return_value = True
        mock_loader.load_documents.return_value = []

        with pytest.raises(RuntimeError, match="No knowledge-base documents"):
            svc.initialize_knowledge_base()

    def test_initialize_force_resets_store(self):
        svc, mock_store, mock_embedder, _, mock_loader = self._make_service()
        mock_store.is_empty.return_value = False
        mock_store.count.return_value = 3
        mock_loader.load_documents.return_value = [
            {"content": "hi", "source": "b.md", "title": "B"}
        ]
        mock_loader.chunk_documents.return_value = [
            {"chunk_id": "b__0", "text": "hi", "source": "b.md", "title": "B"}
        ]
        mock_embedder.embed_batch.return_value = [_fake_embedding()]

        svc.initialize_knowledge_base(force=True)

        mock_store.reset.assert_called_once()


class TestRAGServiceChat:
    def _make_service_ready(self):
        mock_store = MagicMock()
        mock_embedder = MagicMock()
        mock_llm = MagicMock()
        mock_loader = MagicMock()

        mock_store.is_empty.return_value = False
        mock_store.count.return_value = 10
        mock_store.search.return_value = [
            {
                "text": "Equity Flow is a crowdfunding platform.",
                "source": "platform_overview.md",
                "title": "Platform Overview",
                "distance": 0.05,
            }
        ]
        mock_embedder.embed.return_value = _fake_embedding()

        # Simulate a Qwen response
        fake_msg = SimpleNamespace(content="You can create a campaign via the API.")
        mock_llm.chat.return_value = SimpleNamespace(message=fake_msg)

        with (
            patch(f"{RAG_SVC}.VectorStore", return_value=mock_store),
            patch(f"{RAG_SVC}.OllamaEmbedder", return_value=mock_embedder),
            patch(f"{RAG_SVC}.ollama.Client", return_value=mock_llm),
            patch(f"{RAG_SVC}.DocumentLoader", return_value=mock_loader),
            patch(f"{RAG_SVC}._kb_ready", True),
        ):
            from apps.services.rag_service import RAGService

            svc = RAGService()

        # Monkey-patch the already-set store etc. so they are the mocks
        svc._store = mock_store
        svc._embedder = mock_embedder
        svc._llm = mock_llm
        return svc, mock_store, mock_embedder, mock_llm

    def test_chat_returns_response_and_session_id(self):
        svc, _, _, _ = self._make_service_ready()
        with patch(f"{RAG_SVC}._kb_ready", True):
            result = svc.chat("How do I create a campaign?")
        assert "response" in result
        assert "session_id" in result
        assert isinstance(result["session_id"], str)

    def test_chat_returns_sources_list(self):
        svc, _, _, _ = self._make_service_ready()
        with patch(f"{RAG_SVC}._kb_ready", True):
            result = svc.chat("Tell me about Equity Flow")
        assert "sources" in result
        assert "platform_overview.md" in result["sources"]

    def test_chat_creates_new_session_id_when_none(self):
        svc, _, _, _ = self._make_service_ready()
        with patch(f"{RAG_SVC}._kb_ready", True):
            r1 = svc.chat("Hi")
            r2 = svc.chat("Hello")
        assert r1["session_id"] != r2["session_id"]

    def test_chat_reuses_session_id(self):
        svc, _, _, _ = self._make_service_ready()
        sid = str(uuid.uuid4())
        with patch(f"{RAG_SVC}._kb_ready", True):
            r1 = svc.chat("First message", session_id=sid)
            r2 = svc.chat("Second message", session_id=sid)
        assert r1["session_id"] == sid
        assert r2["session_id"] == sid

    def test_chat_calls_llm_with_user_message(self):
        svc, _, _, mock_llm = self._make_service_ready()
        with patch(f"{RAG_SVC}._kb_ready", True):
            svc.chat("What is Equity Flow?")
        call_messages = mock_llm.chat.call_args.kwargs["messages"]
        user_msgs = [m for m in call_messages if m["role"] == "user"]
        assert any("What is Equity Flow?" in m["content"] for m in user_msgs)

    def test_chat_calls_llm_with_system_prompt(self):
        svc, _, _, mock_llm = self._make_service_ready()
        with patch(f"{RAG_SVC}._kb_ready", True):
            svc.chat("How does equity investment work?")
        call_messages = mock_llm.chat.call_args.kwargs["messages"]
        sys_msgs = [m for m in call_messages if m["role"] == "system"]
        assert len(sys_msgs) == 1
        assert "Equity Flow" in sys_msgs[0]["content"]

    def test_chat_embeds_the_query(self):
        svc, _, mock_embedder, _ = self._make_service_ready()
        with patch(f"{RAG_SVC}._kb_ready", True):
            svc.chat("How does equity investment work?")
        mock_embedder.embed.assert_called_once_with("How does equity investment work?")

    def test_clear_session_removes_history(self):
        svc, _, _, _ = self._make_service_ready()
        sid = "my-session"
        with patch(f"{RAG_SVC}._kb_ready", True):
            svc.chat("How does equity investment work?", session_id=sid)
        assert svc.clear_session(sid) is True

    def test_clear_session_returns_false_for_unknown_id(self):
        svc, _, _, _ = self._make_service_ready()
        assert svc.clear_session("nonexistent-id") is False


# ===========================================================================
# Chatbot HTTP endpoints
# ===========================================================================


class TestChatEndpoint:
    async def test_chat_success_returns_200(self, client):
        mock_svc = _make_mock_rag()
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/", json={"message": "Hello"})

        assert response.status_code == 200
        body = response.json()
        assert body["response"] == "This is a helpful answer."
        assert body["session_id"] == "test-session-id"
        assert "platform_overview.md" in body["sources"]

    async def test_chat_passes_message_and_session_id(self, client):
        mock_svc = _make_mock_rag()
        sid = "existing-session"
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            await client.post("/api/chat/", json={"message": "Hi", "session_id": sid})

        mock_svc.chat.assert_called_once_with("Hi", sid)

    async def test_chat_empty_message_returns_422(self, client):
        with patch(f"{CHAT_EP}._get_rag", return_value=_make_mock_rag()):
            response = await client.post("/api/chat/", json={"message": ""})
        assert response.status_code == 422

    async def test_chat_no_body_returns_422(self, client):
        with patch(f"{CHAT_EP}._get_rag", return_value=_make_mock_rag()):
            response = await client.post("/api/chat/", json={})
        assert response.status_code == 422

    async def test_chat_runtime_error_returns_503(self, client):
        mock_svc = MagicMock()
        mock_svc.chat.side_effect = RuntimeError("No knowledge-base documents found.")
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/", json={"message": "hello"})
        assert response.status_code == 503

    async def test_chat_unexpected_error_returns_500(self, client):
        mock_svc = MagicMock()
        mock_svc.chat.side_effect = Exception("unexpected")
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/", json={"message": "hi"})
        assert response.status_code == 500

    async def test_chat_message_too_long_returns_422(self, client):
        long_msg = "x" * 2001
        with patch(f"{CHAT_EP}._get_rag", return_value=_make_mock_rag()):
            response = await client.post("/api/chat/", json={"message": long_msg})
        assert response.status_code == 422


class TestInitEndpoint:
    async def test_init_success_returns_200(self, client):
        mock_svc = _make_mock_rag(init_count=42)
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/init")

        assert response.status_code == 200
        body = response.json()
        assert body["chunks_indexed"] == 42
        assert "ready" in body["message"].lower()

    async def test_init_with_force_returns_rebuilt_message(self, client):
        mock_svc = _make_mock_rag(init_count=20)
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/init?force=true")

        assert response.status_code == 200
        body = response.json()
        assert "rebuilt" in body["message"].lower()
        mock_svc.initialize_knowledge_base.assert_called_once_with(True)

    async def test_init_runtime_error_returns_503(self, client):
        mock_svc = MagicMock()
        mock_svc.initialize_knowledge_base.side_effect = RuntimeError("no docs")
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/init")
        assert response.status_code == 503

    async def test_init_unexpected_error_returns_500(self, client):
        mock_svc = MagicMock()
        mock_svc.initialize_knowledge_base.side_effect = Exception("boom")
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.post("/api/chat/init")
        assert response.status_code == 500


class TestClearSessionEndpoint:
    async def test_clear_existing_session_returns_200(self, client):
        mock_svc = _make_mock_rag(clear_result=True)
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.delete("/api/chat/session/my-session-id")

        assert response.status_code == 200
        assert "my-session-id" in response.json()["message"]

    async def test_clear_unknown_session_returns_404(self, client):
        mock_svc = _make_mock_rag(clear_result=False)
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.delete("/api/chat/session/ghost-session")

        assert response.status_code == 404

    async def test_clear_calls_service_with_correct_session_id(self, client):
        mock_svc = _make_mock_rag(clear_result=True)
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            await client.delete("/api/chat/session/abc-123")

        mock_svc.clear_session.assert_called_once_with("abc-123")


class TestHealthEndpoint:
    async def test_health_ok_when_ollama_responds(self, client):
        mock_svc = MagicMock()
        fake_model = SimpleNamespace(model="qwen2.5:3b")
        mock_svc._llm.list.return_value = SimpleNamespace(models=[fake_model])
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.get("/api/chat/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "qwen2.5:3b" in body["detail"]

    async def test_health_error_when_ollama_unavailable(self, client):
        mock_svc = MagicMock()
        mock_svc._llm.list.side_effect = ConnectionRefusedError("refused")
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.get("/api/chat/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"

    async def test_health_always_returns_200(self, client):
        """Health endpoint must never raise — it returns status=error instead."""
        mock_svc = MagicMock()
        mock_svc._llm.list.side_effect = Exception("anything")
        with patch(f"{CHAT_EP}._get_rag", return_value=mock_svc):
            response = await client.get("/api/chat/health")

        assert response.status_code == 200
