"""FAISS vector database implementation"""

import logging
import os
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from opentelemetry import trace

from app.vector_db.base import VectorDB
from app.config import get_settings
from app.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)


class FAISSVectorDB(VectorDB):
    """FAISS vector database implementation"""

    def __init__(self, dimension: int = 768, index_path: str = "./faiss_index"):
        """Initialize FAISS vector database
        Note: Google Gemini embeddings are 768-dimensional, OpenAI are 1536-dimensional
        """
        import numpy as np
        
        self.embeddings = get_embeddings()
        # Detect embedding dimension
        test_embedding = self.embeddings.embed_query("test")
        self.dimension = len(test_embedding)
        self.index_path = index_path

        # Create or load index
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            logger.info(f"Loaded FAISS index from {index_path}")
        else:
            self.index = faiss.IndexFlatL2(dimension)
            logger.info(f"Created new FAISS index with dimension {dimension}")

        # Store metadata and texts
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.text_store: Dict[str, str] = {}

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
        """Add documents to FAISS index"""        
        with tracer.start_as_current_span("faiss_add_documents") as span:
            span.set_attribute("documents_count", len(texts))

            if embeddings is None:
                embeddings = [self._get_embedding(text) for text in texts]

            if metadata is None:
                metadata = [{}] * len(texts)

            if ids is None:
                ids = [f"doc_{i}_{hash(text)}" for i, text in enumerate(texts)]

            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)

            # Add to index
            self.index.add(embeddings_array)

            # Store metadata and texts
            for id, text, meta in zip(ids, texts, metadata):
                self.metadata_store[id] = meta
                self.text_store[id] = text

            # Save index
            os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
            faiss.write_index(self.index, self.index_path)

            span.set_attribute("added_count", len(ids))
            logger.info(f"Added {len(ids)} documents to FAISS index")

            return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""        
        with tracer.start_as_current_span("faiss_similarity_search") as span:
            span.set_attribute("query_length", len(query))
            span.set_attribute("k", k)

            if embedding is None:
                embedding = self._get_embedding(query)

            # Convert to numpy array
            query_vector = np.array([embedding], dtype=np.float32)

            # Search
            distances, indices = self.index.search(query_vector, k)

            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx < 0:  # Invalid index
                    continue

                # Get ID from metadata store
                doc_ids = list(self.metadata_store.keys())
                if idx < len(doc_ids):
                    doc_id = doc_ids[idx]
                    results.append(
                        {
                            "id": doc_id,
                            "text": self.text_store.get(doc_id, ""),
                            "metadata": self.metadata_store.get(doc_id, {}),
                            "distance": float(distance),
                            "score": 1.0 / (1.0 + distance),  # Convert distance to score
                        }
                    )

            span.set_attribute("results_count", len(results))
            logger.info(f"Found {len(results)} similar documents")

            return results

    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs (Note: FAISS doesn't support deletion easily)"""
        with tracer.start_as_current_span("faiss_delete") as span:
            span.set_attribute("ids_count", len(ids))

            # Remove from stores
            for id in ids:
                self.metadata_store.pop(id, None)
                self.text_store.pop(id, None)

            logger.warning(
                "FAISS doesn't support efficient deletion. Consider rebuilding index."
            )
            return True

    def exists(self, id: str) -> bool:
        """Check if a document exists"""
        return id in self.metadata_store

