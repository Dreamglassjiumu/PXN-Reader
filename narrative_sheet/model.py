"""Data models for parsed narrative Markdown."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NarrativeRow:
    """A normalized row extracted from a narrative Markdown file."""

    source_file: str
    line_no: int
    chapter: str
    quest: str
    scene: str
    type: str
    speaker: str
    content: str
    note: str = ""
