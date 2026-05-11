"""
OllamaEmbedder
--------------
Thin wrapper around the Ollama embeddings endpoint.

Default model: nomic-embed-text (fast, 768-dim, great for RAG).
Override via the EMBED_MODEL env var.
"""

import logging
from typing import List

import ollama
from decouple import config

logger = logging.getLogger(__name__)


class OllamaEmbedder:
    def __init__(self) -> None:
        self.model: str = config("EMBED_MODEL", default="nomic-embed-text")
        ollama_url: str = config("OLLAMA_URL", default="http://localhost:11434")
        self.client = ollama.Client(host=ollama_url)
        logger.info("OllamaEmbedder ready (model=%s)", self.model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, text: str) -> List[float]:
        """Return a single embedding vector for *text*."""
        response = self.client.embeddings(model=self.model, prompt=text)
        return response["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return one embedding per entry in *texts*."""
        return [self.embed(t) for t in texts]
