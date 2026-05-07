# PXN-Reader / narrative-sheet

`PXN-Reader` 现在可以作为“静态文案发布站”使用：团队只需要把 Markdown 文案放进 `content/`，GitHub Actions 会自动把文案转换为 Excel、Word，并生成可发布到 GitHub Pages 的 `public/` 静态网页目录。

原有单文件 CLI 仍然保留：你依旧可以把任意一个 `.md` 文件导出为 `.xlsx` 与 `.docx`。

## 安装

建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## content/ 文案目录

文案组把 Markdown 文件放在 `content/` 下，并按一级目录区分分类：

| 目录 | 页面显示分类 | 适合内容 |
| --- | --- | --- |
| `content/main/` | 主线剧情 | 主线章节、关键剧情、主线任务对白 |
| `content/side/` | 支线任务 | 支线任务、委托、探索事件 |
| `content/lore/` | 世界观设定 | 世界观、术语、阵营、历史资料 |
| `content/npc/` | NPC对白 | NPC 日常对白、闲聊、商店台词 |
| `content/system/` | 系统文本 | UI 文案、提示、成就、错误信息 |

仓库中已经提供三个示例文件：

```text
content/main/story_001.md
content/side/quest_001.md
content/lore/world_001.md
```

建议每个 Markdown 文件继续使用项目支持的叙事块格式，例如：

```markdown
# 第一章

## 主线任务

### 场景名

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

## 本地生成静态站

在仓库根目录执行：

```bash
python -m narrative_sheet build-site
```

也可以直接运行生成器模块：

```bash
python -m narrative_sheet.site_generator
```

命令会扫描 `content/` 下所有 `.md` 文件，并生成：

```text
public/index.html
public/exports/*.xlsx
public/exports/*.docx
public/markdown/**/*.md
```

生成后的 `public/index.html` 是纯 HTML/CSS/JavaScript 静态页面，不依赖后端服务器。你可以直接用浏览器打开，或用任意静态文件服务器预览：

```bash
python -m http.server 8000 --directory public
```

然后访问 <http://localhost:8000>。

## GitHub Pages 自动发布

仓库已新增 `.github/workflows/build-pages.yml`。当 `main` 分支收到 push 时，GitHub Actions 会自动：

1. 安装 `requirements.txt`。
2. 运行测试：`python -m pytest`。
3. 运行静态站生成命令：`python -m narrative_sheet build-site`。
4. 上传 `public/` 并部署到 GitHub Pages。

首次启用 GitHub Pages 时，请在 GitHub 仓库页面操作：

1. 打开 **Settings** → **Pages**。
2. 在 **Build and deployment** 的 **Source** 中选择 **GitHub Actions**。
3. 保存设置后，向 `main` 分支 push 一次，等待 Actions 完成。

## 团队成员如何访问页面

部署完成后，团队成员可以通过 GitHub Pages 地址访问文案中心：

```text
https://<组织或用户名>.github.io/<仓库名>/
```

例如仓库名为 `PXN-Reader` 时，地址通常类似：

```text
https://<组织或用户名>.github.io/PXN-Reader/
```

页面包含：

- 页面标题：`PXN Reader 文案中心`
- 最近更新时间
- 分类筛选区
- 文件列表表格
- 每个文件的分类、文件名、更新时间、Excel 下载、Word 下载、Markdown 查看

团队成员只需要访问页面并下载所需文件，不需要部署或运行服务器。

## 单文件 CLI 用法（保留）

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
