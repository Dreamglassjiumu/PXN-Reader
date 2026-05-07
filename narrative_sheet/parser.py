"""Markdown parser for narrative script files."""

from __future__ import annotations

import re
from pathlib import Path

from .model import NarrativeRow

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
_BLOCK_RE = re.compile(r"^\[(NPC:\s*(?P<npc>[^\]]+)|PlayerChoice|Narration|System|Comment)\]\s*(?P<inline>.*)$")

_TYPE_LABELS = {
    "PlayerChoice": "player_choice",
    "Narration": "narration",
    "System": "system",
    "Comment": "comment",
}


class MarkdownParseError(ValueError):
    """Raised when a Markdown file cannot be parsed."""


def parse_markdown_file(path: str | Path) -> list[NarrativeRow]:
    """Read and parse a single Markdown file."""

    source_path = Path(path)
    if source_path.suffix.lower() != ".md":
        raise MarkdownParseError(f"Only .md files are supported: {source_path}")
    text = source_path.read_text(encoding="utf-8")
    return parse_markdown(text, source_file=source_path.name)


def parse_markdown(text: str, source_file: str = "") -> list[NarrativeRow]:
    """Parse supported headings and narrative blocks from Markdown text.

    Supported headings:
    - ``#`` chapter
    - ``##`` quest
    - ``###`` scene

    Supported blocks:
    - ``[NPC: name]``
    - ``[PlayerChoice]``
    - ``[Narration]``
    - ``[System]``
    - ``[Comment]``
    """

    rows: list[NarrativeRow] = []
    chapter = ""
    quest = ""
    scene = ""
    current: _CurrentBlock | None = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        stripped = line.strip()

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            current = _flush_current(rows, current, source_file, chapter, quest, scene)
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if level == 1:
                chapter = title
                quest = ""
                scene = ""
            elif level == 2:
                quest = title
                scene = ""
            else:
                scene = title
            continue

        block_match = _BLOCK_RE.match(stripped)
        if block_match:
            current = _flush_current(rows, current, source_file, chapter, quest, scene)
            token = block_match.group(1)
            inline = block_match.group("inline").strip()
            if token.startswith("NPC:"):
                current = _CurrentBlock(
                    line_no=line_no,
                    type="npc",
                    speaker=block_match.group("npc").strip(),
                    lines=[inline] if inline else [],
                )
            else:
                current = _CurrentBlock(
                    line_no=line_no,
                    type=_TYPE_LABELS[token],
                    speaker="",
                    lines=[inline] if inline else [],
                )
            continue

        if current is not None:
            if stripped:
                current.lines.append(stripped)
            else:
                current = _flush_current(rows, current, source_file, chapter, quest, scene)

    _flush_current(rows, current, source_file, chapter, quest, scene)
    return rows


class _CurrentBlock:
    def __init__(self, line_no: int, type: str, speaker: str, lines: list[str]) -> None:
        self.line_no = line_no
        self.type = type
        self.speaker = speaker
        self.lines = lines


def _flush_current(
    rows: list[NarrativeRow],
    current: _CurrentBlock | None,
    source_file: str,
    chapter: str,
    quest: str,
    scene: str,
) -> None:
    if current is None:
        return None

    content = "\n".join(current.lines).strip()
    note = content if current.type == "comment" else ""
    if current.type == "comment":
        content = ""

    rows.append(
        NarrativeRow(
            source_file=source_file,
            line_no=current.line_no,
            chapter=chapter,
            quest=quest,
            scene=scene,
            type=current.type,
            speaker=current.speaker,
            content=content,
            note=note,
        )
    )
    return None
