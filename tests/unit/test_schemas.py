"""Unit tests for Pydantic v2 schemas and validation models.

Verifies strict typing, decimal conversions, required fields, and enum validation.
"""

from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.schemas.invoice import (
    InvoiceData,
    LineItem,
    ReviewAction,
    ReviewRequest,
)


class TestInvoiceSchemas:
    """Test suite for InvoiceData and LineItem schemas."""

    def test_valid_invoice_dict_deserialization(self, sample_valid_invoice_dict):
        """Should parse valid dict into InvoiceData with correct types."""
        invoice = InvoiceData(**sample_valid_invoice_dict)
        assert invoice.vendor_name == "Apex Cloud Technologies"
        assert invoice.invoice_number == "INV-2026-1049"
        assert isinstance(invoice.invoice_date, date)
        assert isinstance(invoice.subtotal, Decimal)
        assert invoice.subtotal == Decimal("250.50")
        assert len(invoice.line_items) == 2
        assert invoice.line_items[0].quantity == Decimal("2")

    def test_missing_required_fields_raises_validation_error(self):
        """Missing vendor_name or grand_total must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceData(
                invoice_number="INV-MISSING",
                invoice_date=date.today(),
                # missing vendor_name, line_items, subtotal, grand_total
            )
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "vendor_name" in field_names
        assert "grand_total" in field_names

    def test_string_to_decimal_coercion_and_stripping(self):
        """Dollar signs and currency strings must cleanly coerce to Decimal."""
        item = LineItem(
            description="Cloud Database",
            quantity="5",
            unit_price="$25.50",
            total_price="$127.50",
        )
        assert item.quantity == Decimal("5")
        assert item.unit_price == Decimal("25.50")
        assert item.total_price == Decimal("127.50")

    def test_review_request_valid_action(self):
        """ReviewRequest should accept APPROVE and REJECT actions."""
        req_approve = ReviewRequest(action=ReviewAction.APPROVE, reviewer_notes="Looks good.")
        assert req_approve.action == ReviewAction.APPROVE
        assert req_approve.reviewer_notes == "Looks good."

        req_reject = ReviewRequest(action="REJECT", reviewer_notes="Total mismatch confirmed.")
        assert req_reject.action == ReviewAction.REJECT

    def test_review_request_invalid_action_rejected(self):
        """Invalid review action should be rejected by Pydantic."""
        with pytest.raises(ValidationError):
            ReviewRequest(action="UNKNOWN_ACTION")
