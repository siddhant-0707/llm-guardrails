"""Base vector database interface"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorDB(ABC):
    """Abstract base class for vector databases"""

    @abstractmethod
    def add_documents(
        self,
        texts: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to the vector database"""
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        pass

    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if a document exists"""
        pass


def get_vector_db() -> VectorDB:
    """Get vector database instance based on configuration"""
    db_type = settings.vector_db_type.lower()

    if db_type == "faiss":
        from app.vector_db.faiss import FAISSVectorDB

        return FAISSVectorDB()
    elif db_type == "pgvector":
        from app.vector_db.pgvector import PgVectorDB

        return PgVectorDB()
    elif db_type == "qdrant":
        from app.vector_db.qdrant import QdrantVectorDB

        return QdrantVectorDB()
    else:
        raise ValueError(f"Unsupported vector database type: {db_type}")

