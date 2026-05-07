"""Command line interface for narrative-sheet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporters import export_docx, export_xlsx
from .parser import parse_markdown_file


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "build-site":
        from .site_generator import main as build_site_main

        sys.argv = [sys.argv[0], *sys.argv[2:]]
        build_site_main()
        return

    parser = argparse.ArgumentParser(
        prog="python -m narrative_sheet",
        description="Convert game narrative Markdown into Excel and Word documents.",
    )
    parser.add_argument("input", type=Path, help="Input Markdown file (.md).")
    parser.add_argument("--xlsx", type=Path, help="Output Excel file (.xlsx).")
    parser.add_argument("--docx", type=Path, help="Output Word file (.docx).")
    args = parser.parse_args()

    if not args.xlsx and not args.docx:
        parser.error("At least one of --xlsx or --docx is required.")

    rows = parse_markdown_file(args.input)

    if args.xlsx:
        export_xlsx(rows, args.xlsx)
    if args.docx:
        export_docx(rows, args.docx)


if __name__ == "__main__":
    main()
