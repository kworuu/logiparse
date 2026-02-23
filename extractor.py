import fitz  # PyMuPDF
import re
import json
from datetime import datetime


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text


def extract_text_from_string(raw_text: str) -> str:
    """Use raw text directly (for plain text/demo inputs)."""
    return raw_text


def parse_invoice(text: str) -> dict:
    """
    Extract key logistics fields from raw invoice/waybill text.
    Returns a structured dictionary.
    """
    result = {
        "invoice_number": None,
        "date": None,
        "sender": None,
        "receiver": None,
        "total_weight": None,
        "total_amount": None,
        "currency": None,
        "items": [],
        "tracking_number": None,
        "raw_text_preview": text[:300] + "..." if len(text) > 300 else text
    }

    # --- Invoice Number ---
    inv_match = re.search(
        r'(?:invoice\s*(?:no\.?|number|#|num)[:\s#]+)([A-Z0-9\-\/]+)',
        text, re.IGNORECASE
    )
    if inv_match:
        result["invoice_number"] = inv_match.group(1).strip()

    # --- Date ---
    date_match = re.search(
        r'(?:date|dated|issued)[:\s]*'
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}'
        r'|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}'
        r'|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})',
        text, re.IGNORECASE
    )
    if date_match:
        result["date"] = date_match.group(1).strip()

    # --- Sender ---
    sender_match = re.search(
        r'(?:from|sender|shipper|consignor)[:\s]+([^\n,]+)',
        text, re.IGNORECASE
    )
    if sender_match:
        result["sender"] = sender_match.group(1).strip()

    # --- Receiver ---
    receiver_match = re.search(
        r'(?:to|receiver|recipient|consignee|billed\s+to|deliver\s+to)[:\s]+([^\n,]+)',
        text, re.IGNORECASE
    )
    if receiver_match:
        result["receiver"] = receiver_match.group(1).strip()

    # --- Total Weight ---
    weight_match = re.search(
        r'(?:total\s+)?weight[:\s]*([\d,\.]+)\s*(kg|lbs?|g|tons?)?',
        text, re.IGNORECASE
    )
    if weight_match:
        unit = weight_match.group(2) or "kg"
        result["total_weight"] = f"{weight_match.group(1).strip()} {unit}"

    # --- Total Amount ---
    amount_match = re.search(
        r'(?:total|grand\s+total|amount\s+due|total\s+amount)[:\s]*'
        r'(PHP|₱|\$|USD|EUR)?\s*([\d,\.]+)',
        text, re.IGNORECASE
    )
    if amount_match:
        result["currency"] = amount_match.group(1) or "PHP"
        result["total_amount"] = amount_match.group(2).replace(",", "").strip()

    # --- Tracking Number ---
    tracking_match = re.search(
        r'(?:tracking\s*(?:no|number|#)|waybill\s*(?:no|number|#))[:\s#]*([A-Z0-9\-]+)',
        text, re.IGNORECASE
    )
    if tracking_match:
        result["tracking_number"] = tracking_match.group(1).strip()

    # --- Line Items ---
    # Look for patterns like: ItemName   Qty   UnitPrice   Total
    item_pattern = re.findall(
        r'([A-Za-z][A-Za-z0-9\s\-]{2,30})\s+(\d+)\s+([\d,\.]+)\s+([\d,\.]+)',
        text
    )
    for match in item_pattern[:10]:  # cap at 10 items
        name, qty, unit_price, total = match
        result["items"].append({
            "description": name.strip(),
            "quantity": int(qty),
            "unit_price": unit_price.replace(",", ""),
            "line_total": total.replace(",", "")
        })

    return result


def validate_extracted_data(data: dict) -> dict:
    """
    Run basic validation checks on extracted fields.
    Returns a report of issues found.
    """
    issues = []
    warnings = []

    if not data["invoice_number"]:
        issues.append("❌ Invoice number not found")
    if not data["date"]:
        warnings.append("⚠️  Date not detected — may be missing or in unusual format")
    if not data["sender"]:
        warnings.append("⚠️  Sender/Shipper not found")
    if not data["receiver"]:
        warnings.append("⚠️  Receiver/Consignee not found")
    if not data["total_amount"]:
        issues.append("❌ Total amount not found")
    else:
        try:
            val = float(data["total_amount"])
            if val <= 0:
                issues.append("❌ Total amount is zero or negative — suspicious")
        except ValueError:
            issues.append("❌ Total amount is not a valid number")

    if data["items"]:
        for i, item in enumerate(data["items"]):
            try:
                calc = float(item["quantity"]) * float(item["unit_price"])
                stated = float(item["line_total"])
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
        "field_coverage": f"{sum(1 for v in [data['invoice_number'], data['date'], data['sender'], data['receiver'], data['total_amount']] if v)}/5 key fields extracted"
    }


def process_invoice(source, is_pdf=False) -> dict:
    """Main pipeline: extract → parse → validate → output."""
    if is_pdf:
        raw_text = extract_text_from_pdf(source)
    else:
        raw_text = source  # treat as plain text

    parsed = parse_invoice(raw_text)
    validation = validate_extracted_data(parsed)

    output = {
        "metadata": {
            "processed_at": datetime.now().isoformat(),
            "source_type": "PDF" if is_pdf else "Text"
        },
        "extracted_data": parsed,
        "validation_report": validation
    }

    return output


# --- Demo / CLI usage ---
if __name__ == "__main__":
    sample_invoice = """
    LOGISTICS INVOICE
    Invoice No: INV-2024-00892
    Date: February 20, 2024
    Tracking No: TRK-PH-44821

    From: ABC Warehousing Corp., Mandaue City, Cebu
    To: XYZ Retail Store, Makati City, Metro Manila

    Items:
    Industrial Fan Motor     2    1500.00    3000.00
    Conveyor Belt Segment    5     800.00    4000.00
    Safety Gloves (box)     10     250.00    2500.00

    Total Weight: 45.5 kg
    Total Amount: PHP 9,500.00
    """

    result = process_invoice(sample_invoice, is_pdf=False)
    print(json.dumps(result, indent=2))