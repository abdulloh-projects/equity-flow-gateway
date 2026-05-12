"""
DocumentLoader
--------------
Reads every *.md file in the knowledge/ directory and splits them into
overlapping chunks suitable for embedding and retrieval.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentLoader:
    def __init__(self, knowledge_dir: Optional[str] = None) -> None:
        if knowledge_dir is None:
            knowledge_dir = os.path.join(os.path.dirname(__file__), "knowledge")
        self.knowledge_dir = Path(knowledge_dir)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_documents(self) -> List[Dict]:
        """Return a list of document dicts loaded from the knowledge directory."""
        documents: List[Dict] = []

        md_files = sorted(self.knowledge_dir.glob("*.md"))
        if not md_files:
            logger.warning("No .md files found in %s", self.knowledge_dir)
            return documents

        for file_path in md_files:
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                documents.append(
                    {
                        "content": content,
                        "source": file_path.name,
                        "title": file_path.stem.replace("_", " ").title(),
                    }
                )
                logger.debug("Loaded document: %s", file_path.name)
            except Exception as exc:
                logger.error("Failed to read %s: %s", file_path, exc)

        logger.info("Loaded %d document(s) from %s", len(documents), self.knowledge_dir)
        return documents

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def chunk_documents(
        self,
        documents: List[Dict],
        chunk_size: int = 400,
        overlap: int = 80,
    ) -> List[Dict]:
        """
        Split each document into word-based chunks with overlap.

        Parameters
        ----------
        chunk_size : int
            Maximum number of words per chunk.
        overlap : int
            Number of words shared between consecutive chunks.
        """
        chunks: List[Dict] = []

        for doc in documents:
            words = doc["content"].split()
            total_words = len(words)
            chunk_idx = 0
            i = 0

            while i < total_words:
                end = min(i + chunk_size, total_words)
                chunk_text = " ".join(words[i:end])

                chunks.append(
                    {
                        "text": chunk_text,
                        "source": doc["source"],
                        "title": doc["title"],
                        "chunk_id": f"{doc['source']}__chunk{chunk_idx}",
                    }
                )

                if end == total_words:
                    break

                i += chunk_size - overlap
                chunk_idx += 1

        logger.info(
            "Produced %d chunk(s) from %d document(s)", len(chunks), len(documents)
        )
        return chunks
