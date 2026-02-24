import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import pymupdf
import re

from datetime import datetime

# This loads the hidden variables from your .env file
load_dotenv()

# This reaches into the environment and securely grabs your key
my_secret_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=my_secret_key)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    doc = pymupdf.open(pdf_path)
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
    Gemini AI extracts key logistics fields from raw invoice/waybill text.
    Returns a structured dictionary.
    """

    prompt = f"""You are an expert data extractor. Read the following invoice text messages and extract the details.
    Return ONLY  a valid, raw JSON object. Do not add Markdown code blocks (like '''json). If a field is missing, return null.

    Required Keys:
    - invoice_number
    - date
    - sender
    - receiver
    - total_weight (include the unit e.g..., '850 kg')
    - total_amount (numbers only, no commas)
    - currency (e.g., USD, PHP)
    - tracking_number
    - items (a list of objects with keys: description, quantity, unit_price, line_total)

    Invoice text:
    {text}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        # Sometimes the AI tries to be helpful and wraps the JSON in markdown blocks.
        # This cleans it up so Python doesn't crash.
        clean_text = response.text.strip().removeprefix(
            '```json').removesuffix('```').strip()

        # Converts the text response into a real Python dictionary
        result = json.loads(clean_text)

        # Re-add the raw text preview to prevent Streamlit from breaking
        result["raw_text_preview"] = text[:300] + \
            "..." if len(text) > 300 else text

        return result

    except Exception as e:
        print(f"AI Extraction has failed: {e}")
        # If the AI fails or the internet drops, return empty data so the app doesn't crash
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
            "raw_text_preview": text[:300] + "..."
        }


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
        warnings.append(
            "⚠️  Date not detected — may be missing or in unusual format")
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
                issues.append(
                    "❌ Total amount is zero or negative — suspicious")
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
