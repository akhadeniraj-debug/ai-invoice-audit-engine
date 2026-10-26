"""Shared pytest fixtures, mock clients, and database sessions for DocAudit-Core."""

import os
from datetime import date, timedelta
from decimal import Decimal
from typing import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test environment flags
os.environ["DOCAUDIT_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_S3_BUCKET_NAME"] = "test-docaudit-bucket"


@pytest.fixture
def today_date() -> date:
    """Returns today's date for relative date boundary assertions."""
    return date.today()


@pytest.fixture
def sample_valid_invoice_dict(today_date: date) -> dict:
    """Valid invoice payload with exact arithmetic and fresh date."""
    invoice_date_str = (today_date - timedelta(days=10)).isoformat()
    due_date_str = (today_date + timedelta(days=20)).isoformat()
    return {
        "vendor_name": "Apex Cloud Technologies",
        "invoice_number": "INV-2026-1049",
        "invoice_date": invoice_date_str,
        "due_date": due_date_str,
        "line_items": [
            {
                "description": "Enterprise Cloud Hosting",
                "quantity": 2,
                "unit_price": 100.00,
                "total_price": 200.00,
            },
            {
                "description": "Database Read Replicas",
                "quantity": 1,
                "unit_price": 50.50,
                "total_price": 50.50,
            },
        ],
        "subtotal": 250.50,
        "tax_amount": 25.05,
        "grand_total": 275.55,
        "currency": "USD",
    }


@pytest.fixture
def sample_math_mismatch_invoice_dict(today_date: date) -> dict:
    """Invoice where line items sum != subtotal and subtotal + tax != grand_total."""
    invoice_date_str = (today_date - timedelta(days=5)).isoformat()
    return {
        "vendor_name": "Faulty Ledger Corp",
        "invoice_number": "INV-ERR-001",
        "invoice_date": invoice_date_str,
        "line_items": [
            {
                "description": "Item A",
                "quantity": 1,
                "unit_price": 100.00,
                "total_price": 100.00,
            },
            {
                "description": "Item B",
                "quantity": 2,
                "unit_price": 50.00,
                "total_price": 100.00,
            },
        ],
        "subtotal": 350.00,  # Expected 200.00 (mismatch: +150.00)
        "tax_amount": 20.00,
        "grand_total": 500.00,  # Expected 370.00 (mismatch: +130.00)
        "currency": "USD",
    }


@pytest.fixture
def sample_future_date_invoice_dict(today_date: date) -> dict:
    """Invoice dated in the future (> today)."""
    future_date = (today_date + timedelta(days=15)).isoformat()
    return {
        "vendor_name": "Time Traveler Inc",
        "invoice_number": "INV-FUT-999",
        "invoice_date": future_date,
        "line_items": [
            {
                "description": "Consulting Future",
                "quantity": 1,
                "unit_price": 100.00,
                "total_price": 100.00,
            }
        ],
        "subtotal": 100.00,
        "tax_amount": 10.00,
        "grand_total": 110.00,
        "currency": "USD",
    }


@pytest.fixture
def sample_expired_date_invoice_dict(today_date: date) -> dict:
    """Invoice older than 180 days."""
    old_date = (today_date - timedelta(days=200)).isoformat()
    return {
        "vendor_name": "Ancient Archives LLC",
        "invoice_number": "INV-OLD-001",
        "invoice_date": old_date,
        "line_items": [
            {
                "description": "Legacy Archives",
                "quantity": 1,
                "unit_price": 100.00,
                "total_price": 100.00,
            }
        ],
        "subtotal": 100.00,
        "tax_amount": 10.00,
        "grand_total": 110.00,
        "currency": "USD",
    }


@pytest.fixture
def sample_negative_item_invoice_dict(today_date: date) -> dict:
    """Invoice with non-positive line item quantity or negative unit price."""
    invoice_date_str = (today_date - timedelta(days=2)).isoformat()
    return {
        "vendor_name": "Negative Inventory Co",
        "invoice_number": "INV-NEG-001",
        "invoice_date": invoice_date_str,
        "line_items": [
            {
                "description": "Corrupted Item",
                "quantity": -2,
                "unit_price": -50.00,
                "total_price": 100.00,
            }
        ],
        "subtotal": 100.00,
        "tax_amount": 10.00,
        "grand_total": 110.00,
        "currency": "USD",
    }


@pytest.fixture
def mock_s3_service() -> MagicMock:
    """Mock AWS S3 service for uploads and presigned URLs."""
    s3_mock = MagicMock()
    s3_mock.upload_file.return_value = "s3://test-docaudit-bucket/uploads/sample.pdf"
    s3_mock.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/sample.pdf?token=xyz"
    return s3_mock


@pytest.fixture
def mock_textract_service() -> MagicMock:
    """Mock AWS Textract service returning raw OCR key-value blocks."""
    textract_mock = MagicMock()
    textract_mock.extract_document_text.return_value = """
    Apex Cloud Technologies
    Invoice #: INV-2026-1049
    Date: 2026-10-15
    Due Date: 2026-11-04
    Line Items:
    - Enterprise Cloud Hosting: 2 x $100.00 = $200.00
    - Database Read Replicas: 1 x $50.50 = $50.50
    Subtotal: $250.50
    Tax (10%): $25.05
    Grand Total: $275.55
    """
    return textract_mock
