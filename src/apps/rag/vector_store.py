"""
VectorStore
-----------
Thin ChromaDB wrapper.

- Uses a PersistentClient so the index survives restarts.
- The collection uses cosine distance (good for text embeddings).
- Supports upsert so re-indexing is idempotent.
"""

import logging
import os
from typing import Dict, List

import chromadb

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "equity_flow_knowledge"


class VectorStore:
    def __init__(self) -> None:
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self._client = chromadb.PersistentClient(path=db_path)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "VectorStore ready — collection '%s', %d doc(s) stored",
            _COLLECTION_NAME,
            self._col.count(),
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def add_chunks(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        batch_size: int = 100,
    ) -> None:
        """Upsert *chunks* with their corresponding *embeddings*."""
        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{"source": c["source"], "title": c["title"]} for c in chunks]

        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            self._col.upsert(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
            logger.debug("Upserted chunks %d–%d", start, end)

        logger.info("Stored %d chunk(s) in collection", len(chunks))

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def search(self, query_embedding: List[float], n_results: int = 5) -> List[Dict]:
        """
        Return the *n_results* most similar chunks.

        Each result dict has keys: text, source, title, distance.
        """
        results = self._col.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self._col.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        docs: List[Dict] = []
        for i, text in enumerate(results["documents"][0]):
            docs.append(
                {
                    "text": text,
                    "source": results["metadatas"][0][i]["source"],
                    "title": results["metadatas"][0][i]["title"],
                    "distance": results["distances"][0][i],
                }
            )
        return docs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def count(self) -> int:
        return self._col.count()

    def is_empty(self) -> bool:
        return self._col.count() == 0

    def reset(self) -> None:
        """Drop and recreate the collection (full re-index)."""
        self._client.delete_collection(_COLLECTION_NAME)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Collection reset.")
