"""Integration tests for FastAPI REST API endpoints.

Tests file upload, thread status polling, review resolution, and metrics.
"""

from io import BytesIO
import pytest
from fastapi.testclient import TestClient

from app.database.connection import init_db
from app.main import app
from app.schemas.invoice import AuditStatus, ReviewAction


@pytest.fixture(autouse=True)
def setup_api_db():
    """Ensure in-memory SQLite schema is ready before API requests."""
    init_db()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


class TestApiRoutes:
    """Contract test suite for DocAudit-Core REST API."""

    def test_health_check(self, client: TestClient):
        """GET /health should return 200 OK and healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_unsupported_media_type_is_rejected(self, client: TestClient):
        """Uploading unsupported file format (e.g. .exe or .zip) should return 415."""
        fake_executable = BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
        response = client.post(
            "/api/v1/invoices/process",
            files={"file": ("malware.exe", fake_executable, "application/x-msdownload")},
        )
        assert response.status_code == 415
        assert "Unsupported file format" in response.json()["detail"]

    def test_valid_invoice_upload_and_direct_approval(self, client: TestClient):
        """Upload valid text invoice and verify it completes with APPROVED status."""
        valid_invoice_content = """
        VENDOR: CloudScale Solutions LLC
        Invoice #: INV-2026-9001
        Date: 2026-10-15
        Line Items:
        1. Cloud Hosting Setup 1 $1,000.00 $1,000.00
        SUBTOTAL: $1,000.00
        TAX: $100.00
        TOTAL DUE: $1,100.00
        """.encode("utf-8")

        response = client.post(
            "/api/v1/invoices/process",
            files={"file": ("valid_invoice.txt", BytesIO(valid_invoice_content), "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert data["status"] == AuditStatus.APPROVED.value
        assert len(data["discrepancies"]) == 0

        # Verify inspection endpoint
        thread_id = data["thread_id"]
        status_res = client.get(f"/api/v1/invoices/status/{thread_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["thread_id"] == thread_id
        assert status_data["status"] == AuditStatus.APPROVED.value

    def test_discrepant_invoice_upload_and_human_review_resume(self, client: TestClient):
        """Upload invoice with math errors, verify PENDING_REVIEW, and resolve via /review."""
        faulty_invoice_content = """
        VENDOR: Rogue Supplies Ltd
        Invoice #: INV-FAULTY-888
        Date: 2026-10-10
        Line Items:
        1. Broken Hardware 1 $100.00 $100.00
        SUBTOTAL: $500.00
        TAX: $0.00
        TOTAL DUE: $500.00
        """.encode("utf-8")

        # Step 1: Upload discrepant document
        response = client.post(
            "/api/v1/invoices/process",
            files={"file": ("faulty_invoice.txt", BytesIO(faulty_invoice_content), "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        thread_id = data["thread_id"]
        assert data["status"] == AuditStatus.PENDING_REVIEW.value
        assert len(data["discrepancies"]) > 0

        # Step 2: Poll status endpoint and check pending state
        status_res = client.get(f"/api/v1/invoices/status/{thread_id}")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == AuditStatus.PENDING_REVIEW.value

        # Step 3: Human auditor approves with override
        review_payload = {
            "action": ReviewAction.APPROVE.value,
            "reviewer_notes": "Auditor approved difference after reviewing vendor adjustment credit.",
        }
        review_res = client.post(f"/api/v1/invoices/review/{thread_id}", json=review_payload)
        assert review_res.status_code == 200
        resolved_data = review_res.json()
        assert resolved_data["status"] == AuditStatus.APPROVED.value
        assert resolved_data["reviewer_decision"] == ReviewAction.APPROVE.value

    def test_review_non_existent_thread_returns_404(self, client: TestClient):
        """POST /review on non-existent thread_id should return 404."""
        response = client.post(
            "/api/v1/invoices/review/non-existent-thread-12345",
            json={"action": "APPROVE", "reviewer_notes": "N/A"},
        )
        assert response.status_code == 404

    def test_audit_metrics_endpoint(self, client: TestClient):
        """GET /api/v1/invoices/metrics should return aggregate statistics."""
        response = client.get("/api/v1/invoices/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert "total_documents" in metrics
        assert "approved_count" in metrics
        assert "pending_review_count" in metrics
        assert "rejected_count" in metrics

    def test_upload_real_pdf_file_extracts_actual_entities(self, client: TestClient):
        """Uploads dummy_invoice.pdf and verifies real text is extracted rather than binary placeholder."""
        import os

        pdf_path = "dummy_invoice.pdf"
        assert os.path.exists(pdf_path), "dummy_invoice.pdf must exist for this test"

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        response = client.post(
            "/api/v1/invoices/process",
            files={"file": ("dummy_invoice.pdf", BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()

        # Must not contain the old dummy placeholder
        assert "[Binary file" not in str(data.get("vendor_name"))
        assert data.get("invoice_number") != "INV-DEFAULT-001"

        # Verify actual extracted business fields
        assert "TechSupply" in data["vendor_name"]
        assert data["invoice_number"] == "INV-2026-0891"
        assert data["grand_total"] == 76700.0

    def test_audit_ledger_endpoint(self, client: TestClient):
        """GET /api/v1/invoices/ledger should return historical audit records with filters."""
        response = client.get("/api/v1/invoices/ledger")
        assert response.status_code == 200
        records = response.json()
        assert isinstance(records, list)

        # Test search filter
        search_res = client.get("/api/v1/invoices/ledger?search=TechSupply")
        assert search_res.status_code == 200
        assert isinstance(search_res.json(), list)

    def test_serve_frontend_index(self, client: TestClient):
        """GET / should return 200 or healthy JSON response."""
        response = client.get("/")
        assert response.status_code == 200


