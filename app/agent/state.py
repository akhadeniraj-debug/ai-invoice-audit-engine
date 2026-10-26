"""TypedDict state definitions for the LangGraph audit orchestration."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class DocAuditState(TypedDict, total=False):
    """The central state dictionary passed across LangGraph nodes.

    Attributes:
        thread_id: Unique idempotency and checkpoint thread identifier.
        filename: Original business document filename.
        s3_uri: Immutable storage path in S3.
        raw_ocr_text: Raw OCR text produced by AWS Textract.
        extracted_data: Serialized InvoiceData model.
        discrepancies: Serialized list of AuditDiscrepancy models.
        status: Current document lifecycle status (PROCESSING, APPROVED, PENDING_REVIEW, REJECTED).
        reviewer_decision: Human auditor resolution (APPROVE or REJECT).
        reviewer_notes: Auditor justification commentary.
        error_message: Optional execution failure message.
    """

    thread_id: str
    filename: str
    s3_uri: str
    raw_ocr_text: str
    extracted_data: Optional[Dict[str, Any]]
    discrepancies: List[Dict[str, Any]]
    status: str
    reviewer_decision: Optional[str]
    reviewer_notes: Optional[str]
    error_message: Optional[str]
