"""Build the printable brief from the reviewed Markdown sources.

Requires reportlab. Run from any directory with Python 3.
The assessment and each portfolio are separate pages. No live sources are fetched.
"""
from pathlib import Path
import re
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Russia-strategy-brief-review.pdf"
source = (ROOT / "01-strategy-brief.md").read_text(encoding="utf-8")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("BriefTitle", fontName="Helvetica-Bold", fontSize=17,
                          leading=21, spaceAfter=9, textColor=colors.black))
styles.add(ParagraphStyle("BriefBody", fontName="Times-Roman", fontSize=11,
                          leading=14, spaceAfter=10, alignment=TA_LEFT))
styles.add(ParagraphStyle("BriefSmall", fontName="Helvetica", fontSize=9,
                          leading=12, spaceAfter=8))
styles.add(ParagraphStyle("BriefRef", fontName="Times-Roman", fontSize=9.5,
                          leading=12, spaceAfter=7, splitLongWords=True))

def inline(text):
    # Convert links before escaping so their labels and targets stay intact.
    saved = []
    def link(match):
        label, target = match.groups()
        if not target.startswith("https://"):
            return label
        saved.append(f'<link href="{escape(target, quote=True)}" color="#163A5F">{escape(label)}</link>')
        return f"LINKTOKEN{len(saved)-1}END"
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    for i, value in enumerate(saved):
        text = text.replace(f"LINKTOKEN{i}END", value)
    return text

sections = dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", source, re.M | re.S))
story = []
titles = ["One page country assessment", "Education recommendation for Tiger",
          "Technology strategy recommendation for Steve",
          "Intelligence and immigration recommendation for Gloria",
          "Executive recommendation for Steve with team review"]
for index, title in enumerate(titles):
    if index:
        story.append(PageBreak())
    story.append(Paragraph("Russia national innovation strategy" if index == 0 else title,
                           styles["BriefTitle"]))
    subtitle = ("One page country assessment | Team 2 | Steve, Gloria, Tiger" if index == 0
                else "Team 2 Russia | Proposed portfolio text for independent review")
    story.append(Paragraph(subtitle + " | 10 November 2026", styles["BriefSmall"]))
    paras = [p.strip() for p in sections[title].split("\n\n") if p.strip().startswith('*"')]
    expected = 5 if index == 0 else 3
    assert len(paras) == expected, (title, len(paras))
    for p in paras:
        story.append(Paragraph(inline(p), styles["BriefBody"]))
    story.append(Spacer(1, 5))
    story.append(Paragraph("AI generated review draft. Quoted italic text requires independent student review. "
                           "Citations, exact prompt, and factual critique follow in the appendices. "
                           "No team consensus is asserted.", styles["BriefSmall"]))

story.append(PageBreak())
story.append(Paragraph("References and source provenance", styles["BriefTitle"]))
for p in sections["References"].strip().split("\n\n"):
    if p.startswith("- "):
        for line in p.splitlines():
            story.append(Paragraph(inline(line[2:]), styles["BriefRef"]))
    elif p.strip():
        story.append(Paragraph(inline(p), styles["BriefRef"]))

story.append(PageBreak())
story.append(Paragraph("AI disclosure and prompt record", styles["BriefTitle"]))
disclosure = (ROOT / "06-ai-disclosure.md").read_text(encoding="utf-8")
# Render Markdown tables as separate readable records rather than narrow PDF grids.
for p in disclosure.split("\n\n"):
    p = p.strip()
    if not p or p.startswith("# AI use"):
        continue
    if p.startswith("## "):
        style = ParagraphStyle("Subhead", parent=styles["BriefBody"], fontName="Helvetica-Bold",
                               fontSize=12, leading=16, spaceBefore=12, keepWithNext=True)
        story.append(Paragraph(inline(p[3:]), style))
    elif p.startswith("|"):
        for line in p.splitlines()[2:]:
            fields = [v.strip() for v in line.strip("|").split("|")]
            if fields and fields[0]:
                story.append(Paragraph(inline(" - ".join(v for v in fields if v)), styles["BriefRef"]))
    elif p.startswith(">"):
        # Preserve the exact prompt's words and paragraph breaks.
        for q in p.split("\n>\n"):
            q = "\n".join(re.sub(r"^> ?", "", line) for line in q.splitlines())
            if q.strip():
                story.append(Paragraph(escape(q).replace("\n", "<br/>"), styles["BriefRef"]))
    elif re.match(r"\d+\. ", p):
        for line in p.splitlines():
            story.append(Paragraph(inline(line), styles["BriefRef"]))
    else:
        story.append(Paragraph(inline(p.replace("\n", " ")), styles["BriefRef"]))

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.7*inch, 0.38*inch, "Russia team preparation | Review draft | 10 November 2026")
    canvas.drawRightString(7.8*inch, 0.38*inch, str(doc.page))
    canvas.restoreState()

doc = SimpleDocTemplate(str(OUTPUT), pagesize=(8.5*inch, 11*inch),
                        rightMargin=0.7*inch, leftMargin=0.7*inch,
                        topMargin=0.62*inch, bottomMargin=0.65*inch,
                        title="Russia national innovation strategy review draft",
                        author="Prepared with ChatGPT for team review")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
