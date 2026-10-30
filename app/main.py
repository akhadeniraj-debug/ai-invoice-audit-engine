"""FastAPI application factory, dependency injection, and REST API routes for DocAudit-Core and Sai Arts."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from langgraph.types import Command
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agent.graph import audit_agent
from app.config import settings
from app.database.connection import get_db, init_db
from app.database.models import ApiKeyRecord, DiscrepancyRecord, DocumentRecord
from app.schemas.auth import ApiKeyCreateRequest, ApiKeyIssueResponse, ApiKeyItemResponse
from app.schemas.invoice import AuditStatus, ReviewRequest
from app.schemas.pricing import PricingCalculationRequest, PricingCalculationResponse
from app.services.aws_service import AWSDocumentService
from app.services.pricing_engine import PricingEngine
from app.services.rate_limiter import rate_limiter
from app.services.security import (
    generate_raw_api_key,
    get_key_prefix,
    hash_api_key,
    verify_api_key_and_rate_limit,
)

logger = logging.getLogger(__name__)

# Base project directory for reliable static file serving
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Allowed invoice file extensions
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    # Ensure relational tables exist on startup
    init_db()
    logger.info("Database initialized successfully.")
    yield
    # Cleanup rate limiter Redis resources on shutdown
    await rate_limiter.close()
    logger.info("Rate limiter resources closed.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic Document Intelligence, Financial Audit & Sai Arts Signage Engine",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Window-Seconds", "Retry-After"],
)


# ============================================================================
# 1. HEALTH PROBE
# ============================================================================
@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, Any]:
    """Liveness probe returning application health status and version."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.1.0",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# 2. API KEY MANAGEMENT & ISSUANCE ENDPOINTS
