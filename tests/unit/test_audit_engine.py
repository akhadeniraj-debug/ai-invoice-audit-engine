"""Unit tests for the Deterministic Financial Audit Engine.

These tests enforce zero-hallucination math, date boundary validation,
and line-item integrity using exact Decimal arithmetic.
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.schemas.invoice import InvoiceData, LineItem
from app.services.audit_engine import (
    AuditDiscrepancy,
    AuditEngine,
    DiscrepancyType,
)


class TestDeterministicAuditEngine:
    """Test suite for validating business and financial rules."""

    def test_valid_invoice_produces_zero_discrepancies(self, sample_valid_invoice_dict):
        """A perfectly balanced invoice must return an empty list of discrepancies."""
        invoice = InvoiceData(**sample_valid_invoice_dict)
        discrepancies = AuditEngine.audit(invoice)
        assert len(discrepancies) == 0, f"Expected 0 discrepancies, got: {discrepancies}"

    def test_subtotal_mismatch_is_flagged(self, sample_math_mismatch_invoice_dict):
        """Sum of line items not matching subtotal must be caught and reported."""
        invoice = InvoiceData(**sample_math_mismatch_invoice_dict)
        discrepancies = AuditEngine.audit(invoice)

        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.SUBTOTAL_MISMATCH in types

        # Validate discrepancy message details
        subtotal_disc = next(d for d in discrepancies if d.discrepancy_type == DiscrepancyType.SUBTOTAL_MISMATCH)
        assert "Sum of line items" in subtotal_disc.message
        assert subtotal_disc.expected_value == Decimal("200.00")
        assert subtotal_disc.actual_value == Decimal("350.00")

    def test_grand_total_mismatch_is_flagged(self, sample_math_mismatch_invoice_dict):
        """Subtotal + tax not matching grand_total must be caught."""
        invoice = InvoiceData(**sample_math_mismatch_invoice_dict)
        discrepancies = AuditEngine.audit(invoice)

        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.GRAND_TOTAL_MISMATCH in types

        grand_total_disc = next(d for d in discrepancies if d.discrepancy_type == DiscrepancyType.GRAND_TOTAL_MISMATCH)
        assert grand_total_disc.expected_value == Decimal("370.00")
        assert grand_total_disc.actual_value == Decimal("500.00")

    def test_line_item_math_mismatch_is_flagged(self, today_date):
        """If quantity * unit_price != total_price on a line item, it must be flagged."""
        invoice = InvoiceData(
            vendor_name="Glitchy Goods",
            invoice_number="INV-LINE-ERR",
            invoice_date=today_date,
            line_items=[
                LineItem(
                    description="Bad Item",
                    quantity=Decimal("3"),
                    unit_price=Decimal("10.00"),
                    total_price=Decimal("40.00"),  # Expected 30.00
                )
            ],
            subtotal=Decimal("40.00"),
            tax_amount=Decimal("0.00"),
            grand_total=Decimal("40.00"),
        )
        discrepancies = AuditEngine.audit(invoice)
        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.LINE_ITEM_CALCULATION_MISMATCH in types

    def test_future_date_is_flagged(self, sample_future_date_invoice_dict):
        """Invoices with invoice_date in the future must be flagged."""
        invoice = InvoiceData(**sample_future_date_invoice_dict)
        discrepancies = AuditEngine.audit(invoice)

        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.FUTURE_DATE in types

    def test_stale_invoice_older_than_180_days_is_flagged(self, sample_expired_date_invoice_dict):
        """Invoices older than 180 days must be flagged as stale."""
        invoice = InvoiceData(**sample_expired_date_invoice_dict)
        discrepancies = AuditEngine.audit(invoice)

        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.STALE_DATE in types

    def test_negative_or_zero_quantity_is_flagged(self, today_date):
        """Zero or negative line item quantities must be flagged."""
        invoice = InvoiceData(
            vendor_name="Zero Qty Supplies",
            invoice_number="INV-ZERO-QTY",
            invoice_date=today_date,
            line_items=[
                LineItem(
                    description="Ghost Product",
                    quantity=Decimal("0"),
                    unit_price=Decimal("10.00"),
                    total_price=Decimal("0.00"),
                )
            ],
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            grand_total=Decimal("0.00"),
        )
        discrepancies = AuditEngine.audit(invoice)
        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.INVALID_QUANTITY in types

    def test_negative_unit_price_is_flagged(self, today_date):
        """Negative unit prices must be flagged."""
        invoice = InvoiceData(
            vendor_name="Credit Vendor",
            invoice_number="INV-NEG-PRICE",
            invoice_date=today_date,
            line_items=[
                LineItem(
                    description="Negative Price Item",
                    quantity=Decimal("1"),
                    unit_price=Decimal("-15.00"),
                    total_price=Decimal("-15.00"),
                )
            ],
            subtotal=Decimal("-15.00"),
            tax_amount=Decimal("0.00"),
            grand_total=Decimal("-15.00"),
        )
        discrepancies = AuditEngine.audit(invoice)
        types = [d.discrepancy_type for d in discrepancies]
        assert DiscrepancyType.NEGATIVE_PRICE in types

    def test_floating_point_precision_guard(self, today_date):
        """Ensures that 0.10 + 0.20 == 0.30 does not trigger false positive mismatches."""
        invoice = InvoiceData(
            vendor_name="Decimal Precision LLC",
            invoice_number="INV-DECIMAL-01",
            invoice_date=today_date,
            line_items=[
                LineItem(
                    description="Item 1",
                    quantity=Decimal("1"),
                    unit_price=Decimal("0.10"),
                    total_price=Decimal("0.10"),
                ),
                LineItem(
                    description="Item 2",
                    quantity=Decimal("1"),
                    unit_price=Decimal("0.20"),
                    total_price=Decimal("0.20"),
                ),
            ],
            subtotal=Decimal("0.30"),
            tax_amount=Decimal("0.00"),
            grand_total=Decimal("0.30"),
        )
        discrepancies = AuditEngine.audit(invoice)
        assert len(discrepancies) == 0, f"Precision error detected: {discrepancies}"
