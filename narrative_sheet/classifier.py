"""Local rule-based category suggestions for narrative documents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    """A category option shown in the Streamlit app."""

    key: str
    label: str
    description: str
    keywords: tuple[str, ...]


CATEGORIES: tuple[Category, ...] = (
    Category(
        key="main",
        label="主线剧情",
        description="主线章节、关键剧情、主线任务对白。",
        keywords=("主线", "章节", "chapter", "main", "story", "剧情", "序章", "终章"),
    ),
    Category(
        key="side",
        label="支线任务",
        description="支线任务、委托、探索事件。",
        keywords=("支线", "委托", "side", "quest", "任务", "探索", "奇遇"),
    ),
    Category(
        key="lore",
        label="世界观设定",
        description="世界观、术语、阵营、历史资料。",
        keywords=("世界观", "设定", "lore", "world", "阵营", "历史", "术语", "地名"),
    ),
    Category(
        key="npc",
        label="NPC对白",
        description="NPC 日常对白、闲聊、商店台词。",
        keywords=("npc", "对白", "闲聊", "商店", "角色", "村民", "dialogue", "dialog"),
    ),
    Category(
        key="system",
        label="系统文本",
        description="UI 文案、提示、成就、错误信息。",
        keywords=("系统", "提示", "system", "ui", "按钮", "错误", "成就", "说明"),
    ),
    Category(
        key="other",
        label="其他文档",
        description="暂未明确归类的文案。",
        keywords=(),
    ),
)

_CATEGORY_BY_KEY = {category.key: category for category in CATEGORIES}


def category_labels() -> list[str]:
    """Return category labels for UI select boxes."""

    return [category.label for category in CATEGORIES]


def category_label(key: str) -> str:
    """Return a display label for a category key."""

    return _CATEGORY_BY_KEY.get(key, _CATEGORY_BY_KEY["other"]).label


def category_key_from_label(label: str) -> str:
    """Return the stable category key for a display label."""

    for category in CATEGORIES:
        if category.label == label:
            return category.key
    return "other"


def suggest_category(title: str, markdown: str, filename: str = "") -> str:
    """Suggest a category key using only local keyword rules.

    The classifier intentionally avoids network calls and machine-learning
    services so the app can run on a normal office PC without external cloud
    dependencies.
    """

    haystack = f"{filename}\n{title}\n{markdown[:4000]}".casefold()
    scores: dict[str, int] = {}
    for category in CATEGORIES:
        if category.key == "other":
            continue
        score = sum(1 for keyword in category.keywords if keyword.casefold() in haystack)
        if score:
            scores[category.key] = score

    if not scores:
        return "other"
    return max(scores.items(), key=lambda item: (item[1], -_category_index(item[0])))[0]


def _category_index(key: str) -> int:
    for index, category in enumerate(CATEGORIES):
        if category.key == key:
            return index
    return len(CATEGORIES)
