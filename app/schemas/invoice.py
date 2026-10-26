"""Pydantic v2 schemas for Invoice entities, line items, and human review actions."""

from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from typing import Annotated, Any, List, Optional
from pydantic import BaseModel, Field, BeforeValidator


def coerce_to_decimal(v: Any) -> Decimal:
    """Coerces strings (including currency symbols, commas) or numeric types to Decimal."""
    if isinstance(v, Decimal):
        return v
    if v is None:
        return Decimal("0.00")
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    if isinstance(v, str):
        # Strip currency symbols, commas, and whitespace: e.g. "$ 1,250.50" -> "1250.50"
        cleaned = re.sub(r"[^\d.-]", "", v.strip())
        if not cleaned:
            return Decimal("0.00")
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            raise ValueError(f"Cannot coerce '{v}' to Decimal")
    raise ValueError(f"Unsupported type for Decimal coercion: {type(v)}")


CurrencyDecimal = Annotated[Decimal, BeforeValidator(coerce_to_decimal)]



class LineItem(BaseModel):
    """Represents an individual line item within an invoice."""

    description: str = Field(..., description="Description of the goods or services rendered")
    quantity: CurrencyDecimal = Field(..., description="Quantity of the line item")
    unit_price: CurrencyDecimal = Field(..., description="Unit price per item")
    total_price: CurrencyDecimal = Field(..., description="Extended total price for this line item")


class InvoiceData(BaseModel):
    """Strongly typed structured invoice payload extracted from OCR/LLM."""

    vendor_name: str = Field(..., description="Name of the billing vendor or supplier")
    invoice_number: str = Field(..., description="Unique invoice identification number")
    invoice_date: date = Field(..., description="Date on which the invoice was issued")
    due_date: Optional[date] = Field(None, description="Payment due date if specified")
    line_items: List[LineItem] = Field(default_factory=list, description="List of itemized goods/services")
    subtotal: CurrencyDecimal = Field(..., description="Subtotal amount before tax")
    tax_amount: CurrencyDecimal = Field(default=Decimal("0.00"), description="Total tax amount")
    grand_total: CurrencyDecimal = Field(..., description="Final invoice total payable")
    currency: str = Field(default="USD", description="Currency code (e.g. USD, EUR, GBP)")


class ReviewAction(str, Enum):
    """Permitted decisions for an auditor reviewing a flagged invoice."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ReviewRequest(BaseModel):
    """Payload for human auditor resolving an interrupted audit state."""

    action: ReviewAction = Field(..., description="Auditor resolution action (APPROVE or REJECT)")
    reviewer_notes: Optional[str] = Field(None, description="Audit justification or resolution commentary")


class AuditStatus(str, Enum):
    """Lifecycle status states of an audited document record."""

    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
