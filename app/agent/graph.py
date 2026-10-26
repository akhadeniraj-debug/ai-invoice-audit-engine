"""StateGraph assembly and checkpoint configuration for DocAudit-Core."""

from typing import Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    audit_condition_router,
    deterministic_audit_node,
    extract_schema_node,
    human_review_node,
    persist_node,
)
from app.agent.state import DocAuditState


def create_audit_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    """Compiles and returns the cyclic DocAudit StateGraph with checkpointing."""
    workflow = StateGraph(DocAuditState)

    # 1. Register worker nodes
    workflow.add_node("extract_schema_node", extract_schema_node)
    workflow.add_node("deterministic_audit_node", deterministic_audit_node)
    workflow.add_node("human_review_node", human_review_node)
    workflow.add_node("persist_node", persist_node)

    # 2. Define workflow transitions
    workflow.add_edge(START, "extract_schema_node")
    workflow.add_edge("extract_schema_node", "deterministic_audit_node")

    # 3. Conditional routing: route to human review on errors, otherwise straight to persist
    workflow.add_conditional_edges(
        "deterministic_audit_node",
        audit_condition_router,
        {
            "human_review_node": "human_review_node",
            "persist_node": "persist_node",
        },
    )

    # 4. From human review, proceed to persist
    workflow.add_edge("human_review_node", "persist_node")
    workflow.add_edge("persist_node", END)

    # 5. Compile with checkpointer for stateful interruption and resume
    saver = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=saver)


# Shared global compiled graph instance with in-memory checkpointer
audit_agent = create_audit_graph()
