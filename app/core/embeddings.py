"""Embedding provider abstraction"""

import logging
from typing import List, Optional

try:
    # LangChain v0.1.0+ uses langchain_core
    from langchain_core.embeddings import Embeddings
except ImportError:
    # Fallback for older versions
    from langchain.embeddings.base import Embeddings
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_embeddings() -> Embeddings:
    """Get embedding provider based on configuration"""
    # Use Google Gemini embeddings by default
    if settings.google_api_key:
        try:
            # Try langchain-google-genai first
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            logger.info("Using Google Gemini embeddings (langchain-google-genai)")
            return GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=settings.google_api_key,
            )
        except ImportError:
            try:
                # Fallback to langchain-google-vertexai if available
                from langchain_google_vertexai import VertexAIEmbeddings
                logger.info("Using Google Vertex AI embeddings")
                return VertexAIEmbeddings(
                    model_name="textembedding-gecko@001",
                    project=None,  # Not needed for API key auth
                )
            except ImportError:
                logger.warning("Google Gemini embeddings not available, falling back to OpenAI")
    
    # Fallback to OpenAI if Google is not available
    if settings.openai_api_key:
        try:
            try:
                from langchain_openai import OpenAIEmbeddings
            except ImportError:
                from langchain.embeddings import OpenAIEmbeddings
            logger.info("Using OpenAI embeddings")
            return OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        except ImportError:
            logger.error("OpenAI embeddings not available")
    
    raise ValueError(
        "No embedding provider available. Please set GOOGLE_API_KEY or OPENAI_API_KEY"
    )

