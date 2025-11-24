"""Long-term memory management with Mem0"""

import logging
from typing import Any, Dict, List, Optional

from opentelemetry import trace

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)

# Global instance
_memory_manager: Optional["MemoryManager"] = None


class MemoryManager:
    """Manage long-term memory using Mem0"""

    def __init__(self):
        """Initialize memory manager"""
        self.enabled = settings.mem0_api_key is not None
        self.api_key = settings.mem0_api_key
        self._client = None

        if self.enabled:
            try:
                # Initialize Mem0 client
                # Note: Mem0 SDK may need to be imported when available
                # from mem0 import Mem0
                # self._client = Mem0(api_key=self.api_key)
                logger.info("Mem0 memory manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Mem0: {e}")
                self.enabled = False

    def add_memory(
        self,
        user_id: str,
        memory: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Add a memory for a user"""
        if not self.enabled:
            return None

        with tracer.start_as_current_span("memory_add") as span:
            span.set_attribute("user_id", user_id)
            span.set_attribute("memory_length", len(memory))

            try:
                # Mem0 API call would go here
                # memory_id = self._client.add(user_id=user_id, memory=memory, metadata=metadata)
                # For now, return a mock ID
                logger.info(f"Added memory for user {user_id}")
                return f"memory_{hash(memory)}"
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error adding memory: {e}")
                return None

    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search memories for a user"""
        if not self.enabled:
            return []

        with tracer.start_as_current_span("memory_search") as span:
            span.set_attribute("user_id", user_id)
            span.set_attribute("query", query)

            try:
                # Mem0 API call would go here
                # results = self._client.search(user_id=user_id, query=query, limit=limit)
                # For now, return empty list
                logger.info(f"Searched memories for user {user_id}")
                return []
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error searching memories: {e}")
                return []

    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        if not self.enabled:
            return []

        with tracer.start_as_current_span("memory_get_all") as span:
            span.set_attribute("user_id", user_id)

            try:
                # Mem0 API call would go here
                # memories = self._client.get_all(user_id=user_id)
                logger.info(f"Retrieved all memories for user {user_id}")
                return []
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error getting memories: {e}")
                return []

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a memory"""
        if not self.enabled:
            return False

        with tracer.start_as_current_span("memory_delete") as span:
            span.set_attribute("user_id", user_id)
            span.set_attribute("memory_id", memory_id)

            try:
                # Mem0 API call would go here
                # success = self._client.delete(user_id=user_id, memory_id=memory_id)
                logger.info(f"Deleted memory {memory_id} for user {user_id}")
                return True
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error deleting memory: {e}")
                return False


# Global instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create memory manager instance"""
    global _memory_manager

    if _memory_manager is None:
        _memory_manager = MemoryManager()

    return _memory_manager