# ============================================================================
@app.post(
    "/api/v1/auth/keys",
    response_model=ApiKeyIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a new API key with sliding window rate limiting tier",
    tags=["Authentication"],
)
def issue_api_key(
    payload: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
) -> ApiKeyIssueResponse:
    """Generates a raw key (sai_live_<32_urlsafe_bytes>), stores its SHA-256 hash, and returns the raw key once."""
    raw_key = generate_raw_api_key()
    prefix = get_key_prefix(raw_key)
    hashed = hash_api_key(raw_key)

    record = ApiKeyRecord(
        client_name=payload.client_name.strip(),
        key_prefix=prefix,
        hashed_key=hashed,
        is_active=True,
        rate_limit_rpm=payload.rate_limit_rpm,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(f"Issued API key {prefix}... for client '{record.client_name}' (Limit: {record.rate_limit_rpm} rpm)")

    return ApiKeyIssueResponse(
        id=record.id,
        client_name=record.client_name,
        key_prefix=record.key_prefix,
        raw_key=raw_key,
        is_active=record.is_active,
        rate_limit_rpm=record.rate_limit_rpm,
        created_at=record.created_at,
    )


@app.get(
    "/api/v1/auth/keys",
    response_model=List[ApiKeyItemResponse],
    summary="List all registered API keys and metadata",
    tags=["Authentication"],
)
def list_api_keys(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[ApiKeyItemResponse]:
    """Returns key prefixes and metadata. Never exposes raw keys or cryptographic hashes."""
    records = db.query(ApiKeyRecord).order_by(ApiKeyRecord.created_at.desc()).limit(limit).all()
    return [
        ApiKeyItemResponse(
            id=r.id,
            client_name=r.client_name,
            key_prefix=r.key_prefix,
            is_active=r.is_active,
            rate_limit_rpm=r.rate_limit_rpm,
            created_at=r.created_at,
            last_used_at=r.last_used_at,
        )
        for r in records
    ]


@app.patch(
    "/api/v1/auth/keys/{key_id}/revoke",
    response_model=ApiKeyItemResponse,
    summary="Revoke an active API key",
    tags=["Authentication"],
)
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
) -> ApiKeyItemResponse:
    """Revokes an API key so that subsequent requests with it will receive HTTP 403 Forbidden."""
    record = db.query(ApiKeyRecord).filter(ApiKeyRecord.id == key_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"API key with ID {key_id} not found.")

    record.is_active = False
    db.commit()
    db.refresh(record)
    logger.info(f"Revoked API key {record.key_prefix} (ID: {key_id})")

    return ApiKeyItemResponse(
        id=record.id,
        client_name=record.client_name,
        key_prefix=record.key_prefix,
        is_active=record.is_active,
        rate_limit_rpm=record.rate_limit_rpm,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
    )


# ============================================================================
# 3. PROTECTED PRICING & QUOTATION ESTIMATION ROUTES
# ============================================================================
@app.post(
    "/api/v1/pricing/calculate",
    response_model=PricingCalculationResponse,
    summary="Calculate dynamic signage and facade fabrication pricing",
    tags=["Pricing & Quotations"],
)
async def calculate_signage_pricing(
    payload: PricingCalculationRequest,
    api_key: ApiKeyRecord = Depends(verify_api_key_and_rate_limit),
) -> PricingCalculationResponse:
    """Protected by X-API-Key and Redis sliding window rate limiter. Computes itemized pricing and GST parity."""
    return PricingEngine.calculate(payload, client_name=api_key.client_name)


@app.post(
    "/api/v1/quotes/estimate",
    summary="Generate a formal itemized quotation with quote serial reference",
    tags=["Pricing & Quotations"],
)
async def generate_quote_estimate(
    payload: PricingCalculationRequest,
    api_key: ApiKeyRecord = Depends(verify_api_key_and_rate_limit),
) -> Dict[str, Any]:
    """Protected endpoint generating a formal company quotation estimate with warranty certificates."""
    calc = PricingEngine.calculate(payload, client_name=api_key.client_name)
    serial_no = f"EST-2026-{uuid.uuid4().hex[:6].upper()}"

    return {
        "estimate_reference": serial_no,
        "date": datetime.now(timezone.utc).strftime("%d %b %Y"),
        "enterprise": "Sai Arts Industrial Manufacturing",
        "client_name": api_key.client_name,
        "calculation": calc.model_dump(),
        "warranty": {
            "sheet": "5-Year UV Anti-Yellowing Guarantee",
            "illumination": "2-Year Samsung Direct Replacement",
            "smps": "2-Year Rainproof Industrial SMPS Warranty",
        },
    }


# ============================================================================
# 4. INVOICE INGESTION & DOCUMENT AUDIT ROUTES
# ============================================================================
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
    """Ingests a document, stores it in S3, runs OCR via Textract/local fallback, and audits through LangGraph."""
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

    # 7. Inspect resulting graph state safely
    current_state = audit_agent.get_state(config)
    state_values = current_state.values or {}

    # Check if halted at human review interrupt
    tasks = current_state.tasks or ()
    is_interrupted = bool(tasks and any(getattr(t, "interrupts", None) for t in tasks))
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
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
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

    if current_state.tasks and any(getattr(t, "interrupts", None) for t in current_state.tasks):
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
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
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


# ============================================================================
# 5. STATIC ENTERPRISE DASHBOARD & WEB ROUTES
# ============================================================================
def _find_web_file(filename: str) -> Optional[str]:
    """Finds static dashboard assets with fallback to project root or current directory."""
    candidates = [
        os.path.join(BASE_DIR, "web", filename),
        os.path.join("web", filename),
        os.path.join(BASE_DIR, "signage-enterprise", filename),
        os.path.join("signage-enterprise", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the enterprise dashboard frontend."""
    path = _find_web_file("index.html")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "Sai Arts & DocAudit-Core API is operational. Visit /docs for OpenAPI specs."}


@app.get("/style.css", include_in_schema=False)
def serve_css():
    """Serves the dashboard stylesheet."""
    path = _find_web_file("style.css")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")


@app.get("/app.js", include_in_schema=False)
def serve_js():
    """Serves the dashboard client-side application logic."""
    path = _find_web_file("app.js")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")
