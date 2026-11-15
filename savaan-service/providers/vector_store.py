"""Vector store interface and adapters for episodic memory.

Owns both embedding and storage so each backend pairs them correctly:
- ChromaVectorStore: local ChromaDB + sentence-transformers (the original stack).
A Cloudflare Vectorize + Workers AI embeddings adapter lands with the
Cloudflare adapter PR.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VectorStore(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed one text into a vector."""

    @abstractmethod
    def add_episode(
        self,
        episode_id: str,
        documents: List[str],
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Store one episodic memory."""

    @abstractmethod
    def query_episodes(self, embedding: List[float], n_results: int = 5):
        """Return the raw query result for the nearest stored episodes."""


class ChromaVectorStore(VectorStore):
    def __init__(self, path: str = "./chroma_storage", collection: str = "episodic_memory"):
        import chromadb
        from sentence_transformers import SentenceTransformer

        client = chromadb.PersistentClient(path=path)
        self._collection = client.get_or_create_collection(name=collection)
        self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, text: str) -> List[float]:
        return self._embedding_model.encode([text])[0]

    def add_episode(self, episode_id, documents, embedding, metadata):
        self._collection.add(
            ids=[episode_id],
            documents=documents,
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def query_episodes(self, embedding, n_results: int = 5):
        return self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
