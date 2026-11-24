"""Build a Word version of the simulation report for Google Docs.

Requires python-docx. Run from the repository root:
    python simulation/tools/build_report_docx.py

Upload the .docx to Google Drive and open it with Google Docs, or open it and paste
into an existing Google Doc; headings, bold, and italics carry over.
"""
from pathlib import Path
import re

from docx import Document
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "08-simulation-report.md"
OUTPUT = ROOT / "Russia-simulation-report.docx"


def add_runs(paragraph, text):
    """Add text to a paragraph, honoring **bold** and *italic* markers."""
    for part in re.split(r"(\*\*.+?\*\*|\*.+?\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("*"):
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def build():
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    for section in doc.sections:
        section.left_margin = section.right_margin = Inches(1)
        section.top_margin = section.bottom_margin = Inches(1)

    for block in re.split(r"\n\s*\n", SOURCE.read_text(encoding="utf-8").strip()):
        block = block.strip()
        if block.startswith("# "):
            doc.add_heading(block[2:], level=0)
        elif block.startswith("## "):
            doc.add_heading(block[3:], level=1)
        elif block.startswith("- "):
            for line in block.splitlines():
                add_runs(doc.add_paragraph(style="List Bullet"), line[2:].strip())
        else:
            add_runs(doc.add_paragraph(), " ".join(block.splitlines()))
    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())
