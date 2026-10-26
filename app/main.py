"""FastAPI application factory, dependency injection, and REST API routes for DocAudit-Core."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from langgraph.types import Command
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agent.graph import audit_agent
from app.config import settings
from app.database.connection import get_db, init_db
from app.database.models import DiscrepancyRecord, DocumentRecord
from app.schemas.invoice import AuditStatus, ReviewRequest
from app.services.aws_service import AWSDocumentService

logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    # Ensure database tables exist on startup
    init_db()
    logger.info("Database initialized successfully.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic Document Intelligence & Financial Audit System (DocAudit-Core)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, Any]:
    """Liveness probe returning application health status and version."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post(
    "/api/v1/invoices/process",
    summary="Ingest and audit a business document",
    tags=["Invoices"],
    status_code=status.HTTP_200_OK,
)
async def process_invoice(
    file: UploadFile = File(..., description="Document file (PDF, PNG, JPG, JPEG, TXT)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Ingests a document, stores it in S3, runs OCR via Textract, and audits through LangGraph."""
    # 1. Validate file extension
    filename = file.filename or "uploaded_document"
    dot_idx = filename.rfind(".")
    ext = filename[dot_idx:].lower() if dot_idx != -1 else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 2. Read bytes and generate thread ID
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    thread_id = f"doc_{uuid.uuid4().hex[:12]}"
    aws_svc = AWSDocumentService()

    # 3. Store immutably in S3
    s3_uri = aws_svc.upload_file(file_bytes, filename)

    # 4. OCR / In-Memory Text Extraction (AWS Textract or local pypdf/pdfplumber)
    try:
        ocr_text = aws_svc.extract_text(file_bytes, filename)
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )

    # 5. Persist initial PROCESSING record

    doc_record = DocumentRecord(
        thread_id=thread_id,
        filename=filename,
        s3_uri=s3_uri,
        status=AuditStatus.PROCESSING.value,
        raw_ocr_text=ocr_text,
    )
    db.add(doc_record)
    db.commit()

    # 6. Execute LangGraph Agent
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "filename": filename,
        "s3_uri": s3_uri,
        "raw_ocr_text": ocr_text,
    }

    try:
        # Run graph
        audit_agent.invoke(initial_state, config=config)
    except Exception as e:
        logger.error(f"Error during graph execution for thread {thread_id}: {e}")
        doc_record.status = AuditStatus.FLAGGED.value
        db.commit()
        return {
            "thread_id": thread_id,
            "status": AuditStatus.FLAGGED.value,
            "error": str(e),
            "discrepancies": [],
        }

    # 7. Inspect resulting graph state
    current_state = audit_agent.get_state(config)
    state_values = current_state.values or {}

    # Check if halted at human review interrupt
    is_interrupted = len(current_state.tasks) > 0 and bool(current_state.tasks[0].interrupts)
    current_status = AuditStatus.PENDING_REVIEW.value if is_interrupted else state_values.get("status", AuditStatus.APPROVED.value)

    extracted = state_values.get("extracted_data") or {}
    discrepancies_data = state_values.get("discrepancies", [])

    if is_interrupted:
        doc_record.status = AuditStatus.PENDING_REVIEW.value
        doc_record.vendor_name = extracted.get("vendor_name")
        doc_record.invoice_number = extracted.get("invoice_number")
        doc_record.subtotal = extracted.get("subtotal")
        doc_record.tax_amount = extracted.get("tax_amount")
        doc_record.grand_total = extracted.get("grand_total")
        for d in discrepancies_data:
            rec = DiscrepancyRecord(
                document_id=doc_record.id,
                discrepancy_type=d.get("discrepancy_type", "UNKNOWN"),
                message=d.get("message", ""),
                expected_value=d.get("expected_value"),
                actual_value=d.get("actual_value"),
                field_name=d.get("field_name"),
            )
            db.add(rec)
        db.commit()
        db.refresh(doc_record)
    else:
        db.refresh(doc_record)

    discrepancies = [
        {
            "discrepancy_type": d.discrepancy_type,
            "message": d.message,
            "expected_value": float(d.expected_value) if d.expected_value is not None else None,
            "actual_value": float(d.actual_value) if d.actual_value is not None else None,
            "field_name": d.field_name,
        }
        for d in doc_record.discrepancies
    ]

    return {
        "thread_id": thread_id,
        "status": current_status,
        "filename": filename,
        "s3_uri": s3_uri,
        "vendor_name": doc_record.vendor_name,
        "invoice_number": doc_record.invoice_number,
        "grand_total": float(doc_record.grand_total) if doc_record.grand_total is not None else None,
        "discrepancies": discrepancies,
    }



