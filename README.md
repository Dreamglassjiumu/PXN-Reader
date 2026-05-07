# narrative-sheet

`narrative-sheet` 是一个 Python CLI 工具，用于把游戏文案 Markdown 文件转换成策划易读的 Excel 和 Word 文档。

当前阶段提供项目骨架和最小可用版本：读取单个 `.md` 文件，解析标题层级和指定叙事块，并导出 `.xlsx` 与 `.docx`。

## 安装

建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 使用

```bash
python -m narrative_sheet input.md --xlsx output.xlsx --docx output.docx
```

如果已经执行 `pip install -e .`，也可以使用脚本命令：

```bash
narrative-sheet input.md --xlsx output.xlsx --docx output.docx
```

也可以只导出其中一种格式：

```bash
python -m narrative_sheet input.md --xlsx output.xlsx
python -m narrative_sheet input.md --docx output.docx
```

仓库内提供示例文件：

```bash
python -m narrative_sheet example/sample.md --xlsx output.xlsx --docx output.docx
```

## Markdown 格式

标题层级会映射为策划文档结构：

- `#`：chapter
- `##`：quest
- `###`：scene

支持的块类型：

```markdown
[NPC: 角色名]
这里是 NPC 对白。

[PlayerChoice]
1. 玩家选项 A
2. 玩家选项 B

[Narration]
这里是旁白。

[System]
这里是系统提示。

[Comment]
这里是备注，只会写入 Excel 的 note 字段，并在 Word 中显示为备注段落。
```

## Excel 字段

导出的 Excel 包含以下列：

- `source_file`
- `line_no`
- `chapter`
- `quest`
- `scene`
- `type`
- `speaker`
- `content`
- `note`

## 测试

```bash
python -m pytest
```
