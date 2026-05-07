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
