import json
import os
import base64
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

load_dotenv()
my_secret_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=my_secret_key)

# Maps file extensions to MIME types Gemini understands
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

EXTRACTION_PROMPT = """You are an expert logistics data extractor.
Look at this document (it may be a scanned image, photo, or PDF of an invoice or waybill).
Extract all the relevant fields and return ONLY a valid raw JSON object.
Do not add Markdown code blocks or any explanation — just the JSON.
If a field is missing or unreadable, return null for that field.

Required keys:
- invoice_number
- date
- sender
- receiver
- total_weight (include unit, e.g. '45.5 kg')
- total_amount (numbers only, no commas or currency symbols)
- currency (e.g. PHP, USD)
- tracking_number
- items (list of objects with keys: description, quantity, unit_price, line_total)
"""


def parse_invoice_from_file(file_path: str) -> dict:
    """
    Send a file (PDF, PNG, JPG) directly to Gemini for extraction.
    Gemini reads it natively — no text conversion needed.
    """
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = MIME_TYPES.get(ext)

    if not mime_type:
        raise ValueError(f"Unsupported file type: {ext}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()
    encoded = base64.standard_b64encode(file_bytes).decode("utf-8")

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            {"mime_type": mime_type, "data": encoded},
            EXTRACTION_PROMPT
        ])

        clean_text = response.text.strip().removeprefix(
            "```json").removesuffix("```").strip()
        result = json.loads(clean_text)
        result["raw_text_preview"] = f"[Extracted from {ext.upper()} file via Gemini Vision]"
        return result

    except Exception as e:
        print(f"AI extraction failed: {e}")
        return _empty_result(f"Extraction failed: {e}")


def parse_invoice_from_text(text: str) -> dict:
    """
    Send plain pasted text to Gemini for extraction.
    """
    prompt = EXTRACTION_PROMPT + f"\n\nDocument text:\n{text}"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        clean_text = response.text.strip().removeprefix(
            "```json").removesuffix("```").strip()
        result = json.loads(clean_text)
        result["raw_text_preview"] = text[:300] + \
            "..." if len(text) > 300 else text
        return result

    except Exception as e:
        print(f"AI extraction failed: {e}")
        return _empty_result(f"Extraction failed: {e}")


def _empty_result(preview: str) -> dict:
    """Return a blank result when extraction fails."""
    return {
        "invoice_number": None,
        "date": None,
        "sender": None,
        "receiver": None,
        "total_weight": None,
        "total_amount": None,
        "currency": None,
        "items": [],
        "tracking_number": None,
        "raw_text_preview": preview
    }


def validate_extracted_data(data: dict) -> dict:
    """
    Run validation checks on extracted fields.
    """
    issues = []
    warnings = []

    if not data.get("invoice_number"):
        issues.append("❌ Invoice number not found")
    if not data.get("date"):
        warnings.append("⚠️  Date not detected — may be missing or unusual format")
    if not data.get("sender"):
        warnings.append("⚠️  Sender/Shipper not found")
    if not data.get("receiver"):
        warnings.append("⚠️  Receiver/Consignee not found")
    if not data.get("total_amount"):
        issues.append("❌ Total amount not found")
    else:
        try:
            val = float(str(data["total_amount"]).replace(",", ""))
            if val <= 0:
                issues.append("❌ Total amount is zero or negative — suspicious")
        except ValueError:
            issues.append("❌ Total amount is not a valid number")

    for item in data.get("items", []):
        try:
            calc = float(item["quantity"]) * float(str(item["unit_price"]).replace(",", ""))
            stated = float(str(item["line_total"]).replace(",", ""))
            if abs(calc - stated) > 0.5:
                issues.append(
                    f"❌ Line item '{item['description']}': "
                    f"Qty × UnitPrice ({calc:.2f}) ≠ LineTotal ({stated:.2f})"
                )
        except (ValueError, KeyError):
            pass

    status = "PASS ✅" if not issues else "FAIL ❌"

    return {
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "field_coverage": f"{sum(1 for v in [data.get('invoice_number'), data.get('date'), data.get('sender'), data.get('receiver'), data.get('total_amount')] if v)}/5 key fields extracted"
    }


def process_invoice(source, source_type="text") -> dict:
    """
    Main pipeline: extract → validate → output.
    source_type: 'text', 'pdf', 'image'
    """
    if source_type == "text":
        parsed = parse_invoice_from_text(source)
    else:
        # Both PDF and image go directly to Gemini Vision
        parsed = parse_invoice_from_file(source)

    validation = validate_extracted_data(parsed)

    return {
        "metadata": {
            "processed_at": datetime.now().isoformat(),
            "source_type": source_type.upper()
        },
        "extracted_data": parsed,
        "validation_report": validation
    }


# --- CLI demo ---
if __name__ == "__main__":
    sample = """
    LOGISTICS INVOICE
    Invoice No: INV-2024-00892
    Date: February 20, 2024
    Tracking No: TRK-PH-44821

    From: ABC Warehousing Corp., Mandaue City, Cebu
    To: XYZ Retail Store, Makati City, Metro Manila

    Industrial Fan Motor     2    1500.00    3000.00
    Conveyor Belt Segment    5     800.00    4000.00
    Safety Gloves (box)     10     250.00    2500.00

    Total Weight: 45.5 kg
    Total Amount: PHP 9,500.00
    """
    result = process_invoice(sample, source_type="text")
    print(json.dumps(result, indent=2))