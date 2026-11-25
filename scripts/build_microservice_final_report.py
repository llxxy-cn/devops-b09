"""Render the B09 Microservice Lab report from its Markdown source.

Requires ReportLab and a CJK TrueType font. Run from the repository root:
  python scripts/build_microservice_final_report.py
"""

from __future__ import annotations

import html
import re
from functools import partial
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/final-report/MICROSERVICE-LAB-REPORT.md"
OUTPUT = ROOT / "docs/final-report/B09-Microservice-Lab-期末报告.pdf"
FONT = Path("C:/Windows/Fonts/simsun.ttc")
if not FONT.exists():
    raise SystemExit(f"SimSun font unavailable: {FONT}")
pdfmetrics.registerFont(TTFont("SimSun", str(FONT), subfontIndex=0))


class BoldParagraph(Paragraph):
    """Add a subtle second SimSun impression for headings."""

    def drawOn(self, canvas, x, y, _sW=0):
        super().drawOn(canvas, x, y, _sW)
        super().drawOn(canvas, x + 0.24, y, _sW)


class TOCEntry(Flowable):
    def __init__(self, title: str, page: int):
        super().__init__()
        self.title = title
        self.page = str(page)
        self.height = 49

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return self.width, self.height

    def draw(self):
        size = 18
        baseline = (self.height - size) / 2 + 3
        self.canv.setFont("SimSun", size)
        self.canv.setFillColor(colors.black)
        self.canv.drawString(0, baseline, self.title)
        self.canv.drawRightString(self.width, baseline, self.page)
        left = pdfmetrics.stringWidth(self.title, "SimSun", size) + 12
        right = self.width - pdfmetrics.stringWidth(self.page, "SimSun", size) - 12
        dot_width = pdfmetrics.stringWidth("·", "SimSun", size)
        count = max(0, int((right - left) / dot_width))
        self.canv.drawString(left, baseline, "·" * count)


body = ParagraphStyle(
    "body", fontName="SimSun", fontSize=13, leading=19,
    firstLineIndent=26, textColor=colors.black,
    spaceAfter=11, splitLongWords=True,
    allowOrphans=0, allowWidows=0,
)
heading = ParagraphStyle(
    "section", fontName="SimSun", fontSize=19, leading=28,
    textColor=colors.black, spaceBefore=18,
    spaceAfter=11, keepWithNext=True,
)
subheading = ParagraphStyle(
    "subheading", fontName="SimSun", fontSize=14, leading=20,
    textColor=colors.black, spaceBefore=11, spaceAfter=6,
    keepWithNext=True,
)
small = ParagraphStyle(
    "small", fontName="SimSun", fontSize=11, leading=16,
    textColor=colors.black, splitLongWords=True,
)
table_head = ParagraphStyle(
    "tablehead", parent=small, leading=16,
)


