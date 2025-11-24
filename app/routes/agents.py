"""Agent orchestration API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.orchestrator import AgentOrchestrator, get_agent_orchestrator
from app.agents.memory import MemoryManager, get_memory_manager

router = APIRouter()


class AgentRequest(BaseModel):
    """Agent execution request"""

    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User message")
    tools: list[dict] = Field(default_factory=list, description="Available tools")


class AgentResponse(BaseModel):
    """Agent execution response"""

    response: str
    context: dict
    reasoning: str
    action: str


class MemoryRequest(BaseModel):
    """Memory operation request"""

    user_id: str = Field(..., description="User identifier")
    memory: str = Field(..., description="Memory content")
    metadata: dict = Field(default_factory=dict, description="Memory metadata")


class MemorySearchRequest(BaseModel):
    """Memory search request"""

    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum results")


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> AgentResponse:
    """Execute agent workflow"""
    try:
        result = await orchestrator.execute(
            user_id=request.user_id,
            message=request.message,
            tools=request.tools,
        )
        return AgentResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )


@router.post("/memory", status_code=status.HTTP_201_CREATED)
async def add_memory(
    request: MemoryRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> dict:
    """Add a memory for a user"""
    memory_id = memory_manager.add_memory(
        user_id=request.user_id,
        memory=request.memory,
        metadata=request.metadata,
    )
    if not memory_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory service unavailable",
        )
    return {"memory_id": memory_id, "status": "created"}


@router.post("/memory/search")
async def search_memories(
    request: MemorySearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> dict:
    """Search memories for a user"""
    results = memory_manager.search_memories(
        user_id=request.user_id,
        query=request.query,
        limit=request.limit,
    )
    return {"results": results, "count": len(results)}


@router.get("/memory/{user_id}")
async def get_all_memories(
    user_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> dict:
    """Get all memories for a user"""
    memories = memory_manager.get_all_memories(user_id)
    return {"memories": memories, "count": len(memories)}


@router.delete("/memory/{user_id}/{memory_id}")
async def delete_memory(
    user_id: str,
    memory_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> dict:
    """Delete a memory"""
    success = memory_manager.delete_memory(user_id, memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} not found",
        )
    return {"status": "deleted", "memory_id": memory_id}

