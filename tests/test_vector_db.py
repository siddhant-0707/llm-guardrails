"""Test vector database functionality"""

import pytest
from app.vector_db.base import get_vector_db


def test_vector_db_factory():
    """Test vector DB factory function"""
    # Test that factory returns appropriate instance
    db = get_vector_db()
    assert db is not None
    assert hasattr(db, "add_documents")
    assert hasattr(db, "similarity_search")
    assert hasattr(db, "delete")
    assert hasattr(db, "exists")


@pytest.mark.skip(reason="Requires actual vector DB instance")
def test_faiss_add_documents():
    """Test adding documents to FAISS"""
    from app.vector_db.faiss import FAISSVectorDB

    db = FAISSVectorDB()
    ids = db.add_documents(
        texts=["Hello, world!", "This is a test"],
        metadata=[{"source": "test1"}, {"source": "test2"}],
    )
    assert len(ids) == 2


@pytest.mark.skip(reason="Requires actual vector DB instance")
def test_faiss_similarity_search():
    """Test similarity search in FAISS"""
    from app.vector_db.faiss import FAISSVectorDB

    db = FAISSVectorDB()
    results = db.similarity_search("Hello", k=5)
    assert isinstance(results, list)

