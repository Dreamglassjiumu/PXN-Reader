"""Static site generator for publishing narrative Markdown content.

The generator scans a ``content/`` directory, converts every Markdown file into
Excel and Word exports, copies Markdown files for browser viewing, and writes a
self-contained static ``public/index.html`` suitable for GitHub Pages.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .exporters import export_docx, export_xlsx
from .parser import parse_markdown_file

CATEGORY_LABELS = {
    "main": "主线剧情",
    "side": "支线任务",
    "lore": "世界观设定",
    "npc": "NPC对白",
    "system": "系统文本",
}


@dataclass(frozen=True)
class SiteFile:
    """Metadata for one generated content file entry."""

    category_key: str
    category_label: str
    source_path: Path
    relative_source: Path
    stem: str
    updated_at: datetime
    xlsx_path: Path
    docx_path: Path
    markdown_path: Path


def build_site(
    content_dir: str | Path = "content",
    public_dir: str | Path = "public",
    generated_at: datetime | None = None,
) -> list[SiteFile]:
    """Build the static narrative publishing site.

    Args:
        content_dir: Directory containing Markdown files grouped by category.
        public_dir: Destination directory for the generated static site.
        generated_at: Optional timestamp used by tests or callers that need a
            deterministic build time.

    Returns:
        A list of metadata entries for generated Markdown files.
    """

    content_root = Path(content_dir)
    public_root = Path(public_dir)
    exports_root = public_root / "exports"
    markdown_root = public_root / "markdown"

    if not content_root.exists():
        raise FileNotFoundError(f"Content directory does not exist: {content_root}")
    if not content_root.is_dir():
        raise NotADirectoryError(f"Content path is not a directory: {content_root}")

    if public_root.exists():
        shutil.rmtree(public_root)
    exports_root.mkdir(parents=True, exist_ok=True)
    markdown_root.mkdir(parents=True, exist_ok=True)

    markdown_files = sorted(content_root.rglob("*.md"))
    export_names = _unique_export_names(markdown_files, content_root)
    site_files: list[SiteFile] = []

    for markdown_file in markdown_files:
        relative_source = markdown_file.relative_to(content_root)
        category_key = relative_source.parts[0] if len(relative_source.parts) > 1 else "uncategorized"
        category_label = CATEGORY_LABELS.get(category_key, category_key)
        export_stem = export_names[markdown_file]
        xlsx_path = exports_root / f"{export_stem}.xlsx"
        docx_path = exports_root / f"{export_stem}.docx"
        markdown_path = markdown_root / relative_source
        markdown_path.parent.mkdir(parents=True, exist_ok=True)

        rows = parse_markdown_file(markdown_file)
        export_xlsx(rows, xlsx_path)
        export_docx(rows, docx_path)
        shutil.copy2(markdown_file, markdown_path)

        site_files.append(
            SiteFile(
                category_key=category_key,
                category_label=category_label,
                source_path=markdown_file,
                relative_source=relative_source,
                stem=export_stem,
                updated_at=datetime.fromtimestamp(markdown_file.stat().st_mtime, timezone.utc),
                xlsx_path=xlsx_path.relative_to(public_root),
                docx_path=docx_path.relative_to(public_root),
                markdown_path=markdown_path.relative_to(public_root),
            )
        )

    latest_content_time = max((site_file.updated_at for site_file in site_files), default=datetime.now(timezone.utc))
    build_time = generated_at or latest_content_time
    (public_root / "index.html").write_text(_render_index(site_files, build_time), encoding="utf-8")
    return site_files


def _unique_export_names(markdown_files: list[Path], content_root: Path) -> dict[Path, str]:
    stem_counts: dict[str, int] = {}
    for markdown_file in markdown_files:
        stem_counts[markdown_file.stem] = stem_counts.get(markdown_file.stem, 0) + 1

    names: dict[Path, str] = {}
    used_names: set[str] = set()
    for markdown_file in markdown_files:
        if stem_counts[markdown_file.stem] == 1:
            candidate = markdown_file.stem
        else:
            relative = markdown_file.relative_to(content_root).with_suffix("")
            candidate = "_".join(relative.parts)

        safe_candidate = _safe_filename(candidate)
        unique_candidate = safe_candidate
        suffix = 2
        while unique_candidate in used_names:
            unique_candidate = f"{safe_candidate}_{suffix}"
            suffix += 1
        used_names.add(unique_candidate)
        names[markdown_file] = unique_candidate
    return names


def _safe_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
    return safe or "untitled"


def _render_index(site_files: list[SiteFile], generated_at: datetime) -> str:
    categories = _categories_for(site_files)
    rows = [_file_to_view_model(site_file) for site_file in site_files]
    generated_label = generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows_json = json.dumps(rows, ensure_ascii=False)
    categories_json = json.dumps(categories, ensure_ascii=False)

    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>PXN Reader 文案中心</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7fb;
      --card: #ffffff;
      --text: #172033;
      --muted: #667085;
      --line: #e4e7ec;
      --brand: #4457ff;
      --brand-soft: #edf0ff;
      --shadow: 0 18px 50px rgba(23, 32, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: radial-gradient(circle at top left, #eef2ff 0, transparent 34rem), var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", sans-serif;
      line-height: 1.6;
    }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 48px 24px 64px; }}
    .hero {{ display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; margin-bottom: 28px; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3.25rem); letter-spacing: -0.04em; }}
    .subtitle, .updated {{ color: var(--muted); margin: 0; }}
    .panel {{ background: rgba(255,255,255,0.82); border: 1px solid var(--line); border-radius: 24px; box-shadow: var(--shadow); backdrop-filter: blur(16px); }}
    .filters {{ padding: 18px; margin-bottom: 18px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
    .filter-label {{ color: var(--muted); font-weight: 600; margin-right: 4px; }}
    button.filter {{
      border: 1px solid var(--line); background: #fff; color: var(--text); border-radius: 999px;
      padding: 8px 14px; cursor: pointer; font-weight: 650; transition: all .16s ease;
    }}
    button.filter:hover, button.filter.active {{ border-color: var(--brand); background: var(--brand-soft); color: var(--brand); }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 860px; }}
    th, td {{ padding: 16px 18px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: middle; }}
    th {{ color: var(--muted); font-size: 0.88rem; font-weight: 700; background: #fbfcff; }}
    tbody tr:hover {{ background: #fbfcff; }}
    tbody tr:last-child td {{ border-bottom: 0; }}
    .badge {{ display: inline-flex; align-items: center; border-radius: 999px; background: var(--brand-soft); color: var(--brand); padding: 4px 10px; font-size: .86rem; font-weight: 700; }}
    .filename {{ font-weight: 700; }}
    .path {{ color: var(--muted); font-size: .9rem; }}
    a.download {{ color: var(--brand); text-decoration: none; font-weight: 700; }}
    a.download:hover {{ text-decoration: underline; }}
    .empty {{ text-align: center; color: var(--muted); padding: 36px 16px; }}
    @media (max-width: 720px) {{ .hero {{ display: block; }} .updated {{ margin-top: 12px; }} .page {{ padding: 32px 16px 48px; }} }}
  </style>
</head>
<body>
  <main class=\"page\">
    <section class=\"hero\">
      <div>
        <h1>PXN Reader 文案中心</h1>
        <p class=\"subtitle\">从 content/ 自动生成的静态文案发布站，支持 Excel、Word 与 Markdown 查看。</p>
      </div>
      <p class=\"updated\">最近更新时间：<strong>{html.escape(generated_label)}</strong></p>
    </section>

    <section class=\"panel filters\" aria-label=\"分类筛选区\">
      <span class=\"filter-label\">分类筛选</span>
      <button class=\"filter active\" type=\"button\" data-category=\"all\">全部</button>
      <span id=\"categoryButtons\"></span>
    </section>

    <section class=\"panel table-wrap\">
      <table>
        <thead>
          <tr>
            <th>分类</th>
            <th>文件名</th>
            <th>更新时间</th>
            <th>Excel 下载</th>
            <th>Word 下载</th>
            <th>Markdown 查看</th>
          </tr>
        </thead>
        <tbody id=\"fileRows\"></tbody>
      </table>
      <div class=\"empty\" id=\"emptyState\" hidden>当前分类下暂无文案。</div>
    </section>
  </main>

  <script>
    const files = {rows_json};
    const categories = {categories_json};
    const buttonsRoot = document.getElementById('categoryButtons');
    const rowsRoot = document.getElementById('fileRows');
    const emptyState = document.getElementById('emptyState');

    categories.forEach((category) => {{
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'filter';
      button.dataset.category = category.key;
      button.textContent = `${{category.label}} (${{category.count}})`;
      buttonsRoot.appendChild(button);
    }});

    function renderRows(category) {{
      const visible = category === 'all' ? files : files.filter((file) => file.categoryKey === category);
      rowsRoot.innerHTML = '';
      visible.forEach((file) => {{
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><span class=\"badge\">${{escapeHtml(file.categoryLabel)}}</span></td>
          <td><div class=\"filename\">${{escapeHtml(file.name)}}</div><div class=\"path\">${{escapeHtml(file.path)}}</div></td>
          <td>${{escapeHtml(file.updatedAt)}}</td>
          <td><a class=\"download\" href=\"${{encodeURI(file.xlsx)}}\" download>下载 .xlsx</a></td>
          <td><a class=\"download\" href=\"${{encodeURI(file.docx)}}\" download>下载 .docx</a></td>
          <td><a class=\"download\" href=\"${{encodeURI(file.markdown)}}\" target=\"_blank\" rel=\"noopener\">查看 .md</a></td>
        `;
        rowsRoot.appendChild(row);
      }});
      emptyState.hidden = visible.length !== 0;
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>\"']/g, (char) => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;'
      }}[char]));
    }}

    document.querySelectorAll('button.filter').forEach((button) => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('button.filter').forEach((item) => item.classList.remove('active'));
        button.classList.add('active');
        renderRows(button.dataset.category);
      }});
    }});

    renderRows('all');
  </script>
</body>
</html>
"""


