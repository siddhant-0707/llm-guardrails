"""Test health check endpoints"""

import pytest
from fastapi import status


def test_health_check(client):
    """Test basic health check"""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "llm-guardrails"
    assert "version" in data


def test_detailed_health_check(client, mock_redis):
    """Test detailed health check"""
    from unittest.mock import patch
    from app.core.redis import get_redis

    with patch("app.routes.health.get_redis", return_value=mock_redis):
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "dependencies" in data
        assert "redis" in data["dependencies"]

