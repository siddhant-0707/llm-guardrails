"""Test agent orchestration"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status


@pytest.mark.asyncio
async def test_agent_execution(client, mock_memory_manager, mock_vector_db):
    """Test agent execution"""
    with patch("app.routes.agents.get_agent_orchestrator") as mock_orchestrator:
        mock_orch = MagicMock()
        mock_orch.execute = MagicMock(
            return_value={
                "response": "Test response",
                "context": {},
                "reasoning": "Test reasoning",
                "action": "answer",
            }
        )
        mock_orchestrator.return_value = mock_orch

        response = client.post(
            "/api/v1/agents/execute",
            json={
                "user_id": "test_user",
                "message": "Hello, agent!",
                "tools": [],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "context" in data
        assert "reasoning" in data
        assert "action" in data


def test_memory_add(client, mock_memory_manager):
    """Test adding memory"""
    with patch("app.routes.agents.get_memory_manager", return_value=mock_memory_manager):
        response = client.post(
            "/api/v1/agents/memory",
            json={
                "user_id": "test_user",
                "memory": "User likes Python",
                "metadata": {},
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "memory_id" in data
        assert data["status"] == "created"


def test_memory_search(client, mock_memory_manager):
    """Test searching memories"""
    with patch("app.routes.agents.get_memory_manager", return_value=mock_memory_manager):
        response = client.post(
            "/api/v1/agents/memory/search",
            json={
                "user_id": "test_user",
                "query": "Python",
                "limit": 5,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "count" in data

