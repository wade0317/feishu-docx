<div align="center">

# feishu-docx

<p align="center">
  <em>飞书知识库导出、写入与云空间管理工具 | 支持 Markdown、公众号导入、CLI、TUI、OAuth 2.0</em>
</p>

[![PyPI version](https://badge.fury.io/py/feishu-docx.svg)](https://badge.fury.io/py/feishu-docx)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <strong>中文</strong> | <a href="https://github.com/leemysw/feishu-docx/blob/main/README.md">English</a>
</p>
</div>

<div align="center">
<img src="https://raw.githubusercontent.com/leemysw/feishu-docx/main/docs/tui.png" alt="feishu-docx TUI" width="90%">
</div>

---

## 🎯 为什么选择 feishu-docx？

**让 AI Agent 读懂、写入并管理你的飞书知识库。**

- 🤖 **为AI而生** — 完美支持 Claude/GPT Skills，让 Agent 直接查询飞书文档
- 📄 **全面覆盖** — 云文档、电子表格、多维表格、知识库、公众号文章
- ✍️ **支持写回** — 创建文档、追加内容、更新指定 Block
- ☁️ **云空间管理** — 列文件、删文件、权限管理、批量清空
- 🔐 **自动授权** — 一次授权，Token 自动刷新，告别手动管理
- 🎨 **双重界面** — CLI 命令行 + TUI 终端图形界面，任君选择
- 📦 **开箱即用** — `pip install` 即可使用，零配置开始导出

---

## ⚡ 30秒快速开始

```bash
# 安装
pip install feishu-docx

# 配置凭证（只需一次）
feishu-docx config set --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET

# 导出！（自动获取 tenant_access_token，无需 OAuth 授权）
feishu-docx export "https://my.feishu.cn/wiki/KUIJwaBuGiwaSIkkKJ6cfVY8nSg"

# 直接从公众号抓取并创建飞书文档
feishu-docx create --url "https://mp.weixin.qq.com/s/xxxxx"

# Mermaid fenced code block 会自动写入为飞书画板
feishu-docx create "系统设计" -c $'```mermaid\nflowchart TD\nA --> B\n```'

# 管理应用云空间中的文档
feishu-docx drive ls --type docx

# 可选：使用 OAuth 模式获取用户级权限
# feishu-docx config set --auth-mode oauth && feishu-docx auth
```

---

## 🤖 Skills 支持

**让 Agent 直接访问你的飞书知识库！**

本项目已包含 Claude Skills 配置，位于 `.skills/feishu-docx/SKILL.md`。
Supports OpenCode, Claude Code, Codex, Cursor, and more.

将此 Skill 复制到你的 Agent 项目中，Claude 就能：

- 📖 读取飞书知识库作为上下文
- 🔍 搜索和引用内部文档
- 📝 *（规划中）* 将对话内容写入飞书

---

## ✨ 功能特性

| 功能           | 描述                         |
|--------------|----------------------------|
| 📄 云文档导出     | Docx → Markdown，保留格式、图片、表格 |
| 📊 电子表格导出    | Sheet → Markdown 表格        |
| 📋 多维表格导出    | Bitable → Markdown 表格      |
| 📚 知识库导出     | Wiki 节点自动解析，支持嵌套结构         |
| 🗂️ Wiki 批量导出 | 递归导出整个知识空间，保持目录层级结构        |
| ✍️ 文档写入      | 创建文档、追加 Markdown、更新指定 Block |
| 📰 公众号导入导出   | 公众号文章导出 Markdown / 直接导入飞书 |
| ☁️ 云空间管理    | 列文件、删文件、公开权限、成员权限、批量清空 |
| 🗄️ 数据库结构导出  | APaaS 数据库表结构导出为 Markdown   |
| 🖼️ 自动下载图片   | 图片保存到本地，Markdown 相对路径引用    |
| 🔐 认证方式     | 自动 tenant_access_token（推荐）/ OAuth 2.0 |
| 🎨 精美 TUI    | 基于 Textual 的终端图形界面         |

### ✅ 支持的Block

本工具目前支持导出以下飞书/ Lark 文档组件：

| 组件分类     | 具体内容                     | 支持情况 | 备注            |
|:---------|:-------------------------|:----:|:--------------|
| **基础文本** | 标题、正文、列表、任务(Todo)、代码块、引用 |  ✅   | 完美支持          |
| **文本样式** | 加粗、斜体、删除线、下划线、链接、@人员     |  ✅   | 完美支持          |
| **布局结构** | 分栏、高亮块、分割线               |  ✅   | 完美支持          |
| **表格**   | 原生表格                     |  ✅   | 支持导出为 md/html |
| **多媒体**  | 图片、画板                    |  ✅   | 画板将导出为图片      |
| **嵌入文档** | 电子表格、多维表格                |  ✅   | **仅导出文字内容**   |
| **特殊块**  | 同步块                      |  ⚠️  | 仅支持同文档内的原始块   |
| **文件**   | 附件                       |  ✅   | 文件名+临时下载链接    |

---

## 📖 使用方式

### 适用场景

- 导出飞书文档、Sheet、Bitable、Wiki 为 Markdown
- 抓取微信公众号文章并导出为 Markdown
- 抓取微信公众号文章并直接创建飞书文档
- 创建/追加/更新飞书文档内容
- 管理应用云空间或个人云空间中的文件和权限

### Mermaid 写回兼容性

Markdown 写入飞书文档时，` ```mermaid ` 代码块只会在飞书白板 API 实际支持时转成画板；如果类型不支持或解析失败，会自动降级为普通代码块，不会中断整篇文档同步。

以下结果基于 2026 年 3 月 19 日对文档 `https://nvj4o5b5sdu.feishu.cn/wiki/RbKnw4BfyiQytrki6I4cKqJVnbg` 的实测：

| Mermaid 类型 | 结果 | 说明 |
|---|---|---|
| `graph` / `flowchart` | ✅ 成功写入为画板 | 已实测 `graph LR`、`graph TD`、`graph TB` |
| `sequenceDiagram` | ✅ 成功写入为画板 | |
| `classDiagram` | ✅ 成功写入为画板 | |
| `stateDiagram-v2` | ✅ 成功写入为画板 | |
| `gantt` | ✅ 成功写入为画板 | |
| `pie` | ✅ 成功写入为画板 | |
| `erDiagram` | ✅ 成功写入为画板 | |
| `mindmap` | ✅ 成功写入为画板 | |
| `timeline` | ✅ 成功写入为画板 | |
| `journey` | ❌ 画板写入失败 | 飞书 API 明确返回 `type: journey not supported` |
| `gitgraph` | ❌ 画板写入失败 | 已自动降级为普通代码块 |
| `quadrantChart` | ❌ 画板写入失败 | 飞书 API 返回 Mermaid 词法解析错误 |

未列出的 Mermaid 类型，当前仓库还没有实测结果。当前实现优先保证整篇文档能同步成功，因此不支持的 Mermaid 会自动回退为代码块。

### CLI 命令行

```bash
# 导出单个文档到指定目录
feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs

# 批量导出整个知识空间（保持层级结构）
feishu-docx export-wiki-space <space_id_or_url> -o ./wiki_backup --max-depth 5

# 导出 APaaS 数据库结构
feishu-docx export-workspace-schema <workspace_id> -o ./database_schema.md

# 导出公众号文章为 Markdown
feishu-docx export-wechat "https://mp.weixin.qq.com/s/xxxxxx"

# 抓取公众号文章并创建飞书文档
feishu-docx create --url "https://mp.weixin.qq.com/s/xxxxxx"

# 在 tenant 模式下列出应用云空间中的文档
feishu-docx drive ls --type docx

# 查看和修改文档公开权限
feishu-docx drive perm-show "https://xxx.feishu.cn/docx/xxx"
feishu-docx drive perm-set "https://xxx.feishu.cn/docx/xxx" --share-entity anyone_can_view

# 双重确认后清空云空间文件
feishu-docx drive clear --type docx

# 使用 Token（临时）
feishu-docx export "URL" -t your_access_token

# 启动 TUI 界面
feishu-docx tui
```

### Python API

```python
from feishu_docx import FeishuExporter

# 初始化（使用 tenant_access_token，推荐）
exporter = FeishuExporter(app_id="xxx", app_secret="xxx")

# 导出单个文档
path = exporter.export("https://xxx.feishu.cn/wiki/xxx", "./output")

# 获取文档内容（不保存文件）
content = exporter.export_content("https://xxx.feishu.cn/docx/xxx")

# 批量导出整个知识空间
result = exporter.export_wiki_space(
    space_id="xxx",
    output_dir="./wiki_backup",
    max_depth=3,
)
print(f"导出 {result['exported']} 个文档到 {result['space_dir']}")
```

---

## 🔐 配置飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/) 创建应用
2. 添加重定向 URL：`http://127.0.0.1:9527/`
3. 申请以下权限：

```python
"docx:document:readonly"  # 查看云文档
"wiki:wiki:readonly"  # 查看知识库
"drive:drive:readonly"  # 查看云空间文件（图片下载）
"sheets:spreadsheet:readonly"  # 查看电子表格
"bitable:app:readonly"  # 查看多维表格
"board:whiteboard:node:read"  # 查看白板
"board:whiteboard:node:create"  # 创建白板节点（Mermaid 导入）
"contact:contact.base:readonly"  # 获取用户基本信息（@用户名称）
"offline_access"  # 离线访问（获取 refresh_token）
```

4. 保存凭证：

```bash
feishu-docx config set --app-id cli_xxx --app-secret xxx
```

### 🔑 认证模式

| | **Tenant 模式** (默认) | **OAuth 模式** |
|---|---|---|
| **Token 类型** | `tenant_access_token` | `user_access_token` |
| **配置方式** | 在[开放平台](https://open.feishu.cn/app)预配置权限 | OAuth 流程中动态申请权限 |
| **用户操作** | ✅ 自动获取，无需用户操作 | ❌ 需要在浏览器中授权 |
| **访问范围** | **应用**有权限的文档 | **用户**有权限的文档 |
| **适用场景** | 服务端自动化、AI Agent | 访问用户私有文档 |

**Tenant 模式（推荐）：**
```bash
# 一次性配置
feishu-docx config set --app-id xxx --app-secret xxx

# 导出（自动获取 tenant_access_token）
feishu-docx export "https://xxx.feishu.cn/docx/xxx"
```

> ⚠️ Tenant 模式需要在[飞书开放平台](https://open.feishu.cn/app) → 应用权限中预先配置文档权限。

**云空间管理（tenant / oauth）：**
```bash
# tenant 模式：管理应用云空间
feishu-docx drive ls --type docx

# oauth 模式：管理个人云空间
feishu-docx drive ls --auth-mode oauth --type docx
```

> 📎 飞书会根据 access token 类型区分云空间：`tenant_access_token` 对应应用云空间，`user_access_token` 对应个人云空间。应用云空间资源无法直接通过 UI 管理，需要使用 Drive/File API 管理。

**OAuth 模式（访问用户文档）：**
```bash
# 一次性配置
feishu-docx config set --app-id xxx --app-secret xxx --auth-mode oauth
feishu-docx auth  # 在浏览器中完成授权

# 导出（使用缓存的 user_access_token）
feishu-docx export "https://xxx.feishu.cn/docx/xxx"
```

> 💡 OAuth 模式在授权时动态申请权限，无需预先配置。

---

## 📖 命令参考

| 命令                              | 描述                      |
|---------------------------------|-------------------------|
| `export <URL>`                  | 导出单个文档为 Markdown        |
| `export-wiki-space <space_id>`  | 批量导出知识空间（保持目录层级）        |
| `export-workspace-schema <id>`  | 导出 APaaS 数据库结构         |
| `export-wechat <URL>`           | 导出公众号文章为 Markdown       |
| `create <title>`                | 创建飞书文档（支持 --url 导入公众号） |
| `drive ls`                      | 列出应用云空间 / 个人云空间文件   |
| `drive rm <TOKEN>`              | 删除云空间文件                 |
| `drive perm-show <TOKEN>`       | 查看公开权限                  |
| `drive perm-set <TOKEN>`        | 更新公开权限                  |
| `drive perm-members <TOKEN>`    | 列出权限成员                  |
| `drive perm-add <TOKEN>`        | 新增权限成员                  |
| `drive perm-update <TOKEN>`     | 更新权限成员                  |
| `drive perm-rm <TOKEN>`         | 删除权限成员                  |
| `drive clear`                   | 双重确认后批量清空文件            |
| `write <URL>`                   | 向文档追加 Markdown 内容      |
| `update <URL>`                  | 更新文档中指定 Block          |
| `auth`                          | OAuth 授权                |
| `tui`                           | TUI 交互界面                |
| `config set`                    | 设置凭证                    |
| `config show`                   | 查看配置                    |
| `config clear`                  | 清除缓存                    |

## 📚 文档结构建议

- `README`：总览、快速开始、命令索引
- `docs/*.md`：复杂主题的专题文档

当前已提供：

- [云空间管理](./docs/drive-management.md)

---

## 🛠️ 开发

```bash
git clone https://github.com/leemysw/feishu-docx.git
cd feishu-docx
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 🗺️ Roadmap

- [x] 云文档/表格/知识库导出
- [x] OAuth 2.0 + Token 刷新
- [x] TUI 终端界面
- [x] Claude Skills 支持
- [x] 批量导出整个知识空间
- [x] 写入飞书（创建/更新文档）

---

## 📜 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本历史。

## 📚 更多文档

- [云空间管理](./docs/drive-management.md)

---

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE)

---

**⭐ 如果这个项目对你有帮助，请给一个 Star！**