def clean_inline(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = html.escape(value)
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(
        r"`([^`]+)`",
        lambda match: (
            f"<nobr>{match.group(1)}</nobr>"
            if len(match.group(1)) <= 64 and "/" not in match.group(1)
            else match.group(1)
        ),
        value,
    )
    return value


def parse_table(lines: list[str], width: float) -> Table:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    cols = len(rows[0])
    if cols == 3:
        fractions = [0.22, 0.45, 0.33]
    elif cols == 2:
        fractions = [0.23, 0.77]
    else:
        fractions = [1 / cols] * cols
    data = [
        [
            (BoldParagraph if index == 0 else Paragraph)(
                clean_inline(cell), table_head if index == 0 else small
            )
            for cell in row
        ]
        for index, row in enumerate(rows)
    ]
    result = Table(data, colWidths=[width * part for part in fractions], repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    return result


def make_cover(story: list) -> None:
    story.extend([
        Spacer(1, 50 * mm),
        BoldParagraph("B09 Microservice Lab", ParagraphStyle(
            "coverEnglish", fontName="SimSun", fontSize=23, leading=32,
            textColor=colors.black, alignment=TA_CENTER)),
        Spacer(1, 7 * mm),
        BoldParagraph("DevOps 期末项目报告", ParagraphStyle(
            "coverChinese", fontName="SimSun", fontSize=21, leading=30,
            textColor=colors.black, alignment=TA_CENTER)),
        Spacer(1, 38 * mm),
    ])
    names = [
        ["分工", "姓名", "学号"],
        ["B1", "刘欣雨", "241880481"],
        ["B2", "黄新迪", "241880359"],
        ["B3", "丁卓", "241880585"],
        ["B4", "韩尚真", "241880556"],
    ]
    table = Table(names, colWidths=[68, 150, 150], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story += [table, Spacer(1, 35 * mm)]
    story.append(Paragraph("2026 年 11 月 25 日", ParagraphStyle(
        "date", fontName="SimSun", fontSize=11, leading=18,
        textColor=colors.black, alignment=TA_CENTER)))
    story.append(PageBreak())


def make_contents(story: list, page_numbers: dict[str, int]) -> None:
    story.append(BoldParagraph("目录", ParagraphStyle(
        "contents", fontName="SimSun", fontSize=30, leading=42,
        textColor=colors.black, alignment=TA_CENTER, spaceAfter=15)))
    sections = [
        "1. 项目概述", "2. 系统架构与部署编排",
        "3. DevOps 实践与版本身份", "4. B09 真实项目五阶段系统集成",
        "5. 可观测性与关联日志", "6. 容错、恢复与质量验证",
        "7. 问题定位与工程改进", "8. 成员贡献、复现与交付",
        "附录：证据索引",
    ]
    story.extend(TOCEntry(title, page_numbers.get(title, 0)) for title in sections)
    story.append(PageBreak())


def render_section(section: str, story: list, width: float) -> None:
    lines = section.strip().splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("## "):
            title = line[3:].strip()
            paragraph = BoldParagraph(clean_inline(title), heading)
            paragraph.toc_key = title
            story.append(paragraph)
            index += 1
            continue
        if line.startswith("### "):
            story.append(BoldParagraph(clean_inline(line[4:].strip()), subheading))
            index += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            story += [parse_table(table_lines, width), Spacer(1, 10)]
            continue
        paragraph = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and not lines[index].startswith(("## ", "### ", "|")):
            paragraph.append(lines[index].strip())
            index += 1
        story.append(Paragraph(clean_inline(" ".join(paragraph)), body))


def footer(canvas, doc):
    page = doc.page
    if page == 1:
        return
    canvas.saveState()
    canvas.setFont("SimSun", 9)
    canvas.setFillColor(colors.black)
    canvas.drawCentredString(A4[0] / 2, 32, str(page))
    canvas.restoreState()


class ReportDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section_pages: dict[str, int] = {}

    def afterFlowable(self, flowable):
        title = getattr(flowable, "toc_key", None)
        if title:
            self.section_pages[title] = self.page


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    parts = source.split("<!-- pagebreak -->")
    assert len(parts) == 10, f"expected cover, 8 sections, appendix; found {len(parts)}"
    margin = 50
    width = A4[0] - 2 * margin

    def build(path: Path, page_numbers: dict[str, int]) -> dict[str, int]:
        story: list = []
        make_cover(story)
        make_contents(story, page_numbers)
        for part in parts[1:]:
            render_section(part, story, width)
        doc = ReportDocTemplate(
            str(path), pagesize=A4, leftMargin=margin, rightMargin=margin,
            topMargin=55, bottomMargin=55, title="B09 Microservice Lab 期末项目报告",
            author="B09: 刘欣雨、黄新迪、丁卓、韩尚真",
        )
        doc.build(
            story,
            onFirstPage=footer,
            onLaterPages=footer,
            canvasmaker=partial(Canvas, initialFontName="SimSun", initialFontSize=13),
        )
        return doc.section_pages

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    draft = OUTPUT.with_name("B09-Microservice-Lab-draft.pdf")
    page_numbers = build(draft, {})
    final_numbers = build(OUTPUT, page_numbers)
    draft.unlink()
    assert final_numbers == page_numbers, (page_numbers, final_numbers)
    print(OUTPUT)


if __name__ == "__main__":
    main()
