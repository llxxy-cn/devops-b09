"""Build the editable Microservice Lab report from the maintained Markdown source.

Update the table of contents in Word before exporting the matching PDF.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/final-report/MICROSERVICE-LAB-REPORT.md"
OUTPUT = ROOT / "docs/final-report/Microservice-Lab-期末项目报告-可编辑.docx"
MEMBERS = {"B1": "成员1", "B2": "成员2", "B3": "成员3", "B4": "成员4"}
NAMES = {"刘欣雨": "成员1", "黄新迪": "成员2", "丁卓": "成员3", "韩尚真": "成员4"}


def font(run, size: float | None = None, bold: bool | None = None) -> None:
    run.font.name = "宋体"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.color.rgb = RGBColor(0, 0, 0)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def set_style(style, size: float, bold: bool = False) -> None:
    style.font.name = "宋体"
    style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    disable_auto_spacing(style._element.get_or_add_pPr())


def disable_auto_spacing(ppr) -> None:
    for name in ("autoSpaceDE", "autoSpaceDN"):
        item = ppr.find(qn("w:" + name))
        if item is None:
            item = OxmlElement("w:" + name)
            ppr.append(item)
        item.set(qn("w:val"), "0")


def border_table(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(qn("w:" + edge))
        if el is None:
            el = OxmlElement("w:" + edge)
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:color"), "000000")


def cell_margins(cell, top=100, start=95, bottom=100, end=95) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        item = margins.find(qn("w:" + side))
        if item is None:
            item = OxmlElement("w:" + side)
            margins.append(item)
        item.set(qn("w:w"), str(value))
        item.set(qn("w:type"), "dxa")


def mark_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)


def add_field(paragraph, instr: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = instr
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "右键更新目录"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for item in (begin, instruction, separate, text, end):
        run._r.append(item)
    font(run, 11.5)


def clean(text: str) -> str:
    # Citation details live in the final evidence index; inline workstream codes
    # are removed from the report narrative.
    text = re.sub(r"\[E[1-4](?:[–、]E?[1-4])*\]", "", text)
    text = text.replace("B09 仓库 `https://github.com/llxxy-cn/devops-b09`", "本组项目仓库")
    text = text.replace("标签环境为 Compose 项目 `b09-ms-rc-5338183`，", "标签环境通过Compose部署，")
    text = text.replace("使用独立项目 `b09-ms-b3-241880585` 和", "使用独立的Compose项目和")
    text = text.replace("B3 job_id / trace_id", "job_id与trace_id")
    text = text.replace("B3 PR", "成员3提交的PR").replace("B4 PR", "成员4提交的PR")
    text = re.sub(r"\bB([1-4])\b", lambda m: MEMBERS["B" + m.group(1)], text)
    for name, member in NAMES.items():
        text = text.replace(name, member)
        text = text.replace(f"{member} {member}", member)
    text = text.replace("第 3 节", "版本身份一节")
    text = text.replace("`fixtures/e11e12-b1-real`", "真实项目样例目录")
    text = text.replace("运行镜像别名为 `course-e11e12:e14-rc-5338183-b4`，", "")
    text = text.replace("本报告 PDF、", "本报告、")
    text = text.replace("B09", "本组").replace("`", "")
    text = re.sub(r"\s*→\s*", "→", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[A-Za-z0-9])", "", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"\s+([，。：；、）》])", r"\1", text)
    text = re.sub(r"([（《])\s+", r"\1", text)
    return text.strip()


def add_inline(paragraph, value: str, size: float | None = None) -> None:
    parts = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", value)
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            font(run, size or 11.5)
        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            font(run, size, True)
        else:
            run = paragraph.add_run(part)
            font(run, size)


def add_link(paragraph, label: str, path: str) -> None:
    target = "https://github.com/llxxy-cn/devops-b09/blob/main/" + quote(path, safe="/")
    rel_id = paragraph.part.relate_to(target, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), rel_id)
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "宋体")
    fonts.set(qn("w:eastAsia"), "宋体")
    properties.append(fonts)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    properties.append(color)
    run.append(properties)
    text = OxmlElement("w:t")
    text.text = label
    run.append(text)
    link.append(run)
    paragraph._p.append(link)


def add_table(doc, markdown: list[str]) -> None:
    rows = [list(map(clean, line.strip().strip("|").split("|"))) for line in markdown]
    rows = [r for r in rows if not all(re.fullmatch(r"[-: ]+", x) for x in r)]
    if rows[0][0] == "成员":
        rows = [
            ["成员", "负责内容", "可核对产物"],
            ["成员1", "真实项目与E13交叉联调", "C/Make基线；6条依赖修复及6/6逐边验证；C2/C3拒绝与恢复；A09签收及合并后回归；E14五阶段请求、补丁与复验"],
            ["成员2", "样例部署与专项验证", "两轮Compose部署、同机隔离复现、超时恢复与幂等记录"],
            ["成员3", "E13门禁与监控", "依赖及三项目复验、C6门禁、四服务指标、面板与三阶段日志"],
            ["成员4", "容错与质量验收", "有界重试、错误码、故障恢复复测、报告与提交包"],
        ]
    if rows[0][0] == "责任与场景":
        rows[1][1] = rows[1][1].replace("（v0.9-rc）", "")
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.autofit = False
    border_table(table)
    if rows[0][0] == "成员":
        widths = (Cm(2.2), Cm(4.2), Cm(9.2))
    elif rows[0][0] == "阶段":
        widths = (Cm(2.5), Cm(8.5), Cm(4.6))
    elif len(rows[0]) == 3:
        widths = (Cm(3.0), Cm(8.4), Cm(4.2))
    else:
        widths = (Cm(4.2), Cm(11.4))
    for i, row in enumerate(rows):
        cant_split = OxmlElement("w:cantSplit")
        table.rows[i]._tr.get_or_add_trPr().append(cant_split)
        for j, value in enumerate(row):
            if rows[0][0] == "阶段" and j == 1 and i > 0:
                value = value.replace(" / ", "\n").replace("/", "\n", 1)
            cell = table.cell(i, j)
            cell.width = widths[j]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell_margins(cell)
            p = cell.paragraphs[0]
            p.style = "Table Text"
            p.paragraph_format.first_line_indent = Pt(0)
            font_size = 10.5 if rows[0][0] == "成员" else (9 if len(rows[0]) == 3 else 10)
            add_inline(p, value, font_size)
            if rows[0][0] == "成员" and j == 0 and i < len(rows) - 1:
                p.paragraph_format.keep_with_next = True
            if i == 0:
                for run in p.runs:
                    run.bold = True
        if i == 0:
            mark_header(table.rows[i])
    doc.add_paragraph(style="After Table")


def add_evidence_index(doc) -> None:
    entries = [
        ("成员1", "E13合并后回归包22,261,646字节，SHA256：23753210e75b0892663c35e052d7575cd5d00c042ef6ed82c606b9bbdb2abe89；原交付由A09于2026年11月23日签收，补充回归不替换原签收对象。E14标签环境真实项目五阶段完整包4,959,089字节，SHA256：2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e。", "docs/students/241880481/e13-e14/POST-MERGE-REGRESSION-20261124.md"),
        ("成员2", "E13超时、错误补丁、恢复和幂等专项包15,620,441字节，SHA256：e7e4a3bebe62e3e8306a548a033831e3121edb8bd0919886ad4e6688824a00d6；教学样例两轮部署与同机隔离复现补充包118,136字节，SHA256：8de8a205db69f5cd3faf02b9a8c4df8910f4374658afebd1fdc4e278a02f3445。", "docs/students/241880359/e13-b2-recheck-298ff136/TEST_REPORT.md"),
        ("成员3", "四服务监控记录、PromQL、关联日志、八张截图和完整证据包；SHA256：2dfe80765cdf6ab24833188c22d7edb045cc1a4b75ad5e09b8b23e5a972cb918。", "docs/students/241880585/microservice/可观测性报告.md"),
        ("成员4", "容错与质量复测记录、仓库完整性记录和完整证据包；SHA256：3ef9eb5e1c8da342c0d021e9a14de4ba6b39a3943527eb8ec87f1728e19936fd。", "docs/students/241880556/e13-e14-b4/MICROSERVICE-LAB-B4-QUALITY.md"),
    ]
    for name, detail, path in entries:
        p = doc.add_paragraph(style="Evidence Entry")
        add_inline(p, f"{name}（", 10.5)
        add_link(p, "E13回归" if name == "成员1" else ("E13记录" if name == "成员2" else "仓库记录"), path)
        if name == "成员1":
            add_inline(p, "、", 10.5)
            add_link(p, "正式联调", "docs/students/241880481/e13-e14/formal/README.md")
            add_inline(p, "、", 10.5)
            add_link(p, "A09签收", "evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md")
            add_inline(p, "、", 10.5)
            add_link(p, "E14记录", "docs/students/241880556/e13-e14-b4/MICROSERVICE-LAB-FINAL.md")
        if name == "成员2":
            add_inline(p, "、", 10.5)
            add_link(p, "部署记录", "docs/students/241880359/microservice-deploy/PACKAGE.md")
        add_inline(p, clean(f"）：{detail}"), 10.5)


def main() -> None:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(2.25), Cm(2.1)
    sec.left_margin, sec.right_margin = Cm(2.7), Cm(2.7)
    sec.header_distance, sec.footer_distance = Cm(0.8), Cm(1.0)
    sec.different_first_page_header_footer = True

    styles = doc.styles
    set_style(styles["Normal"], 12)
    styles["Normal"].paragraph_format.line_spacing = 1.25
    styles["Normal"].paragraph_format.space_after = Pt(7)
    styles["Normal"].paragraph_format.first_line_indent = Pt(24)
    set_style(styles["Title"], 24, True)
    styles["Title"].paragraph_format.space_after = Pt(16)
    title_ppr = styles["Title"]._element.get_or_add_pPr()
    title_border = title_ppr.find(qn("w:pBdr"))
    if title_border is not None:
        title_ppr.remove(title_border)
    title_border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "nil")
    title_border.append(bottom)
    title_ppr.append(title_border)
    set_style(styles["Heading 1"], 16, True)
    styles["Heading 1"].paragraph_format.space_before = Pt(14)
    styles["Heading 1"].paragraph_format.space_after = Pt(9)
    styles["Heading 1"].paragraph_format.first_line_indent = Pt(0)
    styles["Heading 1"].paragraph_format.keep_with_next = True
    for name, size in (("Table Text", 10), ("After Table", 2), ("TOC Entry", 11.5), ("Evidence Entry", 10.5)):
        if name not in styles:
            styles.add_style(name, 1)
        set_style(styles[name], size)
    styles["Table Text"].paragraph_format.space_after = Pt(0)
    styles["Table Text"].paragraph_format.line_spacing = 1.15
    styles["After Table"].paragraph_format.space_after = Pt(2)
    styles["TOC Entry"].paragraph_format.first_line_indent = Pt(0)
    styles["TOC Entry"].paragraph_format.line_spacing = 1.1
    styles["TOC Entry"].paragraph_format.space_after = Pt(7)
    styles["Evidence Entry"].paragraph_format.first_line_indent = Pt(21)
    styles["Evidence Entry"].paragraph_format.line_spacing = 1.12
    styles["Evidence Entry"].paragraph_format.space_after = Pt(4)
    if "TOC 1" not in [style.name for style in styles]:
        styles.add_style("TOC 1", WD_STYLE_TYPE.PARAGRAPH)
    set_style(styles["TOC 1"], 11.5)
    styles["TOC 1"].paragraph_format.space_after = Pt(7)
    styles["TOC 1"].paragraph_format.line_spacing = 1.1

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    disable_auto_spacing(footer._p.get_or_add_pPr())
    r = footer.add_run("第")
    font(r, 9)
    add_field(footer, " PAGE ")
    r = footer.add_run("页")
    font(r, 9)

    settings = doc.settings.element
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    settings.append(update)
    for name in ("hideSpellingErrors", "hideGrammaticalErrors"):
        item = OxmlElement("w:" + name)
        item.set(qn("w:val"), "true")
        settings.append(item)

    # The cover provides the sole name-to-member-number mapping.
    for _ in range(3):
        doc.add_paragraph()
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(title, "Microservice Lab期末项目报告", 24)
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.first_line_indent = Pt(0)
    add_inline(meta, "2026年11月27日", 12)
    doc.add_paragraph()
    member = doc.add_table(rows=5, cols=3)
    member.autofit = False
    border_table(member)
    for i, pair in enumerate((("成员编号", "姓名", "学号"), ("成员1", "刘欣雨", "241880481"), ("成员2", "黄新迪", "241880359"), ("成员3", "丁卓", "241880585"), ("成员4", "韩尚真", "241880556"))):
        for j, value in enumerate(pair):
            cell = member.cell(i, j)
            cell.width = (Cm(3.6), Cm(5.6), Cm(6.4))[j]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell_margins(cell, 150, 120, 150, 120)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Pt(0)
            add_inline(p, value, 12)
            if i == 0:
                for run in p.runs:
                    run.bold = True
    doc.add_page_break()

    toc_title = doc.add_paragraph(style="Title")
    toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(toc_title, "目录", 24)
    doc.add_paragraph()
    toc = doc.add_paragraph(style="TOC Entry")
    toc.paragraph_format.tab_stops.add_tab_stop(Cm(15.6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    add_field(toc, ' TOC \\o "1-1" \\h \\z \\u ')
    doc.add_page_break()

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("## "):
            heading = re.sub(r"^\d+\.\s*", "", line[3:]).replace("附录：", "")
            heading = clean(heading)
            p = doc.add_paragraph(style="Heading 1")
            add_inline(p, heading, 16)
            if heading == "证据索引":
                add_evidence_index(doc)
                break
        elif line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            add_table(doc, table_lines)
            continue
        elif line and not line.startswith("# ") and not line.startswith("<!--") and not line.startswith("**项目组**") and not line.startswith("**组员**"):
            value = clean(line)
            if value:
                p = doc.add_paragraph(style="Normal")
                add_inline(p, value)
        i += 1

    doc.core_properties.title = "Microservice Lab期末项目报告"
    doc.core_properties.author = "刘欣雨、黄新迪、丁卓、韩尚真"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
