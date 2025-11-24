"""Qdrant vector database implementation"""

import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from opentelemetry import trace

from app.vector_db.base import VectorDB
from app.config import get_settings
from app.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)


class QdrantVectorDB(VectorDB):
    """Qdrant vector database implementation"""

    def __init__(self, collection_name: str = "documents", dimension: int = 768):
        """Initialize Qdrant client
        Note: Google Gemini embeddings are 768-dimensional
        """
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = collection_name
        self.embeddings = get_embeddings()
        # Detect embedding dimension
        test_embedding = self.embeddings.embed_query("test")
        self.dimension = len(test_embedding)
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure collection exists"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")
        else:
            logger.info(f"Using existing Qdrant collection: {self.collection_name}")

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        return self.embeddings.embed_query(text)

    def add_documents(
        self,
        texts: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to Qdrant"""
        with tracer.start_as_current_span("qdrant_add_documents") as span:
            span.set_attribute("documents_count", len(texts))

            if embeddings is None:
                embeddings = [self._get_embedding(text) for text in texts]

            if metadata is None:
                metadata = [{}] * len(texts)

            if ids is None:
                ids = [f"doc_{i}_{hash(text)}" for i, text in enumerate(texts)]

            points = [
                PointStruct(
                    id=hash(id) % (2**63),  # Qdrant uses integer IDs
                    vector=embedding,
                    payload={"text": text, "id": id, **meta},
                )
                for id, text, embedding, meta in zip(ids, texts, embeddings, metadata)
            ]

            self.client.upsert(collection_name=self.collection_name, points=points)

            span.set_attribute("added_count", len(ids))
            logger.info(f"Added {len(ids)} documents to Qdrant")

            return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        with tracer.start_as_current_span("qdrant_similarity_search") as span:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            span.set_attribute("query_length", len(query))
            span.set_attribute("k", k)

            if embedding is None:
                embedding = self._get_embedding(query)

            # Build filter if metadata provided
            query_filter = None
            if metadata:
                conditions = [
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in metadata.items()
                ]
                if conditions:
                    query_filter = Filter(must=conditions)

            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=k,
                query_filter=query_filter,
            )

            results = [
                {
                    "id": result.payload.get("id", ""),
                    "text": result.payload.get("text", ""),
                    "metadata": {k: v for k, v in result.payload.items() if k not in ["id", "text"]},
                    "score": result.score,
                    "distance": 1.0 - result.score,
                }
                for result in search_results
            ]

            span.set_attribute("results_count", len(results))
            logger.info(f"Found {len(results)} similar documents in Qdrant")

            return results

    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        with tracer.start_as_current_span("qdrant_delete") as span:
            span.set_attribute("ids_count", len(ids))

            # Convert string IDs to integer IDs
            integer_ids = [hash(id) % (2**63) for id in ids]

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=integer_ids,
            )

            logger.info(f"Deleted {len(ids)} documents from Qdrant")
            return True

    def exists(self, id: str) -> bool:
        """Check if a document exists"""
        integer_id = hash(id) % (2**63)
        result = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[integer_id],
        )
        return len(result) > 0

