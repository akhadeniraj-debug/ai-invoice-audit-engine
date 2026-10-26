"""SQLAlchemy relational models for document audit tracking and discrepancies."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Date,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def get_utc_now():
    """Returns current UTC datetime."""
    return datetime.now(timezone.utc)


class DocumentRecord(Base):
    """Relational table tracking an ingested document, its extracted metadata, and review state."""

    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    s3_uri = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, default="PROCESSING", index=True)

    # Extracted Header Entities
    vendor_name = Column(String(255), nullable=True)
    invoice_number = Column(String(128), nullable=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    # Financial Totals
    subtotal = Column(Numeric(14, 2), nullable=True)
    tax_amount = Column(Numeric(14, 2), nullable=True)
    grand_total = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(8), default="USD")

    # Raw Artifacts & Review Log
    raw_ocr_text = Column(Text, nullable=True)
    reviewer_decision = Column(String(32), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationship to DiscrepancyRecord
    discrepancies = relationship(
        "DiscrepancyRecord",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DiscrepancyRecord.id",
    )


class DiscrepancyRecord(Base):
    """Relational table storing individual audit rule violations for a document."""

    __tablename__ = "discrepancy_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)

    discrepancy_type = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    expected_value = Column(Numeric(14, 2), nullable=True)
    actual_value = Column(Numeric(14, 2), nullable=True)
    field_name = Column(String(128), nullable=True)

    created_at = Column(DateTime, default=get_utc_now, nullable=False)


    document = relationship("DocumentRecord", back_populates="discrepancies")