@app.get(
    "/api/v1/invoices/status/{thread_id}",
    summary="Get document audit status and details by thread ID",
    tags=["Invoices"],
)
def get_invoice_status(thread_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Fetches document metadata, extracted entities, discrepancies, and review state."""
    doc = db.query(DocumentRecord).filter(DocumentRecord.thread_id == thread_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with thread_id '{thread_id}' not found.")

    discrepancies = [
        {
            "id": d.id,
            "discrepancy_type": d.discrepancy_type,
            "message": d.message,
            "expected_value": float(d.expected_value) if d.expected_value is not None else None,
            "actual_value": float(d.actual_value) if d.actual_value is not None else None,
            "field_name": d.field_name,
        }
        for d in doc.discrepancies
    ]

    return {
        "id": doc.id,
        "thread_id": doc.thread_id,
        "filename": doc.filename,
        "s3_uri": doc.s3_uri,
        "status": doc.status,
        "vendor_name": doc.vendor_name,
        "invoice_number": doc.invoice_number,
        "subtotal": float(doc.subtotal) if doc.subtotal is not None else None,
        "tax_amount": float(doc.tax_amount) if doc.tax_amount is not None else None,
        "grand_total": float(doc.grand_total) if doc.grand_total is not None else None,
        "currency": doc.currency,
        "reviewer_decision": doc.reviewer_decision,
        "reviewer_notes": doc.reviewer_notes,
        "discrepancies": discrepancies,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


@app.post(
    "/api/v1/invoices/review/{thread_id}",
    summary="Submit human auditor resolution for an interrupted document",
    tags=["Invoices"],
)
def review_invoice(
    thread_id: str,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Submits auditor decision (APPROVE/REJECT) and resumes LangGraph execution from checkpoint."""
    doc = db.query(DocumentRecord).filter(DocumentRecord.thread_id == thread_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with thread_id '{thread_id}' not found.")

    config = {"configurable": {"thread_id": thread_id}}
    current_state = audit_agent.get_state(config)

    # Resume graph execution if checkpoint exists
    resume_data = {
        "action": payload.action.value,
        "reviewer_notes": payload.reviewer_notes or "",
    }

    if current_state.tasks and any(t.interrupts for t in current_state.tasks):
        audit_agent.invoke(Command(resume=resume_data), config=config)
    else:
        # If checkpointer state was cleared or evicted, apply resolution directly to DB
        doc.status = (
            AuditStatus.APPROVED.value
            if payload.action.value == "APPROVE"
            else AuditStatus.REJECTED.value
        )
        doc.reviewer_decision = payload.action.value
        doc.reviewer_notes = payload.reviewer_notes
        db.commit()

    db.refresh(doc)
    return {
        "thread_id": doc.thread_id,
        "status": doc.status,
        "reviewer_decision": doc.reviewer_decision,
        "reviewer_notes": doc.reviewer_notes,
        "updated_at": doc.updated_at.isoformat(),
    }


@app.get(
    "/api/v1/invoices/metrics",
    summary="Get financial audit KPIs and system metrics",
    tags=["Metrics"],
)
def get_audit_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Aggregates high-signal KPIs across all processed documents."""
    total_docs = db.query(DocumentRecord).count()
    approved_docs = db.query(DocumentRecord).filter(DocumentRecord.status == AuditStatus.APPROVED.value).count()
    pending_docs = db.query(DocumentRecord).filter(DocumentRecord.status == AuditStatus.PENDING_REVIEW.value).count()
    rejected_docs = db.query(DocumentRecord).filter(DocumentRecord.status == AuditStatus.REJECTED.value).count()

    total_value = (
        db.query(func.sum(DocumentRecord.grand_total))
        .filter(DocumentRecord.status == AuditStatus.APPROVED.value)
        .scalar()
        or 0.0
    )

    total_discrepancies = db.query(DiscrepancyRecord).count()

    return {
        "total_documents": total_docs,
        "approved_count": approved_docs,
        "pending_review_count": pending_docs,
        "rejected_count": rejected_docs,
        "total_audited_amount_usd": float(total_value),
        "total_discrepancies_detected": total_discrepancies,
    }


@app.get(
    "/api/v1/invoices/ledger",
    summary="Get paginated historical audit ledger",
    tags=["Invoices"],
)
def get_invoice_ledger(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieves recently audited documents with discrepancy summaries for the frontend ledger."""
    query = db.query(DocumentRecord)
    if status and status.upper() != "ALL":
        query = query.filter(DocumentRecord.status == status.upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (DocumentRecord.invoice_number.ilike(s))
            | (DocumentRecord.vendor_name.ilike(s))
            | (DocumentRecord.filename.ilike(s))
            | (DocumentRecord.thread_id.ilike(s))
        )
    records = query.order_by(DocumentRecord.created_at.desc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "thread_id": r.thread_id,
            "filename": r.filename,
            "status": r.status,
            "vendor_name": r.vendor_name,
            "invoice_number": r.invoice_number,
            "invoice_date": r.invoice_date.isoformat() if r.invoice_date else None,
            "subtotal": float(r.subtotal) if r.subtotal is not None else None,
            "tax_amount": float(r.tax_amount) if r.tax_amount is not None else None,
            "grand_total": float(r.grand_total) if r.grand_total is not None else None,
            "currency": r.currency,
            "reviewer_decision": r.reviewer_decision,
            "reviewer_notes": r.reviewer_notes,
            "discrepancy_count": len(r.discrepancies),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


# Static Dashboard Routes
@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the enterprise dashboard frontend."""
    index_path = os.path.join("web", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "DocAudit-Core API is operational. Visit /docs for OpenAPI specs."}


@app.get("/style.css", include_in_schema=False)
def serve_css():
    """Serves the dashboard stylesheet."""
    css_path = os.path.join("web", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")


@app.get("/app.js", include_in_schema=False)
def serve_js():
    """Serves the dashboard client-side application logic."""
    js_path = os.path.join("web", "app.js")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")


