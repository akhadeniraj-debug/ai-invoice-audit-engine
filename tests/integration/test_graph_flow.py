"""Integration tests for end-to-end LangGraph state machine with HITL interruption and resume."""

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agent.graph import create_audit_graph
from app.agent.state import DocAuditState
from app.database.connection import init_db
from app.schemas.invoice import AuditStatus, ReviewAction


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure in-memory SQLite tables are created before running graph flows."""
    init_db()


class TestGraphFlowHITL:
    """Tests the full LangGraph execution path with Human-in-the-Loop interruptions."""

    def test_valid_invoice_flows_directly_to_approved(self, sample_valid_invoice_dict):
        """Valid invoice must complete automatically with status APPROVED."""
        graph = create_audit_graph(checkpointer=MemorySaver())
        thread_id = "thread-valid-direct-001"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: DocAuditState = {
            "thread_id": thread_id,
            "filename": "valid_invoice.pdf",
            "s3_uri": "s3://test-bucket/valid_invoice.pdf",
            "extracted_data": sample_valid_invoice_dict,
        }

        # Run graph
        final_state = graph.invoke(initial_state, config=config)

        assert final_state["status"] == AuditStatus.APPROVED.value
        assert len(final_state["discrepancies"]) == 0

    def test_mismatched_invoice_interrupts_for_human_review(self, sample_math_mismatch_invoice_dict):
        """Invoice with discrepancies must halt at interrupt() and await reviewer decision."""
        graph = create_audit_graph(checkpointer=MemorySaver())
        thread_id = "thread-mismatch-hitl-002"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: DocAuditState = {
            "thread_id": thread_id,
            "filename": "faulty_invoice.pdf",
            "s3_uri": "s3://test-bucket/faulty_invoice.pdf",
            "extracted_data": sample_math_mismatch_invoice_dict,
        }

        # First run: should halt at the human_review_node interrupt
        graph.invoke(initial_state, config=config)

        # Inspect current graph state
        current_state = graph.get_state(config)
        assert current_state.next == ("human_review_node",)
        assert current_state.tasks[0].interrupts is not None
        assert len(current_state.tasks[0].interrupts) > 0

        interrupt_data = current_state.tasks[0].interrupts[0].value
        assert interrupt_data["status"] == AuditStatus.PENDING_REVIEW.value
        assert len(interrupt_data["discrepancies"]) > 0

    def test_reviewer_override_approval_resumes_to_approved(self, sample_math_mismatch_invoice_dict):
        """Auditor can override flagged invoice with APPROVE, concluding in status APPROVED."""
        graph = create_audit_graph(checkpointer=MemorySaver())
        thread_id = "thread-override-hitl-003"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: DocAuditState = {
            "thread_id": thread_id,
            "filename": "discrepant_invoice.pdf",
            "s3_uri": "s3://test-bucket/discrepant_invoice.pdf",
            "extracted_data": sample_math_mismatch_invoice_dict,
        }

        # Run until interrupt
        graph.invoke(initial_state, config=config)

        # Resume execution with an auditor override
        resume_payload = {
            "action": ReviewAction.APPROVE.value,
            "reviewer_notes": "Manager approved special vendor promotional discount difference.",
        }
        resumed_state = graph.invoke(Command(resume=resume_payload), config=config)

        assert resumed_state["status"] == AuditStatus.APPROVED.value
        assert resumed_state["reviewer_decision"] == ReviewAction.APPROVE.value
        assert resumed_state["reviewer_notes"] == resume_payload["reviewer_notes"]

    def test_reviewer_rejection_resumes_to_rejected(self, sample_math_mismatch_invoice_dict):
        """Auditor can reject flagged invoice, concluding in status REJECTED."""
        graph = create_audit_graph(checkpointer=MemorySaver())
        thread_id = "thread-reject-hitl-004"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: DocAuditState = {
            "thread_id": thread_id,
            "filename": "fraudulent_invoice.pdf",
            "s3_uri": "s3://test-bucket/fraudulent_invoice.pdf",
            "extracted_data": sample_math_mismatch_invoice_dict,
        }

        # Run until interrupt
        graph.invoke(initial_state, config=config)

        # Resume execution with rejection
        resume_payload = {
            "action": ReviewAction.REJECT.value,
            "reviewer_notes": "Math mismatch confirmed. Requested corrected invoice from vendor.",
        }
        resumed_state = graph.invoke(Command(resume=resume_payload), config=config)

        assert resumed_state["status"] == AuditStatus.REJECTED.value
        assert resumed_state["reviewer_decision"] == ReviewAction.REJECT.value
