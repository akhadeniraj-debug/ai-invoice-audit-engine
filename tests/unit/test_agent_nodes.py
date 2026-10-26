"""Unit tests for LangGraph worker nodes in isolation."""

from decimal import Decimal
import pytest

from app.agent.nodes import (
    audit_condition_router,
    deterministic_audit_node,
    extract_schema_node,
)
from app.agent.state import DocAuditState
from app.schemas.invoice import AuditStatus


class TestAgentNodes:
    """Tests individual LangGraph node behavior."""

    def test_extract_schema_node_with_pre_extracted_data(self, sample_valid_invoice_dict):
        """extract_schema_node should serialize valid invoice dictionary into state."""
        initial_state: DocAuditState = {
            "thread_id": "test-thread-01",
            "extracted_data": sample_valid_invoice_dict,
        }
        result = extract_schema_node(initial_state)
        assert result["status"] == AuditStatus.PROCESSING.value
        assert result["extracted_data"]["vendor_name"] == "Apex Cloud Technologies"

    def test_deterministic_audit_node_approves_valid_data(self, sample_valid_invoice_dict):
        """deterministic_audit_node should assign status APPROVED when no errors are found."""
        state: DocAuditState = {
            "thread_id": "test-thread-02",
            "extracted_data": sample_valid_invoice_dict,
        }
        result = deterministic_audit_node(state)
        assert result["status"] == AuditStatus.APPROVED.value
        assert len(result["discrepancies"]) == 0

    def test_deterministic_audit_node_flags_errors(self, sample_math_mismatch_invoice_dict):
        """deterministic_audit_node should assign PENDING_REVIEW when math mismatch is detected."""
        state: DocAuditState = {
            "thread_id": "test-thread-03",
            "extracted_data": sample_math_mismatch_invoice_dict,
        }
        result = deterministic_audit_node(state)
        assert result["status"] == AuditStatus.PENDING_REVIEW.value
        assert len(result["discrepancies"]) > 0

    def test_audit_condition_router(self):
        """Router should direct to human_review_node if errors exist, otherwise to persist_node."""
        state_with_errors: DocAuditState = {
            "discrepancies": [{"discrepancy_type": "SUBTOTAL_MISMATCH", "message": "error"}],
        }
        assert audit_condition_router(state_with_errors) == "human_review_node"

        state_clean: DocAuditState = {"discrepancies": []}
        assert audit_condition_router(state_clean) == "persist_node"
