"""AWS S3 Storage and AWS Textract OCR extraction services.

Provides cloud integration with robust in-memory local fallbacks (pypdf, pdfplumber)
and intelligent LLM structured extraction (Groq, Gemini, OpenAI).
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import io
import json
import logging
import os
import re
from typing import Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.schemas.invoice import InvoiceData, LineItem

logger = logging.getLogger(__name__)


class AWSDocumentService:
    """Handles S3 object persistence, OCR text extraction, and structured invoice parsing."""

    def __init__(self):
        self.region = settings.AWS_REGION
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

        self._s3_client = None
        self._textract_client = None

        # Only initialize boto3 clients if non-placeholder credentials are provided
        aws_key = settings.AWS_ACCESS_KEY_ID or ""
        aws_secret = settings.AWS_SECRET_ACCESS_KEY or ""
        if aws_key and aws_secret and not aws_key.lower().startswith("placeholder"):
            try:
                self._s3_client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                )
                self._textract_client = boto3.client(
                    "textract",
                    region_name=self.region,
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                )
            except Exception as e:
                logger.warning(f"Could not initialize live AWS clients: {e}")

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        """Uploads document bytes to S3, returning the canonical S3 URI.

        Falls back to a simulated S3 URI if AWS credentials are not configured.
        """
        s3_key = f"documents/{datetime.now(timezone.utc).strftime('%Y%m%d')}_{filename}"
        s3_uri = f"s3://{self.bucket_name}/{s3_key}"

        if self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_bytes,
                )
                logger.info(f"Successfully uploaded {filename} to {s3_uri}")
                return s3_uri
            except (BotoCoreError, ClientError) as e:
                logger.error(f"Failed to upload to S3: {e}. Falling back to simulated URI.")

        return s3_uri

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extracts text from document bytes using AWS Textract or in-memory local fallbacks.

        Local fallback checks both filename extension and binary magic bytes:
        - Uses pypdf to extract raw text across all pages in memory.
        - Falls back to pdfplumber for complex table and text layouts.
        - Decodes UTF-8 for plain text files.
        Never returns a dummy placeholder string.
        """
        # 1. Attempt AWS Textract if active credentials exist
        if self._textract_client:
            try:
                response = self._textract_client.detect_document_text(
                    Document={"Bytes": file_bytes}
                )
                extracted_lines = [
                    item["Text"]
                    for item in response.get("Blocks", [])
                    if item.get("BlockType") == "LINE"
                ]
                if extracted_lines:
                    logger.info(f"AWS Textract successfully extracted {len(extracted_lines)} lines.")
                    return "\n".join(extracted_lines)
            except (BotoCoreError, ClientError) as e:
                logger.warning(f"AWS Textract call failed ({e}). Proceeding to local in-memory fallback.")

        # 2. Local fallback for PDF files (check extension or %PDF magic header)
        is_pdf = filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF")
        if is_pdf:
            # Try pypdf first
            try:
                import pypdf

                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_pages = [page.extract_text() or "" for page in reader.pages]
                combined = "\n".join(text_pages).strip()
                if combined:
                    logger.info(f"pypdf successfully extracted {len(combined)} characters from {filename}")
                    return combined
            except Exception as ex:
                logger.warning(f"pypdf extraction failed for {filename}: {ex}. Trying pdfplumber...")

            # Fall back to pdfplumber
            try:
                import pdfplumber

                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    page_texts = []
                    for page in pdf.pages:
                        page_str = page.extract_text() or ""
                        if page_str.strip():
                            page_texts.append(page_str)
                        # Extract table rows if present
                        tables = page.extract_tables() or []
                        for table in tables:
                            for row in table:
                                cleaned_row = [str(c).strip() for c in row if c is not None and str(c).strip()]
                                if cleaned_row:
                                    page_texts.append(" | ".join(cleaned_row))
                    combined = "\n".join(page_texts).strip()
                    if combined:
                        logger.info(f"pdfplumber successfully extracted {len(combined)} characters from {filename}")
                        return combined
            except Exception as ex:
                logger.warning(f"pdfplumber extraction failed for {filename}: {ex}")

        # 3. Local fallback for UTF-8 text documents
        try:
            text = file_bytes.decode("utf-8").strip()
            if text:
                return text
        except UnicodeDecodeError:
            pass

        # 4. If no text could be extracted, raise an informative error instead of returning a dummy string
        raise ValueError(
            f"Could not extract any readable text from '{filename}'. "
            f"Please ensure the file is a text-based PDF or plain text, or configure AWS Textract for OCR."
        )

    @classmethod
    def extract_with_groq(cls, ocr_text: str) -> Optional[InvoiceData]:
        """Extracts structured invoice entities using Groq API."""
        if not settings.GROQ_API_KEY:
            return None
        try:
            from groq import Groq

            client = Groq(api_key=settings.GROQ_API_KEY)
            prompt = (
                "You are an expert financial auditor and data extraction system. "
                "Parse the following OCR invoice text into a strict JSON object with these exact keys:\n"
                "- vendor_name: (string) the billing vendor or supplier name\n"
                "- invoice_number: (string) unique invoice identifier\n"
                "- invoice_date: (string, YYYY-MM-DD)\n"
                "- due_date: (string, YYYY-MM-DD or null)\n"
                "- line_items: (list of objects) each with description (string), quantity (number), "
                "unit_price (number), total_price (number)\n"
                "- subtotal: (number) total amount before tax\n"
                "- tax_amount: (number) total tax/GST/VAT amount (0 if none)\n"
                "- grand_total: (number) final invoice total due\n"
                "- currency: (string, e.g. USD, INR, EUR)\n\n"
                "Return ONLY the raw JSON object. Do not wrap in markdown or commentary.\n\n"
                f"OCR Text:\n{ocr_text}"
            )
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            raw_content = response.choices[0].message.content.strip()
            cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw_content).strip()
            invoice = InvoiceData.model_validate_json(cleaned)
            logger.info(f"Groq successfully extracted structured invoice: {invoice.invoice_number}")
            return invoice
        except Exception as e:
            logger.warning(f"Groq LLM extraction failed: {e}. Falling back to heuristic parsing.")
            return None

    @classmethod
    def extract_with_gemini(cls, ocr_text: str) -> Optional[InvoiceData]:
        """Extracts structured invoice entities using Google Gemini if configured."""
        if not settings.GEMINI_API_KEY:
            return None
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                "Extract invoice data into JSON conforming to: vendor_name, invoice_number, "
                "invoice_date (YYYY-MM-DD), due_date (YYYY-MM-DD or null), "
                "line_items (list of description, quantity, unit_price, total_price), "
                "subtotal, tax_amount, grand_total, currency.\n\n"
                f"Text:\n{ocr_text}"
            )
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            raw = response.text.strip()
            cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw).strip()
            return InvoiceData.model_validate_json(cleaned)
        except Exception as e:
            logger.warning(f"Gemini LLM extraction failed: {e}")
            return None

    @classmethod
    def parse_text_to_invoice(cls, ocr_text: str) -> InvoiceData:
        """Parses raw text blocks into a validated Pydantic InvoiceData model.

        Attempts high-accuracy LLM structured extraction first (Groq / Gemini),
        and seamlessly falls back to a deterministic regex parser for offline / test environments.
        """
        # In testing environment or offline test runners, use deterministic local parser directly
        if settings.APP_ENV == "testing":
            return cls._parse_text_heuristic(ocr_text)

        # 1. Attempt LLM extraction if API keys are configured
        if settings.GROQ_API_KEY:
            llm_invoice = cls.extract_with_groq(ocr_text)
            if llm_invoice:
                return llm_invoice

        if settings.GEMINI_API_KEY:
            llm_invoice = cls.extract_with_gemini(ocr_text)
            if llm_invoice:
                return llm_invoice

        # 2. Deterministic regex & heuristic fallback
        return cls._parse_text_heuristic(ocr_text)

    @classmethod
    def _parse_text_heuristic(cls, ocr_text: str) -> InvoiceData:
        """Deterministic heuristic and regex extraction for offline and unit test execution."""
        lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]

        # 1. Vendor Name
        vendor = "Unknown Vendor"
        for i, line in enumerate(lines):
            upper_line = line.upper()
            if any(k in upper_line for k in ("VENDOR:", "FROM:", "BILL FROM:", "SUPPLIER:", "SELLER:")):
                after = line.split(":", 1)[1].strip()
                if after:
                    vendor = after
                    break
                elif i + 1 < len(lines):
                    vendor = lines[i + 1]
                    break

        if vendor == "Unknown Vendor" and lines:
            for line in lines:
                if not line.startswith("=") and not line.startswith("-") and line != "INVOICE" and line != "TAX INVOICE":
                    vendor = line
                    break

        # 2. Invoice Number
        inv_match = re.search(
            r"(?:Invoice\s*(?:Number|#|No\.?)|Inv\s*#)[:\s]+([A-Za-z0-9-_]+)",
            ocr_text,
            re.IGNORECASE,
        )
        invoice_number = inv_match.group(1) if inv_match else "INV-DEFAULT-001"

        # 3. Invoice Date
        date_match = re.search(
            r"(?:Invoice\s+)?Date[:\s]+([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}-[A-Za-z]+-\d{4}|\d{4}-\d{2}-\d{2})",
            ocr_text,
            re.IGNORECASE,
        )
        invoice_date = date.today()
        if date_match:
            date_str = date_match.group(1).strip()
            for fmt in ("%B %d, %Y", "%b %d, %Y", "%d-%b-%Y", "%d-%B-%Y", "%Y-%m-%d"):
                try:
                    invoice_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue

        # 4. Totals (Subtotal, Tax, Grand Total)
        subtotal_match = re.search(r"\bSUBTOTAL[:\s]+(?:\$\s*)?([\d,]+\.?\d*)", ocr_text, re.IGNORECASE)
        tax_match = re.search(
            r"\b(?:TAX|GST|VAT|SALES\s+TAX)(?:\s*\(.*?\))?[:\s]+(?:\$\s*)?([\d,]+\.?\d*)",
            ocr_text,
            re.IGNORECASE,
        )
        total_match = re.search(
            r"\b(?:TOTAL\s+DUE|GRAND\s+TOTAL|BALANCE\s+DUE|TOTAL)[:\s]+(?:\$\s*)?([\d,]+\.?\d*)",
            ocr_text,
            re.IGNORECASE,
        )

        subtotal = Decimal(subtotal_match.group(1).replace(",", "")) if subtotal_match else Decimal("0.00")
        tax_amount = Decimal(tax_match.group(1).replace(",", "")) if tax_match else Decimal("0.00")
        grand_total = Decimal(total_match.group(1).replace(",", "")) if total_match else (subtotal + tax_amount)

        # 5. Line Items
        line_items = []
        # Pattern matching item line like: "1. Setup 1 $3,000.00 $3,000.00" or "Cloud Setup 1 35000.00 35000.00"
        item_pattern = re.compile(
            r"^(?:\d+\.?\s*)?([A-Za-z0-9\s().+-]+?)\s+(\d+)\s+\$?([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})$"
        )
        for line in lines:
            m = item_pattern.match(line)
            if m:
                desc, qty, price, total = m.groups()
                line_items.append(
                    LineItem(
                        description=desc.strip(),
                        quantity=Decimal(qty),
                        unit_price=Decimal(price.replace(",", "")),
                        total_price=Decimal(total.replace(",", "")),
                    )
                )

        if not line_items:
            # If no line items extracted, create a single summary item matching the subtotal
            line_items.append(
                LineItem(
                    description="General Invoiced Services",
                    quantity=Decimal("1"),
                    unit_price=subtotal,
                    total_price=subtotal,
                )
            )

        return InvoiceData(
            vendor_name=vendor,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            line_items=line_items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            grand_total=grand_total,
            currency="USD",
        )
