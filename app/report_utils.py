from fpdf import FPDF
import io
import re

def strip_unicode(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def generate_pdf(summary_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    clean_text = strip_unicode(summary_text)
    for line in clean_text.splitlines():
        pdf.multi_cell(0, 10, line)

    # Get PDF as bytes using output(dest='S').encode('latin-1')
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_bytes)

