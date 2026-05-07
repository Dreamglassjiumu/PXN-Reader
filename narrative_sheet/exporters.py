"""Export parsed narrative rows to Excel and Word documents.

The exporters write minimal Office Open XML packages with the Python standard
library. This keeps the first milestone lightweight while still producing files
that spreadsheet and word-processing applications can open.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from .model import NarrativeRow

EXCEL_FIELDS = [
    "source_file",
    "line_no",
    "chapter",
    "quest",
    "scene",
    "type",
    "speaker",
    "content",
    "note",
]

_TYPE_TITLES = {
    "npc": "NPC 对白",
    "player_choice": "玩家选项",
    "narration": "旁白",
    "system": "系统提示",
    "comment": "备注",
}


def export_xlsx(rows: Iterable[NarrativeRow], output_path: str | Path) -> None:
    """Export narrative rows to a minimal Excel workbook."""

    table = [EXCEL_FIELDS]
    table.extend([[getattr(row, field) for field in EXCEL_FIELDS] for row in rows])

    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _xlsx_content_types())
        archive.writestr("_rels/.rels", _xlsx_root_rels())
        archive.writestr("xl/workbook.xml", _xlsx_workbook())
        archive.writestr("xl/_rels/workbook.xml.rels", _xlsx_workbook_rels())
        archive.writestr("xl/worksheets/sheet1.xml", _xlsx_sheet(table))
        archive.writestr("xl/styles.xml", _xlsx_styles())


def export_docx(rows: Iterable[NarrativeRow], output_path: str | Path) -> None:
    """Export narrative rows to a minimal Word document."""

    body_parts: list[str] = []
    previous_chapter = previous_quest = previous_scene = None

    for row in rows:
        if row.chapter and row.chapter != previous_chapter:
            body_parts.append(_docx_heading(row.chapter, 1))
            previous_chapter = row.chapter
            previous_quest = None
            previous_scene = None
        if row.quest and row.quest != previous_quest:
            body_parts.append(_docx_heading(row.quest, 2))
            previous_quest = row.quest
            previous_scene = None
        if row.scene and row.scene != previous_scene:
            body_parts.append(_docx_heading(row.scene, 3))
            previous_scene = row.scene

        body_parts.append(_docx_paragraph(row))

    document_xml = _docx_document("".join(body_parts))

    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _docx_content_types())
        archive.writestr("_rels/.rels", _docx_root_rels())
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", _docx_styles())


def _xlsx_sheet(table: list[list[object]]) -> str:
    rows_xml = []
    for row_index, values in enumerate(table, start=1):
        cells = []
        for col_index, value in enumerate(values, start=1):
            reference = f"{_column_name(col_index)}{row_index}"
            style = ' s="1"' if row_index == 1 else ""
            text = escape(str(value or ""))
            cells.append(f'<c r="{reference}" t="inlineStr"{style}><is><t>{text}</t></is></c>')
        rows_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>'
        f'{"".join(rows_xml)}'
        '</sheetData>'
        '</worksheet>'
    )


def _xlsx_content_types() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )


def _xlsx_root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )


def _xlsx_workbook() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Narrative" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )


def _xlsx_workbook_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )


def _xlsx_styles() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font/><font><b/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
        '</styleSheet>'
    )


def _docx_document(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body>'
        '</w:document>'
    )


def _docx_heading(text: str, level: int) -> str:
    return (
        '<w:p>'
        f'<w:pPr><w:pStyle w:val="Heading{level}"/></w:pPr>'
        f'<w:r><w:t>{escape(text)}</w:t></w:r>'
        '</w:p>'
    )


def _docx_paragraph(row: NarrativeRow) -> str:
    label = _TYPE_TITLES.get(row.type, row.type)
    if row.type == "npc" and row.speaker:
        text = f"[{label}] {row.speaker}: {row.content}"
    elif row.type == "comment":
        text = f"[{label}] {row.note}"
    else:
        text = f"[{label}] {row.content}"

    runs = "".join(f'<w:r><w:t>{escape(part)}</w:t></w:r>' if index == 0 else f'<w:r><w:br/><w:t>{escape(part)}</w:t></w:r>' for index, part in enumerate(text.split("\n")))
    return f'<w:p>{runs}</w:p>'


def _docx_content_types() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '</Types>'
    )


def _docx_root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )


def _docx_styles() -> str:
    styles = [
        ('Heading1', 'heading 1', 32, True),
        ('Heading2', 'heading 2', 28, True),
        ('Heading3', 'heading 3', 24, True),
    ]
    style_xml = []
    for style_id, name, size, bold in styles:
        bold_xml = '<w:b/>' if bold else ''
        style_xml.append(
            f'<w:style w:type="paragraph" w:styleId="{style_id}">'
            f'<w:name w:val="{name}"/><w:rPr>{bold_xml}<w:sz w:val="{size}"/></w:rPr>'
            '</w:style>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'{"".join(style_xml)}'
        '</w:styles>'
    )


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name
