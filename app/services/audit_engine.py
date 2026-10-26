"""Deterministic Financial Audit Engine.

Enforces zero-hallucination arithmetic, date compliance, and line-item integrity
using pure Python Decimal precision.
"""

from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.invoice import InvoiceData


class DiscrepancyType(str, Enum):
    """Enumeration of possible deterministic audit rule violations."""

    SUBTOTAL_MISMATCH = "SUBTOTAL_MISMATCH"
    GRAND_TOTAL_MISMATCH = "GRAND_TOTAL_MISMATCH"
    LINE_ITEM_CALCULATION_MISMATCH = "LINE_ITEM_CALCULATION_MISMATCH"
    FUTURE_DATE = "FUTURE_DATE"
    STALE_DATE = "STALE_DATE"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    NEGATIVE_PRICE = "NEGATIVE_PRICE"


class AuditDiscrepancy(BaseModel):
    """Detailed record of a single rule discrepancy found during auditing."""

    discrepancy_type: DiscrepancyType
    message: str
    expected_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    field_name: Optional[str] = None


class AuditEngine:
    """Zero-hallucination deterministic audit engine for financial documents."""

    MAX_INVOICE_AGE_DAYS = 180

    @classmethod
    def audit(
        cls,
        invoice: InvoiceData,
        reference_date: Optional[date] = None,
    ) -> List[AuditDiscrepancy]:
        """Audits an invoice against accounting rules, returning any discrepancies found.

        Args:
            invoice: Strongly-typed InvoiceData model.
            reference_date: Baseline date for temporal checks (defaults to date.today()).

        Returns:
            List of AuditDiscrepancy instances (empty if fully compliant).
        """
        discrepancies: List[AuditDiscrepancy] = []
        today = reference_date or date.today()

        # 1. Line Item Integrity & Calculations
        computed_subtotal = Decimal("0.00")
        for idx, item in enumerate(invoice.line_items):
            # Check for non-positive quantities
            if item.quantity <= Decimal("0"):
                discrepancies.append(
                    AuditDiscrepancy(
                        discrepancy_type=DiscrepancyType.INVALID_QUANTITY,
                        message=f"Line item #{idx + 1} ('{item.description}') has non-positive quantity: {item.quantity}",
                        expected_value=Decimal("1.00"),
                        actual_value=item.quantity,
                        field_name=f"line_items[{idx}].quantity",
                    )
                )

            # Check for negative unit prices
            if item.unit_price < Decimal("0"):
                discrepancies.append(
                    AuditDiscrepancy(
                        discrepancy_type=DiscrepancyType.NEGATIVE_PRICE,
                        message=f"Line item #{idx + 1} ('{item.description}') has negative unit price: {item.unit_price}",
                        expected_value=Decimal("0.00"),
                        actual_value=item.unit_price,
                        field_name=f"line_items[{idx}].unit_price",
                    )
                )

            # Check quantity * unit_price == total_price
            expected_line_total = item.quantity * item.unit_price
            if item.total_price != expected_line_total:
                discrepancies.append(
                    AuditDiscrepancy(
                        discrepancy_type=DiscrepancyType.LINE_ITEM_CALCULATION_MISMATCH,
                        message=(
                            f"Line item #{idx + 1} total mismatch: {item.quantity} * {item.unit_price} = "
                            f"{expected_line_total}, but declared total is {item.total_price}"
                        ),
                        expected_value=expected_line_total,
                        actual_value=item.total_price,
                        field_name=f"line_items[{idx}].total_price",
                    )
                )

            computed_subtotal += item.total_price

        # 2. Subtotal Check: Sum of line items == declared subtotal
        if invoice.line_items and computed_subtotal != invoice.subtotal:
            discrepancies.append(
                AuditDiscrepancy(
                    discrepancy_type=DiscrepancyType.SUBTOTAL_MISMATCH,
                    message=(
                        f"Sum of line items ({computed_subtotal}) does not match declared subtotal ({invoice.subtotal})"
                    ),
                    expected_value=computed_subtotal,
                    actual_value=invoice.subtotal,
                    field_name="subtotal",
                )
            )

        # 3. Grand Total Check: Subtotal + Tax == Grand Total
        expected_grand_total = invoice.subtotal + invoice.tax_amount
        if expected_grand_total != invoice.grand_total:
            discrepancies.append(
                AuditDiscrepancy(
                    discrepancy_type=DiscrepancyType.GRAND_TOTAL_MISMATCH,
                    message=(
                        f"Subtotal ({invoice.subtotal}) + Tax ({invoice.tax_amount}) = {expected_grand_total}, "
                        f"which does not match declared grand total ({invoice.grand_total})"
                    ),
                    expected_value=expected_grand_total,
                    actual_value=invoice.grand_total,
                    field_name="grand_total",
                )
            )

        # 4. Date Boundary Compliance
        if invoice.invoice_date > today:
            discrepancies.append(
                AuditDiscrepancy(
                    discrepancy_type=DiscrepancyType.FUTURE_DATE,
                    message=f"Invoice date ({invoice.invoice_date}) is in the future relative to {today}",
                    field_name="invoice_date",
                )
            )
        elif invoice.invoice_date < (today - timedelta(days=cls.MAX_INVOICE_AGE_DAYS)):
            discrepancies.append(
                AuditDiscrepancy(
                    discrepancy_type=DiscrepancyType.STALE_DATE,
                    message=(
                        f"Invoice date ({invoice.invoice_date}) is older than {cls.MAX_INVOICE_AGE_DAYS} days "
                        f"relative to {today}"
                    ),
                    field_name="invoice_date",
                )
            )

        return discrepancies
