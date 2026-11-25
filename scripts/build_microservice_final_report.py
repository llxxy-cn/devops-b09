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

body = ParagraphStyle(
    "body", fontName="SimSun", fontSize=11.5, leading=20,
    textColor=colors.black, spaceAfter=12, splitLongWords=True,
)
heading = ParagraphStyle(
    "section", fontName="SimSun", fontSize=17, leading=26,
    textColor=colors.black, spaceAfter=16, keepWithNext=True,
)
small = ParagraphStyle(
    "small", fontName="SimSun", fontSize=9.5, leading=15,
    textColor=colors.black, splitLongWords=True,
)
table_head = ParagraphStyle(
    "tablehead", parent=small, leading=15,
)


def clean_inline(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = html.escape(value)
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
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
        [Paragraph(clean_inline(cell), table_head if index == 0 else small) for cell in row]
        for index, row in enumerate(rows)
    ]
    result = Table(data, colWidths=[width * part for part in fractions], repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.black),
    ]))
    return result


def make_cover(story: list) -> None:
    story.extend([
        Spacer(1, 50 * mm),
        Paragraph("B09 Microservice Lab", ParagraphStyle(
            "coverEnglish", fontName="SimSun", fontSize=23, leading=32,
            textColor=colors.black, alignment=TA_CENTER)),
        Spacer(1, 7 * mm),
        Paragraph("DevOps 课程期末项目报告", ParagraphStyle(
            "coverChinese", fontName="SimSun", fontSize=21, leading=30,
            textColor=colors.black, alignment=TA_CENTER)),
        Spacer(1, 38 * mm),
    ])
    names = [
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
    ]))
    story += [table, Spacer(1, 35 * mm)]
    story.append(Paragraph("2026 年 11 月 25 日", ParagraphStyle(
        "date", fontName="SimSun", fontSize=11, leading=18,
        textColor=colors.black, alignment=TA_CENTER)))
    story.append(PageBreak())


def make_contents(story: list) -> None:
    story.append(Paragraph("目录", ParagraphStyle(
        "contents", fontName="SimSun", fontSize=17, leading=26,
        textColor=colors.black, spaceAfter=22)))
    sections = [
        "1. 项目概述与验收范围", "2. 系统架构与部署编排",
        "3. DevOps 实践与版本身份", "4. B09 真实项目五阶段系统集成",
        "5. 可观测性：指标、面板与关联日志", "6. 容错、恢复与质量验证",
        "7. 问题定位与反思", "8. 成员贡献、复现与交付",
        "附录：证据索引与版本边界",
    ]
    for index, title in enumerate(sections):
        page = index + 3
        story.append(Paragraph(f"{clean_inline(title)}　······　{page}",
                               ParagraphStyle(f"toc{index}", parent=body,
                                              fontSize=11.5, leading=21, spaceAfter=10)))
    story += [Spacer(1, 16 * mm), Paragraph(
        "正文为第 1–8 节，共 8 页；封面、目录、附录不计入正文。每轮任务的实际被测提交、项目和 job/trace 分别标注。",
        body), PageBreak()]


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
            story.append(Paragraph(clean_inline(title), heading))
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
        while index < len(lines) and lines[index].strip() and not lines[index].startswith(("## ", "|")):
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


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    parts = source.split("<!-- pagebreak -->")
    assert len(parts) == 10, f"expected cover, 8 body pages, appendix; found {len(parts)}"
    margin = 50
    width = A4[0] - 2 * margin
    story: list = []
    make_cover(story)
    make_contents(story)
    for index, part in enumerate(parts[1:]):
        render_section(part, story, width)
        if index < len(parts) - 2:
            story.append(PageBreak())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=55, bottomMargin=55, title="B09 Microservice Lab 期末项目报告",
        author="B09: 刘欣雨、黄新迪、丁卓、韩尚真",
    )
    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
        canvasmaker=partial(Canvas, initialFontName="SimSun", initialFontSize=11.5),
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
