<div align="center">

# feishu-docx

<p align="center">
  <em>Feishu knowledge base export, writing, and cloud-space management tool with Markdown, WeChat import, CLI, TUI, and OAuth 2.0</em><br>
</p>

[![PyPI version](https://badge.fury.io/py/feishu-docx.svg)](https://badge.fury.io/py/feishu-docx)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <a href="https://github.com/leemysw/feishu-docx/blob/main/README_zh.md">中文</a> | <strong>English</strong>
</p>

</div>

<div align="center">
<img src="https://raw.githubusercontent.com/leemysw/feishu-docx/main/docs/tui.png" alt="feishu-docx TUI" width="90%">
</div>

---

## 🎯 Why feishu-docx?

**Let AI Agents read, write, and manage your Feishu/Lark knowledge base.**

- 🤖 **Built for AI** — Works seamlessly with Claude/GPT Skills for document retrieval
- 📄 **Full Coverage** — Documents, Spreadsheets, Bitables, Wiki nodes, and WeChat articles
- ✍️ **Write Back Support** — Create docs, append content, and update specific blocks
- ☁️ **Cloud-Space Management** — List files, delete files, manage permissions, clear files safely
- 🔐 **Authentication** — One-time auth, automatic token refresh
- 🎨 **Dual Interface** — CLI + Beautiful TUI (Textual-based)
- 📦 **Zero Config** — `pip install` and start exporting

---

## ⚡ Quick Start (30 seconds)

```bash
# Install
pip install feishu-docx

# Configure credentials (one-time)
feishu-docx config set --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET

# Export! (auto-obtains tenant_access_token, no OAuth needed)
feishu-docx export "https://my.feishu.cn/wiki/KUIJwaBuGiwaSIkkKJ6cfVY8nSg"

# Create a Feishu doc directly from a WeChat article
feishu-docx create --url "https://mp.weixin.qq.com/s/xxxxx"

# Mermaid fenced code blocks are imported as Feishu whiteboards
feishu-docx create "System Design" -c $'```mermaid\nflowchart TD\nA --> B\n```'

# Manage app cloud-space documents
feishu-docx drive ls --type docx

# Optional: Use OAuth mode for user-level permissions
# feishu-docx config set --auth-mode oauth && feishu-docx auth
```


---

## 🤖 Skills Support

**Enable Agent to access your Feishu knowledge base directly!**

This project includes a Claude Skill at `.skills/feishu-docx/SKILL.md`.
Supports OpenCode, Claude Code, Codex, Cursor, and more.

Copy this Skill to your agent project, and Claude can:

- 📖 Read Feishu knowledge base as context
- 🔍 Search and reference internal documents
- 📝 *(Planned)* Write conversation content back to Feishu

---

## ✨ Features

| Feature                 | Description                                     |
|-------------------------|-------------------------------------------------|
| 📄 Document Export      | Docx → Markdown with formatting, images, tables |
| 📊 Spreadsheet Export   | Sheet → Markdown tables                         |
| 📋 Bitable Export       | Multidimensional tables → Markdown              |
| 📚 Wiki Export          | Auto-resolve wiki nodes                         |
| 🗂️ Wiki Batch Export   | Recursively export entire wiki space with hierarchy |
| ✍️ Document Writing    | Create docs, append Markdown, update specific blocks |
| 📰 WeChat Import/Export | Export WeChat articles or create Feishu docs from them |
| ☁️ Drive Management    | List files, delete files, manage permissions, clear files |
| 🗄️ Database Schema     | Export APaaS database structure to Markdown     |
| 🖼️ Auto Image Download | Images saved locally with relative paths        |
| 🔐 Auth                 | Auto tenant_access_token (recommended) or OAuth 2.0 |
| 🎨 Beautiful TUI        | Terminal UI powered by Textual                  |



### ✅ Supported Blocks

This tool currently supports exporting the following Feishu/Lark document components:

| Category       | Features                                                       | Status | Notes                                    |
|----------------|----------------------------------------------------------------|--------|------------------------------------------|
| **Basic Text** | Headings, Paragraphs, Lists, Tasks (Todo), Code Blocks, Quotes | ✅      | Fully Supported                          |
| **Formatting** | Bold, Italic, Strikethrough, Underline, Links, @Mentions       | ✅      | Fully Supported                          |
| **Layout**     | Columns, Callouts, Dividers                                    | ✅      | Fully Supported                          |
| **Tables**     | Native Tables                                                  | ✅      | Export to Markdown/HTML                  |
| **Media**      | Images, Drawing Boards                                         | ✅      | Drawing boards exported as images        |
| **Embedded**   | Spreadsheets (Sheets), Bitable                                 | ✅      | **Text content only**                    |
| **Special**    | Synced Blocks                                                  | ⚠️     | Original blocks within the same doc only |
| **Files**      | Attachments                                                    | ✅      | File name + download link                |

---

## 📖 Usage

### Use Cases

- Export Feishu docs, Sheets, Bitables, and Wiki nodes to Markdown
- Export a WeChat article to Markdown
- Create a Feishu doc directly from a WeChat article URL
- Create, append, or update Feishu document content
- Manage files and permissions in app cloud space or personal cloud space

### Mermaid Writeback Compatibility

When writing Markdown to Feishu docs, Mermaid fenced code blocks are imported through the whiteboard API only for diagram types that Feishu actually accepts. Unsupported or parser-failing Mermaid blocks are downgraded to normal code blocks instead of failing the whole document sync.

Verified against the document `https://nvj4o5b5sdu.feishu.cn/wiki/RbKnw4BfyiQytrki6I4cKqJVnbg` on March 19, 2026:

| Mermaid type | Result | Notes |
|---|---|---|
| `graph` / `flowchart` | ✅ Whiteboard import succeeded | Tested with `graph LR`, `graph TD`, `graph TB` |
| `sequenceDiagram` | ✅ Whiteboard import succeeded | |
| `classDiagram` | ✅ Whiteboard import succeeded | |
| `stateDiagram-v2` | ✅ Whiteboard import succeeded | |
| `gantt` | ✅ Whiteboard import succeeded | |
| `pie` | ✅ Whiteboard import succeeded | |
| `erDiagram` | ✅ Whiteboard import succeeded | |
| `mindmap` | ✅ Whiteboard import succeeded | |
| `timeline` | ✅ Whiteboard import succeeded | |
| `journey` | ❌ Whiteboard import failed | Feishu API reported `type: journey not supported` |
| `gitgraph` | ❌ Whiteboard import failed | Downgraded to a normal code block |
| `quadrantChart` | ❌ Whiteboard import failed | Feishu API returned Mermaid lexical parse error |

Types not listed above were not verified in this repository yet. Current implementation prefers successful document sync over strict whiteboard conversion, so unsupported Mermaid blocks fall back to code blocks.

### CLI

```bash
# Export single document to specific directory
feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs

# Batch export entire wiki space (preserves hierarchy)
feishu-docx export-wiki-space <space_id_or_url> -o ./wiki_backup --max-depth 5

# Export APaaS database schema
feishu-docx export-workspace-schema <workspace_id> -o ./database_schema.md

# Export WeChat article to Markdown
feishu-docx export-wechat "https://mp.weixin.qq.com/s/xxxxxx"

# Fetch a WeChat article and create a Feishu doc
feishu-docx create --url "https://mp.weixin.qq.com/s/xxxxxx"

# List app cloud-space documents in tenant mode
feishu-docx drive ls --type docx

# Manage public permission of a document
feishu-docx drive perm-show "https://xxx.feishu.cn/docx/xxx"
feishu-docx drive perm-set "https://xxx.feishu.cn/docx/xxx" --share-entity anyone_can_view

# Clear files in cloud space with double confirmation
feishu-docx drive clear --type docx

# Use token directly
feishu-docx export "URL" -t your_access_token

# Launch TUI
feishu-docx tui
```

### Python API

```python
from feishu_docx import FeishuExporter

# Initialize (uses tenant_access_token by default)
exporter = FeishuExporter(app_id="xxx", app_secret="xxx")

# Export single document
path = exporter.export("https://xxx.feishu.cn/wiki/xxx", "./output")

# Get content without saving
content = exporter.export_content("https://xxx.feishu.cn/docx/xxx")

# Batch export entire wiki space
result = exporter.export_wiki_space(
    space_id="xxx",
    output_dir="./wiki_backup",
    max_depth=3,
)
print(f"Exported {result['exported']} docs to {result['space_dir']}")
```

---

## 🔐 Feishu App Setup

1. Create app at [Feishu Open Platform](https://open.feishu.cn/)
2. Add redirect URL: `http://127.0.0.1:9527/`
3. Request permissions:

```python
"docx:document:readonly"  # 查看云文档
"wiki:wiki:readonly"  # 查看知识库
"drive:drive:readonly"  # 查看云空间文件（图片下载）
"sheets:spreadsheet:readonly"  # 查看电子表格
"bitable:app:readonly"  # 查看多维表格
"board:whiteboard:node:read"  # 查看白板
"board:whiteboard:node:create"  # Create whiteboard nodes (Mermaid import)
"contact:contact.base:readonly"  # 获取用户基本信息（@用户名称）
"offline_access"  # 离线访问（获取 refresh_token）
```

4. Save credentials:

```bash
feishu-docx config set --app-id cli_xxx --app-secret xxx
```

### 🔑 Authentication Modes

| | **Tenant Mode** (Default) | **OAuth Mode** |
|---|---|---|
| **Token Type** | `tenant_access_token` | `user_access_token` |
| **Setup** | Configure permissions in [Open Platform](https://open.feishu.cn/app) | Request permissions during OAuth flow |
| **User Interaction** | ✅ Automatic, no user action needed | ❌ Requires browser authorization |
| **Access Scope** | Documents the **app** has permission to | Documents the **user** has permission to |
| **Best For** | Server automation, AI Agents | Accessing user's private documents |

**Tenant Mode (Recommended for most cases):**
```bash
# One-time setup
feishu-docx config set --app-id xxx --app-secret xxx

# Export (auto-obtains tenant_access_token)
feishu-docx export "https://xxx.feishu.cn/docx/xxx"
```

> ⚠️ Tenant mode requires pre-configuring document permissions in [Feishu Open Platform](https://open.feishu.cn/app) → App Permissions.

**Cloud space management (tenant/user):**
```bash
# Tenant mode: manage files in app cloud space
feishu-docx drive ls --type docx

# OAuth mode: manage files in personal cloud space
feishu-docx drive ls --auth-mode oauth --type docx
```

> 📎 Feishu separates cloud space by token type: `tenant_access_token` maps to app cloud space, and `user_access_token` maps to personal cloud space. App cloud space resources cannot be managed from the UI and should be managed through Drive/File APIs.

**OAuth Mode (For user-level access):**
```bash
# One-time setup
feishu-docx config set --app-id xxx --app-secret xxx --auth-mode oauth
feishu-docx auth  # Opens browser for authorization

# Export (uses cached user_access_token)
feishu-docx export "https://xxx.feishu.cn/docx/xxx"
```

> 💡 OAuth mode requests permissions during the authorization flow, no pre-configuration needed.

---

## 📖 Commands

| Command                            | Description                             |
|------------------------------------|-----------------------------------------|
| `export <URL>`                     | Export single document to Markdown      |
| `export-wiki-space <space_id>`     | Batch export wiki space with hierarchy  |
| `export-workspace-schema <id>`     | Export APaaS database schema            |
| `export-wechat <URL>`              | Export WeChat article to Markdown       |
| `create <title>`                   | Create new Feishu document (`--url` supported) |
| `drive ls`                         | List files in app/user cloud space      |
| `drive rm <TOKEN>`                 | Delete a file from cloud space          |
| `drive perm-show <TOKEN>`          | Show public permission settings         |
| `drive perm-set <TOKEN>`           | Update public permission settings       |
| `drive perm-members <TOKEN>`       | List permission members                 |
| `drive perm-add <TOKEN>`           | Add a permission member                 |
| `drive perm-update <TOKEN>`        | Update a permission member              |
| `drive perm-rm <TOKEN>`            | Remove a permission member              |
| `drive clear`                      | Clear files with double confirmation    |
| `write <URL>`                      | Append Markdown content to document     |
| `update <URL>`                     | Update specific block in document       |
| `auth`                             | OAuth authorization                     |
| `tui`                              | Launch TUI interface                    |
| `config set`                       | Set credentials                         |
| `config show`                      | Show configuration                      |
| `config clear`                     | Clear cache                             |

## 📚 Documentation Strategy

- `README`: overview, quick start, and command index
- `docs/*.md`: topic-focused guides for more complex workflows

Currently available:

- [Drive Management](./docs/drive-management.md)

---

## 🗺️ Roadmap

- [x] Document/Sheet/Wiki export
- [x] OAuth 2.0 + Token refresh
- [x] TUI interface
- [x] Claude Skills support
- [x] Batch export entire wiki space
- [x] Write to Feishu (create/update docs)

---

## 📜 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.

## 📚 More Docs

- [Drive Management](./docs/drive-management.md)

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

**⭐ Star this repo if you find it helpful!**
