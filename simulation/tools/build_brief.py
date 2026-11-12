"""Build the printable strategy brief from 01-strategy-brief.md.

Requires reportlab. Run from any directory with Python 3:
    python simulation/tools/build_brief.py

The country assessment is kept on page 1; each later section starts a new page.
"""
from pathlib import Path
import re
from html import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01-strategy-brief.md"
OUTPUT = ROOT / "Russia-strategy-brief.pdf"

TITLE = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=15, leading=18, spaceAfter=3)
SUB = ParagraphStyle("Sub", fontName="Helvetica", fontSize=8.5, leading=11, spaceAfter=8,
                     textColor=colors.HexColor("#333333"))
H2 = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=2,
                    spaceAfter=6, keepWithNext=True)
BODY = ParagraphStyle("Body", fontName="Times-Roman", fontSize=10.5, leading=13.2, spaceAfter=6.5)
CELL = ParagraphStyle("Cell", fontName="Times-Roman", fontSize=9, leading=10.5)
CELL_B = ParagraphStyle("CellB", parent=CELL, fontName="Times-Bold")
REF = ParagraphStyle("Ref", fontName="Times-Roman", fontSize=10, leading=12.5, spaceAfter=5,
                     leftIndent=14, firstLineIndent=-14)


def inline(text):
    """Convert the small Markdown subset used in the brief to ReportLab markup."""
    saved = []

    def link(match):
        label, target = match.groups()
        saved.append(f'<link href="{escape(target, quote=True)}" color="#163A5F">{escape(label)}</link>')
        return f"\x00{len(saved) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, text)
    text = escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], text)


def table(block):
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in block.splitlines() if not re.match(r"^\|\s*-", line)]
    data = [[Paragraph(inline(c), CELL_B if r == 0 or i == 0 else CELL) for i, c in enumerate(row)]
            for r, row in enumerate(rows)]
    widths = [2.55 * inch] + [(7.1 - 2.55) / (len(rows[0]) - 1) * inch] * (len(rows[0]) - 1)
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6EBF0")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#555555")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.HexColor("#555555")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
    ]))
    return [t, Spacer(1, 7)]


def build():
    text = SOURCE.read_text(encoding="utf-8")
    story = []
    first_section = True
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), TITLE))
        elif block.startswith("## "):
            if not first_section:
                story.append(PageBreak())
            first_section = False
            story.append(Paragraph(inline(block[3:]), H2))
        elif block.startswith("|"):
            story.extend(table(block))
        elif re.match(r"\d+\. ", block):
            for line in block.splitlines():
                num, rest = line.split(". ", 1)
                story.append(Paragraph(f"[{num}] " + inline(rest), REF))
        elif len(story) == 1:
            story.append(Paragraph(inline(block), SUB))
        else:
            story.append(Paragraph(inline(block.replace("\n", " ")), BODY))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(0.7 * inch, 0.4 * inch, "Team 2 | Russia | Strategy brief")
        canvas.drawRightString(7.8 * inch, 0.4 * inch, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(OUTPUT), pagesize=(8.5 * inch, 11 * inch),
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.65 * inch,
                            title="Russia: National Innovation Strategy Brief",
                            author="Team 2 (Russia)")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return OUTPUT


if __name__ == "__main__":
    print(build())
