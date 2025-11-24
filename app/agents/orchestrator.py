"""Agent orchestration using LangGraph"""

import logging
from typing import Any, Dict, List, Optional

try:
    # LangChain v0.1.0+ uses langchain_core
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
except ImportError:
    # Fallback for older versions
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from opentelemetry import trace

from app.agents.memory import MemoryManager, get_memory_manager
from app.config import get_settings
from app.vector_db.base import VectorDB, get_vector_db

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)

# Global instance
_agent_orchestrator: Optional["AgentOrchestrator"] = None


# AgentState is defined inline in _build_graph as TypedDict


class AgentOrchestrator:
    """Orchestrate agent execution with LangGraph"""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        vector_db: Optional[VectorDB] = None,
    ):
        """Initialize agent orchestrator"""
        self.memory = memory_manager or get_memory_manager()
        self.vector_db = vector_db or get_vector_db()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build LangGraph workflow"""
        # Note: LangGraph expects TypedDict or similar for state
        # This is a simplified implementation - adjust based on your LangGraph version
        from typing import TypedDict
        
        class AgentStateDict(TypedDict):
            messages: List[BaseMessage]
            user_id: str
            tools: List[Dict[str, Any]]
            context: Dict[str, Any]
            retrieved_docs: List[Dict[str, Any]]
            reasoning: str
            action: str
            response: str
        
        workflow = StateGraph(AgentStateDict)

        # Add nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("action", self._action_node)
        workflow.add_node("respond", self._respond_node)

        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "reason")
        workflow.add_edge("reason", "action")
        workflow.add_edge("action", "respond")
        workflow.add_edge("respond", END)

        return workflow.compile()

    def _retrieve_node(self, state):
        """Retrieval node: fetch relevant context"""
        with tracer.start_as_current_span("agent_retrieve") as span:
            span.set_attribute("user_id", state["user_id"])
            span.set_attribute("query", state["messages"][-1].content if state["messages"] else "")

            # Retrieve from vector DB
            query = state["messages"][-1].content if state["messages"] else ""
            retrieved_docs = self.vector_db.similarity_search(
                query=query,
                k=5,
                metadata={"user_id": state["user_id"]},
            )

            # Retrieve from memory
            memories = self.memory.search_memories(state["user_id"], query, limit=3)

            span.set_attribute("retrieved_docs", len(retrieved_docs))
            span.set_attribute("retrieved_memories", len(memories))

            return {
                "retrieved_docs": retrieved_docs,
                "context": {
                    "documents": retrieved_docs,
                    "memories": memories,
                },
            }

    def _reason_node(self, state):
        """Reasoning node: analyze context and determine action"""
        with tracer.start_as_current_span("agent_reason") as span:
            # Simplified reasoning - in production, use LLM
            context_summary = f"Found {len(state.get('retrieved_docs', []))} documents and {len(state.get('context', {}).get('memories', []))} memories"

            # Determine action based on state
            action = "answer"  # Default action

            span.set_attribute("action", action)
            span.set_attribute("reasoning", context_summary)

            return {
                "reasoning": context_summary,
                "action": action,
            }

    def _action_node(self, state):
        """Action node: execute tool or generate response"""
        with tracer.start_as_current_span("agent_action") as span:
            span.set_attribute("action", state.get("action", ""))

            # Execute action based on state.action
            # For now, generate a simple response
            response = f"Based on the retrieved context, I can help you with: {state.get('reasoning', '')}"

            span.set_attribute("response_length", len(response))

            return {"response": response}

    def _respond_node(self, state):
        """Response node: format and return final response"""
        with tracer.start_as_current_span("agent_respond") as span:
            # Add response to messages
            response = state.get("response", "")
            response_message = AIMessage(content=response)

            # Store in memory if relevant
            if response and len(response) > 50:
                self.memory.add_memory(
                    user_id=state["user_id"],
                    memory=response,
                    metadata={"source": "agent_response"},
                )

            span.set_attribute("response_length", len(response))

            return {"messages": state["messages"] + [response_message]}

    async def execute(
        self,
        user_id: str,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute agent workflow"""
        with tracer.start_as_current_span("agent_execute") as span:
            span.set_attribute("user_id", user_id)

            initial_state = {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "tools": tools or [],
                "context": {},
                "retrieved_docs": [],
                "reasoning": "",
                "action": "",
                "response": "",
            }

            # Execute graph
            result = await self.graph.ainvoke(initial_state)

            logger.info(f"Agent execution completed for user {user_id}")

            return {
                "response": result["response"],
                "context": result["context"],
                "reasoning": result["reasoning"],
                "action": result["action"],
            }


# Global instance
_agent_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create agent orchestrator instance"""
    global _agent_orchestrator

    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()

    return _agent_orchestrator

