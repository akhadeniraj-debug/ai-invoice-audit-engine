"""LangGraph worker nodes for document ingestion, deterministic audit, and HITL review."""

import logging
from typing import Any, Dict
from langgraph.types import interrupt

from app.agent.state import DocAuditState
from app.database.connection import SessionLocal
from app.database.models import DiscrepancyRecord, DocumentRecord
from app.schemas.invoice import AuditStatus, InvoiceData, ReviewAction
from app.services.audit_engine import AuditEngine
from app.services.aws_service import AWSDocumentService

logger = logging.getLogger(__name__)


def extract_schema_node(state: DocAuditState) -> Dict[str, Any]:
    """Node: Ingests raw OCR text and structures it into a typed InvoiceData schema."""
    extracted = state.get("extracted_data")
    if extracted:
        invoice = InvoiceData.model_validate(extracted)
    else:
        raw_text = state.get("raw_ocr_text", "")
        invoice = AWSDocumentService.parse_text_to_invoice(raw_text)

    return {
        "extracted_data": invoice.model_dump(mode="json"),
        "status": AuditStatus.PROCESSING.value,
    }


def deterministic_audit_node(state: DocAuditState) -> Dict[str, Any]:
    """Node: Runs zero-hallucination deterministic math and compliance checks."""
    extracted = state.get("extracted_data")
    if not extracted:
        raise ValueError("Missing extracted_data in agent state during audit node.")

    invoice = InvoiceData.model_validate(extracted)
    discrepancies = AuditEngine.audit(invoice)

    if discrepancies:
        return {
            "discrepancies": [d.model_dump(mode="json") for d in discrepancies],
            "status": AuditStatus.PENDING_REVIEW.value,
        }

    return {
        "discrepancies": [],
        "status": AuditStatus.APPROVED.value,
    }


def audit_condition_router(state: DocAuditState) -> str:
    """Conditional Edge: Routes to human review if errors exist, otherwise straight to persist."""
    discrepancies = state.get("discrepancies", [])
    if discrepancies and len(discrepancies) > 0:
        return "human_review_node"
    return "persist_node"


def human_review_node(state: DocAuditState) -> Dict[str, Any]:
    """Node: Pauses execution via interrupt() awaiting an authorized human reviewer decision."""
    # Graph execution will halt here. The payload passed to interrupt() is exposed to the caller.
    review_input: Any = interrupt({
        "thread_id": state.get("thread_id"),
        "status": AuditStatus.PENDING_REVIEW.value,
        "message": "Audit discrepancies detected. Awaiting human auditor resolution.",
        "discrepancies": state.get("discrepancies", []),
    })

    # When the graph is resumed with Command(resume=...), review_input receives that payload
    if not isinstance(review_input, dict):
        review_input = {"action": ReviewAction.REJECT.value, "reviewer_notes": "Invalid resume input"}

    decision = review_input.get("action", ReviewAction.REJECT.value)
    notes = review_input.get("reviewer_notes", "")

    if decision == ReviewAction.APPROVE.value:
        final_status = AuditStatus.APPROVED.value
    else:
        final_status = AuditStatus.REJECTED.value

    return {
        "status": final_status,
        "reviewer_decision": decision,
        "reviewer_notes": notes,
    }


def persist_node(state: DocAuditState) -> Dict[str, Any]:
    """Node: Atomically commits the document, extracted entities, and discrepancies into the database."""
    thread_id = state.get("thread_id", "")
    final_status = state.get("status", AuditStatus.APPROVED.value)
    extracted = state.get("extracted_data") or {}

    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.thread_id == thread_id).first()
        if not doc:
            doc = DocumentRecord(
                thread_id=thread_id,
                filename=state.get("filename", "unknown.pdf"),
                s3_uri=state.get("s3_uri", ""),
                status=final_status,
                raw_ocr_text=state.get("raw_ocr_text", ""),
            )
            db.add(doc)
            db.flush()

        # Update document fields
        doc.status = final_status
        doc.vendor_name = extracted.get("vendor_name")
        doc.invoice_number = extracted.get("invoice_number")
        doc.subtotal = extracted.get("subtotal")
        doc.tax_amount = extracted.get("tax_amount")
        doc.grand_total = extracted.get("grand_total")
        doc.currency = extracted.get("currency", "USD")
        doc.reviewer_decision = state.get("reviewer_decision")
        doc.reviewer_notes = state.get("reviewer_notes")

        # Update or record discrepancies
        discrepancies_data = state.get("discrepancies", [])
        if discrepancies_data and not doc.discrepancies:
            for d in discrepancies_data:
                record = DiscrepancyRecord(
                    document_id=doc.id,
                    discrepancy_type=d.get("discrepancy_type", "UNKNOWN"),
                    message=d.get("message", ""),
                    expected_value=d.get("expected_value"),
                    actual_value=d.get("actual_value"),
                    field_name=d.get("field_name"),
                )
                db.add(record)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist document state to DB: {e}")
        return {"status": final_status, "error_message": str(e)}
    finally:
        db.close()

    return {"status": final_status}