def _categories_for(site_files: list[SiteFile]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for site_file in site_files:
        counts[site_file.category_key] = counts.get(site_file.category_key, 0) + 1
        labels[site_file.category_key] = site_file.category_label
    def category_order(key: str) -> tuple[int, str]:
        if key in CATEGORY_LABELS:
            return (list(CATEGORY_LABELS).index(key), key)
        return (999, key)

    return [
        {"key": key, "label": labels[key], "count": counts[key]}
        for key in sorted(counts, key=category_order)
    ]


def _file_to_view_model(site_file: SiteFile) -> dict[str, str]:
    return {
        "categoryKey": site_file.category_key,
        "categoryLabel": site_file.category_label,
        "name": site_file.relative_source.name,
        "path": site_file.relative_source.as_posix(),
        "updatedAt": site_file.updated_at.strftime("%Y-%m-%d %H:%M UTC"),
        "xlsx": site_file.xlsx_path.as_posix(),
        "docx": site_file.docx_path.as_posix(),
        "markdown": site_file.markdown_path.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the PXN Reader static narrative publishing site.")
    parser.add_argument("--content-dir", type=Path, default=Path("content"), help="Markdown content directory.")
    parser.add_argument("--public-dir", type=Path, default=Path("public"), help="Static site output directory.")
    args = parser.parse_args()
    site_files = build_site(args.content_dir, args.public_dir)
    print(f"Generated {len(site_files)} Markdown file(s) into {args.public_dir}")


if __name__ == "__main__":
    main()
