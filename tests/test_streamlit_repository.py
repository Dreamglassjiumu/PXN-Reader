from pathlib import Path

from narrative_sheet.classifier import category_key_from_label, category_label, suggest_category
from narrative_sheet.repository import (
    create_document,
    list_documents,
    read_markdown,
    soft_delete_document,
    update_document,
)


SAMPLE_MARKDOWN = """# 主线第一章

## 进入图书馆

### 门厅

[Narration]
古老的门缓缓打开。
"""


def test_classifier_suggests_local_category():
    assert suggest_category("主线第一章", SAMPLE_MARKDOWN, "story.md") == "main"
    assert category_label("main") == "主线剧情"
    assert category_key_from_label("NPC对白") == "npc"


def test_repository_creates_exports_and_lists_documents(tmp_path):
    database_path = tmp_path / "data" / "pxn.sqlite3"
    storage_dir = tmp_path / "storage"

    document = create_document(
        SAMPLE_MARKDOWN,
        "story.md",
        title="主线第一章",
        category="main",
        tags="第一章, 图书馆",
        database_path=database_path,
        storage_dir=storage_dir,
    )

    assert document.id > 0
    assert document.markdown_path.is_file()
    assert document.docx_path.is_file()
    assert document.xlsx_path.is_file()
    assert read_markdown(document) == SAMPLE_MARKDOWN

    documents = list_documents(
        search_title="第一章", category="main", database_path=database_path, storage_dir=storage_dir
    )
    assert [item.id for item in documents] == [document.id]
    assert documents[0].category_label == "主线剧情"


def test_repository_updates_regenerates_and_soft_deletes(tmp_path):
    database_path = tmp_path / "data" / "pxn.sqlite3"
    storage_dir = tmp_path / "storage"
    document = create_document(
        SAMPLE_MARKDOWN,
        "story.md",
        database_path=database_path,
        storage_dir=storage_dir,
    )
    original_docx_mtime = document.docx_path.stat().st_mtime_ns
    edited_markdown = SAMPLE_MARKDOWN.replace("古老的门缓缓打开。", "书架之间传来脚步声。")

    updated = update_document(
        document.id,
        title="修订后的标题",
        category="lore",
        tags="修订",
        markdown=edited_markdown,
        database_path=database_path,
        storage_dir=storage_dir,
    )

    assert updated.title == "修订后的标题"
    assert updated.category == "lore"
    assert updated.tags == "修订"
    assert read_markdown(updated) == edited_markdown
    assert updated.docx_path.stat().st_mtime_ns >= original_docx_mtime

    soft_delete_document(updated.id, database_path=database_path)
    assert list_documents(database_path=database_path, storage_dir=storage_dir) == []
    assert updated.markdown_path.is_file()
    assert updated.docx_path.is_file()
    assert updated.xlsx_path.is_file()
