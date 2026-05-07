from pathlib import Path
import subprocess
import sys

from narrative_sheet.parser import MarkdownParseError, parse_markdown, parse_markdown_file


def test_parse_markdown_extracts_headings_and_blocks():
    markdown = """# Chapter A

## Quest A

### Scene A

[Narration]
The fog is thick.

[NPC: Alice]
Hello, traveler.

[PlayerChoice]
1. Ask about the fog.
2. Leave.

[System]
Quest updated.

[Comment]
Branch this scene later.
"""

    rows = parse_markdown(markdown, source_file="sample.md")

    assert len(rows) == 5
    assert rows[0].source_file == "sample.md"
    assert rows[0].line_no == 7
    assert rows[0].chapter == "Chapter A"
    assert rows[0].quest == "Quest A"
    assert rows[0].scene == "Scene A"
    assert rows[0].type == "narration"
    assert rows[0].content == "The fog is thick."

    assert rows[1].type == "npc"
    assert rows[1].speaker == "Alice"
    assert rows[1].content == "Hello, traveler."

    assert rows[2].type == "player_choice"
    assert rows[2].content == "1. Ask about the fog.\n2. Leave."

    assert rows[3].type == "system"
    assert rows[3].content == "Quest updated."

    assert rows[4].type == "comment"
    assert rows[4].content == ""
    assert rows[4].note == "Branch this scene later."


def test_parse_markdown_file_rejects_non_markdown(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("# Chapter", encoding="utf-8")

    try:
        parse_markdown_file(path)
    except MarkdownParseError as exc:
        assert "Only .md files" in str(exc)
    else:
        raise AssertionError("Expected MarkdownParseError")


def test_cli_generates_xlsx_and_docx(tmp_path):
    input_path = Path("example/sample.md")
    xlsx_path = tmp_path / "output.xlsx"
    docx_path = tmp_path / "output.docx"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "narrative_sheet",
            str(input_path),
            "--xlsx",
            str(xlsx_path),
            "--docx",
            str(docx_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert xlsx_path.is_file()
    assert xlsx_path.stat().st_size > 0
    assert docx_path.is_file()
    assert docx_path.stat().st_size > 0


def test_site_generator_builds_static_site(tmp_path):
    from datetime import datetime, timezone

    from narrative_sheet.site_generator import build_site

    content_dir = tmp_path / "content"
    (content_dir / "main").mkdir(parents=True)
    (content_dir / "side").mkdir(parents=True)
    (content_dir / "main" / "story_001.md").write_text(
        """# Chapter\n\n## Quest\n\n### Scene\n\n[Narration]\nHello from the main story.\n""",
        encoding="utf-8",
    )
    (content_dir / "side" / "quest_001.md").write_text(
        """# Side\n\n## Quest\n\n### Scene\n\n[NPC: Bob]\nNeed help?\n""",
        encoding="utf-8",
    )
    public_dir = tmp_path / "public"

    site_files = build_site(
        content_dir=content_dir,
        public_dir=public_dir,
        generated_at=datetime(2026, 5, 7, 12, 0, tzinfo=timezone.utc),
    )

    assert len(site_files) == 2
    assert (public_dir / "index.html").is_file()
    assert (public_dir / "exports" / "story_001.xlsx").is_file()
    assert (public_dir / "exports" / "story_001.docx").is_file()
    assert (public_dir / "exports" / "quest_001.xlsx").is_file()
    assert (public_dir / "exports" / "quest_001.docx").is_file()
    assert (public_dir / "markdown" / "main" / "story_001.md").is_file()

    html = (public_dir / "index.html").read_text(encoding="utf-8")
    assert "PXN Reader 文案中心" in html
    assert "最近更新时间" in html
    assert "分类筛选" in html
    assert "主线剧情" in html
    assert "支线任务" in html
    assert "story_001.md" in html
    assert "exports/story_001.xlsx" in html
    assert "markdown/main/story_001.md" in html


def test_build_site_command_preserves_existing_cli(tmp_path):
    public_dir = tmp_path / "public"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "narrative_sheet",
            "build-site",
            "--content-dir",
            "content",
            "--public-dir",
            str(public_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (public_dir / "index.html").is_file()
    assert (public_dir / "exports" / "story_001.xlsx").is_file()
