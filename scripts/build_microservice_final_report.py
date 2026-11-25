"""Render the B09 Microservice Lab report from its Markdown source.

Requires ReportLab and a CJK TrueType font. Run from the repository root:
  python scripts/build_microservice_final_report.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
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
FONT = Path("C:/Windows/Fonts/simhei.ttf")
if not FONT.exists():
    raise SystemExit(f"Chinese font unavailable: {FONT}")
pdfmetrics.registerFont(TTFont("SimHei", str(FONT)))

NAVY = colors.HexColor("#17324d")
BLUE = colors.HexColor("#176b91")
PALE = colors.HexColor("#eef5f8")
INK = colors.HexColor("#223443")
MUTED = colors.HexColor("#617485")

body = ParagraphStyle(
    "body", fontName="SimHei", fontSize=11, leading=19,
    textColor=INK, spaceAfter=12, splitLongWords=True,
)
heading = ParagraphStyle(
    "section", fontName="SimHei", fontSize=19, leading=27,
    textColor=NAVY, spaceAfter=17, keepWithNext=True,
)
small = ParagraphStyle(
    "small", fontName="SimHei", fontSize=9.1, leading=14,
    textColor=INK, splitLongWords=True,
)
table_head = ParagraphStyle(
    "tablehead", parent=small, textColor=colors.white, leading=12,
)


def clean_inline(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = html.escape(value)
    value = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r"<font color='#176b91'>\1</font>", value)
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
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#cbdde5")),
    ]))
    return result


class Architecture(Flowable):
    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 74

    def draw(self):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#8caebf"))
        c.setFillColor(PALE)
        boxes = [
            (0, 27, 105, "编排器"),
            (132, 27, 105, "四业务服务"),
            (264, 27, 105, "任务产物"),
            (396, 27, 105, "复验结果"),
        ]
        for x, y, w, label in boxes:
            c.roundRect(x, y, w, 38, 6, stroke=1, fill=1)
            c.setFillColor(NAVY)
            c.setFont("SimHei", 10)
            c.drawCentredString(x + w / 2, y + 13, label)
            c.setFillColor(PALE)
        c.setStrokeColor(BLUE)
        for x in [110, 242, 374]:
            c.line(x, 46, x + 16, 46)
            c.line(x + 12, 49, x + 16, 46)
            c.line(x + 12, 43, x + 16, 46)


def make_cover(story: list[Flowable]) -> None:
    story.extend([
        Spacer(1, 38 * mm),
        Paragraph("B09 Microservice Lab", ParagraphStyle(
            "coverEnglish", fontName="SimHei", fontSize=29, leading=36,
            textColor=NAVY, alignment=TA_CENTER)),
        Spacer(1, 10 * mm),
        Paragraph("DevOps 课程期末项目报告", ParagraphStyle(
            "coverChinese", fontName="SimHei", fontSize=25, leading=32,
            textColor=BLUE, alignment=TA_CENTER)),
        Spacer(1, 26 * mm),
        Paragraph("真实项目集成 · 微服务编排 · 可观测性 · 容错恢复", ParagraphStyle(
            "subtitle", fontName="SimHei", fontSize=12, leading=20,
            textColor=MUTED, alignment=TA_CENTER)),
        Spacer(1, 28 * mm),
    ])
    names = [
        ["B1", "刘欣雨", "241880481"],
        ["B2", "黄新迪", "241880359"],
        ["B3", "丁卓", "241880585"],
        ["B4", "韩尚真", "241880556"],
    ]
    table = Table(names, colWidths=[68, 150, 150], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "SimHei"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PALE, colors.white]),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story += [table, Spacer(1, 30 * mm)]
    story.append(Paragraph("2026 年 11 月 25 日 · 截止 2026 年 12 月 1 日", ParagraphStyle(
        "date", fontName="SimHei", fontSize=10, leading=17,
        textColor=MUTED, alignment=TA_CENTER)))
    story.append(PageBreak())


def make_contents(story: list[Flowable]) -> None:
    story.append(Paragraph("目录", ParagraphStyle(
        "contents", fontName="SimHei", fontSize=21, leading=28,
        textColor=NAVY, spaceAfter=18)))
    sections = [
        "1. 项目概述与验收范围", "2. 系统架构与部署编排",
        "3. DevOps 实践与版本身份", "4. B09 真实项目五阶段系统集成",
        "5. 可观测性：指标、面板与关联日志", "6. 容错、恢复与质量验证",
        "7. 问题定位与反思", "8. 成员贡献、复现与交付",
        "附录：证据索引与版本边界",
    ]
    for index, title in enumerate(sections):
        page = index + 3
        story.append(Paragraph(f"{clean_inline(title)} <font color='#617485'>······ {page}</font>",
                               ParagraphStyle(f"toc{index}", parent=body,
                                              fontSize=11, leading=20, spaceAfter=9)))
    story += [Spacer(1, 18 * mm), Paragraph(
        "正文为第 1–8 节，共 8 页；封面、目录、附录不计入正文。每轮任务的实际被测提交、项目和 job/trace 分别标注。",
        body), PageBreak()]


def render_section(section: str, story: list[Flowable], width: float) -> None:
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
            if title.startswith("2."):
                story += [Architecture(width), Spacer(1, 8)]
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
    canvas.setStrokeColor(colors.HexColor("#d2e0e7"))
    canvas.line(46, 46, A4[0] - 46, 46)
    canvas.setFont("SimHei", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(47, 31, "B09 Microservice Lab · 2026 秋")
    canvas.drawRightString(A4[0] - 47, 31, str(page))
    canvas.restoreState()


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    parts = source.split("<!-- pagebreak -->")
    assert len(parts) == 10, f"expected cover, 8 body pages, appendix; found {len(parts)}"
    margin = 47
    width = A4[0] - 2 * margin
    story: list[Flowable] = []
    make_cover(story)
    make_contents(story)
    for index, part in enumerate(parts[1:]):
        render_section(part, story, width)
        if index < len(parts) - 2:
            story.append(PageBreak())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=52, bottomMargin=60, title="B09 Microservice Lab 期末项目报告",
        author="B09: 刘欣雨、黄新迪、丁卓、韩尚真",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
