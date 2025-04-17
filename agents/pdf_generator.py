# agents/pdf_generator.py

from fpdf import FPDF
import os
import re

def replace_emojis(text):
    """
    Replace specific unsupported emojis with text equivalents.
    You can customize this function to include more replacements as needed.
    """
    text = text.replace("🚨", "[Risk]")
    text = text.replace("✅", "[OK]")
    # Add further replacements if needed:
    # text = text.replace("😊", "[Smile]")  for example
    return text

class PDFReportGenerator(FPDF):
    def __init__(self, title="EKS Operational Report"):
        super().__init__()
        self.title = title
        # Define the path to your fonts folder relative to this file.
        base_font_path = os.path.join(os.path.dirname(__file__), "..", "fonts")
        regular_font_path = os.path.join(base_font_path, "DejaVuSans.ttf")
        bold_font_path = os.path.join(base_font_path, "DejaVuSans-Bold.ttf")
        italic_font_path = os.path.join(base_font_path, "DejaVuSans-Oblique.ttf")  # Adjust filename if needed
        
        # Register font variants with FPDF (uni=True enables Unicode support)
        self.add_font("DejaVu", "", regular_font_path, uni=True)
        self.add_font("DejaVu", "B", bold_font_path, uni=True)
        self.add_font("DejaVu", "I", italic_font_path, uni=True)
    
    def header(self):
        # Use the bold variant for the header title.
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, self.title, border=False, ln=1, align="C")
        self.ln(10)
    
    def footer(self):
        # For simplicity, use the regular font for the footer
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf(report_text: str, output_filename: str = "eks_operational_report.pdf"):
    report_text = replace_emojis(report_text)

    pdf = PDFReportGenerator()
    pdf.add_page()
    pdf.set_font("DejaVu", "", 12)

    for line in report_text.splitlines():
        if line.strip():
            pdf.multi_cell(0, 10, line)
        else:
            pdf.ln(5)

    pdf.output(output_filename)
    return output_filename
    
    # Write report content line-by-line
#    for line in report_text.splitlines():
#        pdf.multi_cell(0, 10, line)
        
#    pdf.output(output_filename)
#    return output_filename
