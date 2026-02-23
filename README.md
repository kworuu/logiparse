# 📦 LogiParse — Logistics Invoice & Waybill Extractor

> **Built for the OLTEK Solutions "Paper to Data: Logistics Automation Challenge"**  
> Turns messy logistics documents into clean, structured, machine-readable data.

---

## What It Does

LogiParse is a logistics document intelligence tool that:

1. **Extracts** key fields from raw invoice/waybill text or PDF files
2. **Validates** the extracted data for completeness and logical consistency
3. **Outputs** clean, structured JSON ready for database ingestion

### Fields Extracted
| Field | Example |
|---|---|
| Invoice Number | `INV-2024-00892` |
| Date | `February 20, 2024` |
| Sender / Shipper | `ABC Warehousing Corp., Cebu` |
| Receiver / Consignee | `XYZ Retail Store, Makati` |
| Tracking Number | `TRK-PH-44821` |
| Total Weight | `45.5 kg` |
| Total Amount | `PHP 9,500.00` |
| Line Items | Description, Qty, Unit Price, Line Total |

### Validation Checks
- ✅ All critical fields present
- ✅ Total amount is a valid positive number
- ✅ Line item math: `Qty × UnitPrice = LineTotal`
- ⚠️ Warnings for missing optional fields

---

## Tech Stack

- **Python 3.10+**
- **PyMuPDF** — PDF text extraction
- **Regex (re)** — Pattern-based field parsing
- **Streamlit** — Web interface
- No ML model required — pure rule-based extraction optimized for logistics document layouts

---

## Demo

### Input: Paste text or upload a PDF invoice
### Output:
```json
{
  "extracted_data": {
    "invoice_number": "INV-2024-00892",
    "date": "February 20, 2024",
    "sender": "ABC Warehousing Corp., Mandaue City, Cebu",
    "receiver": "XYZ Retail Store, Makati City, Metro Manila",
    "total_weight": "45.5 kg",
    "total_amount": "9500.00",
    "currency": "PHP",
    "tracking_number": "TRK-PH-44821",
    "items": [
      { "description": "Industrial Fan Motor", "quantity": 2, "unit_price": "1500.00", "line_total": "3000.00" },
      { "description": "Conveyor Belt Segment", "quantity": 5, "unit_price": "800.00", "line_total": "4000.00" }
    ]
  },
  "validation_report": {
    "status": "PASS ✅",
    "issues": [],
    "warnings": [],
    "field_coverage": "5/5 key fields extracted"
  }
}
```

---

## Installation & Running

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/logiparse.git
cd logiparse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the web app
streamlit run app.py

# OR run the CLI demo
python extractor.py
```

---

## Project Structure

```
logiparse/
├── extractor.py      # Core extraction + validation logic
├── app.py            # Streamlit web interface
├── requirements.txt  # Dependencies
└── README.md
```

---

## Why This Matters for Logistics

Manual data entry from paper invoices and waybills is one of the biggest bottlenecks in Philippine logistics operations. A single mistyped amount or undetected missing field can cause shipment delays, billing disputes, and inventory mismatches.

LogiParse automates the extraction and validation pipeline — the same way barcode scanning eliminated manual product entry at checkout counters.

---

## Developer

Built by a 2nd-year BS Computer Science student from Cebu as a portfolio project for the OLTEK Solutions Logistics Automation Challenge (Feb 2026).

**Skills demonstrated:** Python, Regex/NLP, PDF parsing, Data Validation, Streamlit UI