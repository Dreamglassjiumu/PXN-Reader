# PXN-Reader / narrative-sheet

PXN-Reader 现在可以作为本地 Streamlit Web 应用运行：你在自己的电脑上启动工具，文案组其他成员通过公司局域网 IP 访问，例如 `http://你的内网IP:8501`。

本项目不依赖 GitHub Pages、Streamlit Cloud、Supabase 或任何外部云服务；不依赖外部 CDN、外部字体、外部图片。上传、数据库、Word、Excel 都保存在本机目录中，适合在普通 Windows 电脑上运行。

原有单文件 CLI 和静态站生成命令仍然保留，已有测试也继续覆盖这些功能。

## 主要功能

- 网页上传 `.md` 文件。
- 上传后自动转换为 `.docx` 和 `.xlsx`。
- 自动给出分类建议，并允许用户手动选择分类。
- 文档列表支持：
  - 搜索标题
  - 按分类筛选
  - 查看更新时间
  - 下载 Word
  - 下载 Excel
- 支持查看文档详情。
- 支持编辑：
  - 标题
  - 分类
  - 标签
  - Markdown 内容
- 保存编辑后自动重新生成 Word 和 Excel。
- 支持软删除：删除后从列表隐藏，但不会直接物理删除文件。

## 本地数据目录

PXN-Reader 使用本机文件和 SQLite 保存数据：

```text
data/                         SQLite 数据库
storage/markdown/             上传或编辑后的 Markdown
storage/word/                 自动生成的 Word 文件
storage/excel/                自动生成的 Excel 文件
```

请定期备份 `data/` 和 `storage/` 目录。

## 安装

建议使用虚拟环境。Windows PowerShell 示例：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Mac / Linux 示例：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```


## 公司电脑离线安装（已有 Python，但不能访问 PyPI）

如果公司电脑已经安装 Python，但因为不能访问 PyPI 导致 `pip install -r requirements.txt` 失败，可以使用 GitHub Actions 生成的离线依赖包。离线包会包含项目源码、`offline_wheels/` 依赖目录、`install_offline.bat` 和 `start_pxn_reader.bat`。

### 生成并下载离线包

1. 在 GitHub 仓库页面打开 **Actions**。
2. 选择 **Package offline wheels** 工作流。
3. 点击 **Run workflow** 手动运行，或在 `requirements.txt` / 离线安装脚本变更后等待自动运行。
4. 工作流完成后，在运行详情页的 **Artifacts** 区域下载 `pxn-reader-offline-windows-python311`。
5. 将下载的 artifact 复制到公司电脑，并解压到任意本地目录。

### 在公司电脑安装和启动

1. 双击 `install_offline.bat`。脚本会使用当前电脑已有的 Python 创建 `.venv`，并执行离线安装：

   ```bat
   py -m venv .venv
   .venv\Scripts\python.exe -m pip install --no-index --find-links=offline_wheels -r requirements.txt
   ```

   `--no-index` 会禁止 pip 访问外网，只从解压目录中的 `offline_wheels/` 安装依赖。

2. 安装完成后，双击 `start_pxn_reader.bat` 启动 Streamlit 应用。脚本会执行：

   ```bat
   .venv\Scripts\python.exe -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
   ```

3. 本机浏览器访问：

   ```text
   http://localhost:8501
   ```

4. 同事在同一公司内网中访问：

   ```text
   http://你的内网IP:8501
   ```

## 如何本地启动

在仓库根目录执行：

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

启动后，本机浏览器可访问：

```text
http://localhost:8501
```

`--server.address 0.0.0.0` 的作用是允许局域网内其他电脑访问这台电脑上的 Streamlit 服务。

## 如何查看自己的内网 IP

### Windows

打开命令提示符或 PowerShell，执行：

```powershell
ipconfig
```

在当前使用的网络适配器下查找 `IPv4 地址`，常见格式类似：

```text
192.168.1.23
10.0.0.15
```

### Mac

可以在终端执行：

```bash
ifconfig
```

也可以打开系统网络设置，查看当前 Wi-Fi 或有线网络的 IP 地址。

## 同事如何访问

假设你的内网 IP 是 `192.168.1.23`，同事在同一公司内网中访问：

```text
http://192.168.1.23:8501
```

也就是：

```text
http://你的内网IP:8501
```

## 如果同事打不开，请检查

- 你的电脑是否睡眠或关机。
- Streamlit 是否还在运行。
- Windows 防火墙是否允许 Python 访问网络。
- 启动命令是否使用了 `--server.address 0.0.0.0`。
- `8501` 端口是否被公司网络或安全策略限制。
- 同事是否和你的电脑在同一个局域网或 VPN 网络中。

## 如何备份

定期备份以下目录即可：

```text
data/
storage/
```

恢复时，将备份的 `data/` 和 `storage/` 放回仓库根目录，再重新运行 Streamlit。

## 网页界面说明

界面采用“中世纪图书馆 / 古典书库”风格，并使用朴实清楚的功能文案：

- 上传文档
- 编辑文档
- 删除文档
- 下载 Word
- 下载 Excel
- 搜索标题
- 按分类筛选

所有样式都写在本地 `app.py` 中，不加载外部 CDN、字体或图片。

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


## 纯前端版本使用说明

仓库新增单文件网页工具 `PXN-Reader.html`，适合只需要本机双击使用、不能安装 Python、不能启动服务器、不能访问外网的文案整理场景。该版本不会删除或替代现有 Python / Streamlit 版本。

### 使用方式

1. 在文件管理器中双击打开 `PXN-Reader.html`。
2. 点击 **选择 Markdown 文件**，选择本地 `.md` 文件。
3. 文件内容会显示在 **Markdown 内容** 区域，也可以直接在该区域粘贴或修改 Markdown。
4. 点击 **开始解析**。
5. 在 **解析结果** 表格中检查结构化数据，并按需修改 **分类**。
6. 根据需要点击：
   - **导出 Word**：导出可用 Word 打开的 `.doc` 文件。
   - **导出 Excel**：导出可用 Excel 打开的 `.xls` 文件。
   - **复制阅读稿**：复制整理后的纯文本阅读稿。
   - **清空当前文档**：清空当前文件、文本和解析结果。

### 纯前端版本特点

- 不使用 Python。
- 不使用 Streamlit。
- 不需要服务器。
- 不引用外部 CDN、外部字体或外部图片。
- CSS 和 JavaScript 均内置在 `PXN-Reader.html` 中。
- 可在公司内网断网环境下打开使用。

### Markdown 解析规则

纯前端版本与现有工具保持相同的标题层级约定：

- `#`：章节 `chapter`
- `##`：任务 `quest`
- `###`：场景 `scene`

支持的文本块：

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
这里是备注。
```

解析后会生成以下核心字段：

- `source_file`
- `chapter`
- `quest`
- `scene`
- `type`
- `speaker`
- `content`
- `char_count`
- `content_id`

其中 `content_id` 会按解析顺序自动生成，例如 `TXT_000001`、`TXT_000002`。页面还会给出分类建议：主线剧情、支线任务、世界观设定、NPC对白、系统文本、其他，并允许手动修改。

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

## 本地生成静态站（保留）

如果仍需要在本机生成 `public/` 静态目录，可以执行：

```bash
python -m narrative_sheet build-site
```

也可以直接运行生成器模块：

```bash
python -m narrative_sheet.site_generator
```

该功能只在本机生成文件，不要求使用任何外部云服务。

## 测试

```bash
python -m pytest
```
