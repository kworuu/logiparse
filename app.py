"""
LogiParse - Logistics Invoice & Waybill Extractor.
This module provides a Streamlit web interface to extract, 
parse, and validate data from PDF invoices and text.
"""

import tempfile
import os
import sys
import json
import streamlit as st

from extractor import process_invoice
sys.path.insert(0, os.path.dirname(__file__))


# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LogiParse — Invoice Extractor",
    page_icon="📦",
    layout="wide"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main { background-color: #0d1117; }

    h1, h2, h3 { font-family: 'Space Mono', monospace; }

    .hero-title {
        font-family: 'Space Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        color: #00e5ff;
        letter-spacing: -1px;
        margin-bottom: 0;
    }

    .hero-sub {
        color: #8b949e;
        font-size: 1rem;
        margin-top: 4px;
        margin-bottom: 2rem;
    }

    .field-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }

    .field-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #58a6ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    .field-value {
        font-size: 1rem;
        color: #e6edf3;
        font-weight: 600;
    }

    .field-missing {
        color: #484f58;
        font-style: italic;
        font-size: 0.9rem;
    }

    .status-pass {
        background: #0d2818;
        border: 1px solid #238636;
        border-radius: 8px;
        padding: 12px 16px;
        color: #3fb950;
        font-family: 'Space Mono', monospace;
        font-size: 1rem;
    }

    .status-fail {
        background: #2d1117;
        border: 1px solid #da3633;
        border-radius: 8px;
        padding: 12px 16px;
        color: #f85149;
        font-family: 'Space Mono', monospace;
        font-size: 1rem;
    }

    .issue-item {
        background: #2d1117;
        border-left: 3px solid #da3633;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
        color: #ffa198;
    }

    .warning-item {
        background: #272115;
        border-left: 3px solid #d29922;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
        color: #e3b341;
    }

    .coverage-badge {
        display: inline-block;
        background: #1f3a5f;
        color: #58a6ff;
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid #1f6feb;
        margin-top: 6px;
    }

    .item-row {
        display: flex;
        justify-content: space-between;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        font-size: 0.9rem;
        color: #e6edf3;
    }

    .stTextArea textarea {
        font-family: 'Space Mono', monospace;
        font-size: 0.82rem;
        background: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #1f6feb, #00e5ff22);
        color: #58a6ff;
        border: 1px solid #1f6feb;
        font-family: 'Space Mono', monospace;
        font-size: 0.85rem;
        padding: 0.6rem 1.4rem;
        border-radius: 8px;
        width: 100%;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: #1f6feb;
        color: white;
        border-color: #58a6ff;
    }

    .divider {
        border: none;
        border-top: 1px solid #21262d;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">LogiParse</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Logistics Invoice & Waybill Extractor — Paper to Structured Data</div>',
            unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ─── Input Section ───────────────────────────────────────────────────────────
col_input, col_results = st.columns([1, 1], gap="large")

with col_input:
    st.markdown("### Input Document")

    input_mode = st.radio(
        "Source type",
        ["Paste Text", "Upload PDF"],
        horizontal=True,
        label_visibility="collapsed"
    )

    raw_result = None

    if input_mode == "Paste Text":
        default_text = """LOGISTICS INVOICE
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
Total Amount: PHP 9,500.00"""

        text_input = st.text_area(
            "Paste invoice or waybill text below:",
            value=default_text,
            height=320,
            label_visibility="collapsed"
        )

        if st.button("⚡ Extract & Validate"):
            if text_input.strip():
                with st.spinner("Parsing document..."):
                    raw_result = process_invoice(text_input, is_pdf=False)
            else:
                st.error("Please paste some invoice text first.")

    else:
        uploaded_file = st.file_uploader(
            "Upload a PDF invoice or waybill",
            type=["pdf"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            st.success(f"✅ Loaded: {uploaded_file.name}")
            if st.button("⚡ Extract & Validate"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                with st.spinner("Reading PDF and extracting data..."):
                    raw_result = process_invoice(tmp_path, is_pdf=True)
                os.unlink(tmp_path)

# ─── Results Section ─────────────────────────────────────────────────────────
with col_results:
    if raw_result:
        data = raw_result["extracted_data"]
        validation = raw_result["validation_report"]
        meta = raw_result["metadata"]

        st.markdown("### Extracted Fields")

        def field_card(label, value):
            val_html = f'<div class="field-value">{value}</div>' if value else '<div class="field-missing">Not detected</div>'
            st.markdown(f"""
            <div class="field-card">
                <div class="field-label">{label}</div>
                {val_html}
            </div>
            """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            field_card("Invoice Number", data.get("invoice_number"))
            field_card("Sender", data.get("sender"))
            field_card("Total Weight", data.get("total_weight"))
        with col_b:
            field_card("Date", data.get("date"))
            field_card("Receiver", data.get("receiver"))
            amt = data.get("total_amount")
            cur = data.get("currency", "PHP")
            field_card("Total Amount", f"{cur} {amt}" if amt else None)

        if data.get("tracking_number"):
            field_card("Tracking Number", data["tracking_number"])

        # Line Items
        if data.get("items"):
            st.markdown("**Line Items**")
            for item in data["items"]:
                st.markdown(f"""
                <div class="item-row">
                    <span>{item['description']}</span>
                    <span>Qty: {item['quantity']}</span>
                    <span>Unit: {item['unit_price']}</span>
                    <span><strong>{item['line_total']}</strong></span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # Validation Report
        st.markdown("### Validation Report")

        status = validation["status"]
        status_class = "status-pass" if "PASS" in status else "status-fail"
        st.markdown(
            f'<div class="{status_class}">{status}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="coverage-badge"> {validation["field_coverage"]}</div>', unsafe_allow_html=True)

        if validation.get("issues"):
            st.markdown("<br>", unsafe_allow_html=True)
            for issue in validation["issues"]:
                st.markdown(
                    f'<div class="issue-item">{issue}</div>', unsafe_allow_html=True)

        if validation.get("warnings"):
            for warning in validation["warnings"]:
                st.markdown(
                    f'<div class="warning-item">{warning}</div>', unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # JSON Export
        st.markdown("### Structured Output (JSON)")
        export_data = {
            "extracted_data": {k: v for k, v in data.items() if k != "raw_text_preview"},
            "validation_report": validation,
            "metadata": meta
        }
        json_str = json.dumps(export_data, indent=2)
        st.code(json_str, language="json")
        st.download_button(
            label="⬇️ Download JSON",
            data=json_str,
            file_name="extracted_invoice.json",
            mime="application/json"
        )

    else:
        st.markdown("### Extracted Fields")
        st.markdown("""
        <div style="color:#484f58; padding: 60px 20px; text-align:center; font-family:'Space Mono',monospace; font-size:0.85rem; border: 1px dashed #30363d; border-radius:10px;">
            Paste invoice text or upload a PDF<br>then click Extract & Validate
        </div>
        """, unsafe_allow_html=True)
