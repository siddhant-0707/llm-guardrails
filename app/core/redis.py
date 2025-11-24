"""Redis client setup"""

import logging
from typing import Optional

from redis import Redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[Redis] = None


def get_redis() -> Redis:
    """Get or create Redis client"""
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

        # Test connection
        try:
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    return _redis_client


def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client

    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

