"""PXN-Reader local Streamlit web application."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from narrative_sheet.classifier import (
    CATEGORIES,
    category_key_from_label,
    category_label,
    category_labels,
    suggest_category,
)
from narrative_sheet.database import DEFAULT_DATABASE_PATH, connect
from narrative_sheet.repository import (
    create_document,
    get_document,
    list_documents,
    read_markdown,
    soft_delete_document,
    update_document,
)

st.set_page_config(page_title="PXN Reader 文案中心", page_icon="📚", layout="wide")

STYLE = """
<style>
:root {
  --library-bg: #24170f;
  --library-panel: #f4ead5;
  --library-paper: #fff9eb;
  --library-line: #c8ae7f;
  --library-text: #2e2118;
  --library-muted: #6f5b45;
  --library-accent: #7c3f22;
}
.stApp {
  background:
    radial-gradient(circle at top left, rgba(157, 106, 58, 0.28), transparent 32rem),
    linear-gradient(135deg, #1d120c 0%, #382417 44%, #20130d 100%);
  color: var(--library-text);
}
.block-container { padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: #ead9b9; border-right: 1px solid var(--library-line); }
div[data-testid="stVerticalBlock"] > div:has(> .library-card) {
  background: var(--library-panel);
  border: 1px solid var(--library-line);
  border-radius: 18px;
  box-shadow: 0 18px 40px rgba(0,0,0,0.28);
  padding: 1.1rem 1.25rem;
}
.library-title {
  background: linear-gradient(135deg, #f8edd4, #dec494);
  border: 1px solid var(--library-line);
  border-radius: 22px;
  box-shadow: 0 18px 40px rgba(0,0,0,0.30);
  padding: 1.5rem 1.7rem;
  margin-bottom: 1.2rem;
}
.library-title h1 { color: #2e170c; margin: 0 0 .35rem; }
.library-title p { color: var(--library-muted); margin: 0; }
.library-card { display: none; }
.stButton button, .stDownloadButton button {
  border: 1px solid #8a633e;
  background: #7c3f22;
  color: #fff9eb;
  border-radius: 10px;
  font-weight: 600;
}
.stButton button:hover, .stDownloadButton button:hover {
  border-color: #5d2d18;
  background: #63311b;
  color: #fff9eb;
}
</style>
"""


def main() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)
    connect(DEFAULT_DATABASE_PATH)
    _render_header()
    _render_upload_panel()
    _render_document_library()


def _render_header() -> None:
    st.markdown(
        """
        <div class="library-title">
          <h1>PXN Reader 文案中心</h1>
          <p>本机运行的文案书库。上传 Markdown 后自动生成 Word 和 Excel，同事可通过局域网地址访问。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_upload_panel() -> None:
    st.markdown('<span class="library-card"></span>', unsafe_allow_html=True)
    st.subheader("上传文档")
    uploaded_file = st.file_uploader("上传文档（.md）", type=["md"], accept_multiple_files=False)
    if uploaded_file is None:
        st.caption("请选择一个 Markdown 文件。上传后会自动转换为 Word 和 Excel。")
        return

    markdown = uploaded_file.getvalue().decode("utf-8-sig")
    suggested_key = suggest_category(Path(uploaded_file.name).stem, markdown, uploaded_file.name)
    labels = category_labels()
    suggested_label = category_label(suggested_key)
    title = _title_from_markdown(markdown) or Path(uploaded_file.name).stem

    with st.form("upload_form"):
        st.write(f"分类建议：**{suggested_label}**")
        document_title = st.text_input("标题", value=title)
        selected_label = st.selectbox("手动选择分类", labels, index=labels.index(suggested_label))
        tags = st.text_input("标签", placeholder="可选，例如：第一章, 战斗前")
        submitted = st.form_submit_button("上传文档")

    if submitted:
        create_document(
            markdown,
            uploaded_file.name,
            title=document_title,
            category=category_key_from_label(selected_label),
            tags=tags,
        )
        st.success("上传完成，已生成 Word 和 Excel。")
        st.rerun()


def _render_document_library() -> None:
    st.sidebar.header("文档列表")
    search_title = st.sidebar.text_input("搜索标题", placeholder="输入标题关键字")
    category_options = ["全部"] + [category.label for category in CATEGORIES]
    selected_filter = st.sidebar.selectbox("按分类筛选", category_options)
    selected_category = "all" if selected_filter == "全部" else category_key_from_label(selected_filter)

    documents = list_documents(search_title=search_title, category=selected_category)
    st.markdown('<span class="library-card"></span>', unsafe_allow_html=True)
    st.subheader("文档列表")
    st.caption("可搜索标题、按分类筛选、查看更新时间，并下载 Word 或 Excel。")

    if not documents:
        st.info("当前没有符合条件的文档。")
        return

    for document in documents:
        with st.container(border=True):
            title_col, time_col, action_col = st.columns([4, 2, 3])
            with title_col:
                st.markdown(f"**{document.title}**")
                st.caption(f"分类：{document.category_label}　标签：{document.tags or '无'}")
            with time_col:
                st.write("查看更新时间")
                st.caption(document.updated_at)
            with action_col:
                word_col, excel_col, detail_col = st.columns(3)
                with word_col:
                    _download_button(
                        "下载 Word",
                        document.docx_path,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        f"word-{document.id}",
                    )
                with excel_col:
                    _download_button(
                        "下载 Excel",
                        document.xlsx_path,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        f"excel-{document.id}",
                    )
                with detail_col:
                    if st.button("查看详情", key=f"detail-{document.id}"):
                        st.session_state["selected_document_id"] = document.id

    selected_id = st.session_state.get("selected_document_id")
    if selected_id:
        _render_detail(int(selected_id))


def _render_detail(document_id: int) -> None:
    document = get_document(document_id)
    markdown = read_markdown(document)
    labels = category_labels()
    current_label = category_label(document.category)

    st.markdown('<span class="library-card"></span>', unsafe_allow_html=True)
    st.subheader("文档详情")
    st.write(f"标题：**{document.title}**")
    st.write(f"分类：{current_label}")
    st.write(f"更新时间：{document.updated_at}")

    with st.expander("编辑文档", expanded=True):
        with st.form(f"edit-form-{document.id}"):
            title = st.text_input("标题", value=document.title)
            selected_label = st.selectbox("分类", labels, index=labels.index(current_label))
            tags = st.text_input("标签", value=document.tags)
            edited_markdown = st.text_area("Markdown 内容", value=markdown, height=360)
            saved = st.form_submit_button("编辑文档")
        if saved:
            update_document(
                document.id,
                title=title,
                category=category_key_from_label(selected_label),
                tags=tags,
                markdown=edited_markdown,
            )
            st.success("保存完成，已重新生成 Word 和 Excel。")
            st.rerun()

    with st.expander("删除文档"):
        st.warning("删除文档会从列表中移除记录，但不会直接物理删除 storage/ 中的文件。")
        if st.button("删除文档", key=f"delete-{document.id}"):
            soft_delete_document(document.id)
            st.session_state.pop("selected_document_id", None)
            st.success("已删除文档。")
            st.rerun()


def _download_button(label: str, path: Path, mime: str, key: str) -> None:
    if path.is_file():
        st.download_button(label, path.read_bytes(), file_name=path.name, mime=mime, key=key)
    else:
        st.button(label, disabled=True, key=key)


def _title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.removeprefix("# ").strip()
    return ""


if __name__ == "__main__":
    main()
