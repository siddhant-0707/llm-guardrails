"""pgvector PostgreSQL implementation"""

import logging
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import execute_values
from opentelemetry import trace

from app.vector_db.base import VectorDB
from app.config import get_settings
from app.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)


class PgVectorDB(VectorDB):
    """PostgreSQL with pgvector extension"""

    def __init__(self):
        """Initialize pgvector database"""
        self.connection_url = settings.pgvector_url
        self.embeddings = get_embeddings()
        # Detect embedding dimension
        test_embedding = self.embeddings.embed_query("test")
        self.dimension = len(test_embedding)
        self._ensure_table()

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_url)

    def _ensure_table(self):
        """Ensure vector table exists"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Create table
                # Create table with dynamic dimension
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        text TEXT NOT NULL,
                        embedding vector({self.dimension}),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Create index for similarity search
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                    ON documents USING ivfflat (embedding vector_cosine_ops);
                    """
                )

                conn.commit()
                logger.info("pgvector table and index created")

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
        """Add documents to pgvector"""
        with tracer.start_as_current_span("pgvector_add_documents") as span:
            import json

            span.set_attribute("documents_count", len(texts))

            if embeddings is None:
                embeddings = [self._get_embedding(text) for text in texts]

            if metadata is None:
                metadata = [{}] * len(texts)

            if ids is None:
                ids = [f"doc_{i}_{hash(text)}" for i, text in enumerate(texts)]

            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    data = [
                        (
                            id,
                            text,
                            str(embedding),  # Convert to string for vector type
                            json.dumps(meta),
                        )
                        for id, text, embedding, meta in zip(ids, texts, embeddings, metadata)
                    ]

                    execute_values(
                        cur,
                        """
                        INSERT INTO documents (id, text, embedding, metadata)
                        VALUES %s
                        ON CONFLICT (id) DO UPDATE
                        SET text = EXCLUDED.text,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata;
                        """,
                        data,
                    )

                    conn.commit()

            span.set_attribute("added_count", len(ids))
            logger.info(f"Added {len(ids)} documents to pgvector")

            return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        with tracer.start_as_current_span("pgvector_similarity_search") as span:
            import json

            span.set_attribute("query_length", len(query))
            span.set_attribute("k", k)

            if embedding is None:
                embedding = self._get_embedding(query)

            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, text, metadata, 
                               1 - (embedding <=> %s::vector) as similarity
                        FROM documents
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                        """,
                        (str(embedding), str(embedding), k),
                    )

                    rows = cur.fetchall()

            results = [
                {
                    "id": row[0],
                    "text": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "score": float(row[3]),
                    "distance": 1.0 - float(row[3]),
                }
                for row in rows
            ]

            span.set_attribute("results_count", len(results))
            logger.info(f"Found {len(results)} similar documents in pgvector")

            return results

    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        with tracer.start_as_current_span("pgvector_delete") as span:
            span.set_attribute("ids_count", len(ids))

            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM documents WHERE id = ANY(%s);",
                        (ids,),
                    )
                    conn.commit()

            logger.info(f"Deleted {len(ids)} documents from pgvector")
            return True

    def exists(self, id: str) -> bool:
        """Check if a document exists"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS(SELECT 1 FROM documents WHERE id = %s);", (id,))
                return cur.fetchone()[0]

