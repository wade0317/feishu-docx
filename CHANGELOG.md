# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 写入 Markdown 时支持将 ` ```mermaid ` fenced code block 自动创建为飞书画板，并通过白板 Mermaid/PlantUML API 导入源码
- 写入 Markdown 一级标题时，使用带 `__DOC_H1__ ` 标记的有序列表块，便于后续 Docs Add-on 仅转换目标块为 `heading1`
- 新增最小 Docs Add-on 示例 `docs/addons/heading-turninto-addon/`，用于将带标记的有序列表块转换为一级标题并移除标记

### Fixed
- 修复导出 Markdown 时 `ordered.style.sequence = auto` 的首个列表项错误渲染为 `2.` 的问题

## [0.2.2] - 2026-03-11

### Added
- 新增 `drive` 命令组，支持在应用云空间或个人云空间中列出文件、删除文件、查看/更新公开权限、管理权限成员
- 新增 `DriveAPI` SDK 子模块，封装 `drive.v1.file` 与 `drive.v1.permission_*` 文件管理能力
- 新增云空间资源 URL / token 解析能力，支持从 `docx`、`sheet`、`bitable`、`wiki`、`folder` 等链接中提取 token
- 新增 `drive clear` 高风险清空命令，默认执行双重确认
- 新增专题文档 `docs/drive-management.md`

### Fixed
- 修复 Markdown 嵌套列表写入飞书时 `children` 结构不兼容的问题，改为递归创建子块
- 修复包含 YAML front matter 的 Markdown 文件写入异常，写入前会先清理 front matter
- 修复 Markdown 表格本地创建流程，按飞书限制自动拆分超过 9 行的表格并逐个回填单元格内容
- 修复 Block 创建请求体清洗逻辑，使用飞书 SDK `Block` 模型构造请求并移除不允许的响应字段
- 修复 `write` 命令中的调试断点残留

## [0.2.1] - 2026-03-02

### Added
- 新增 `create --url`：支持输入微信公众号文章 URL，自动抓取并创建飞书云文档
- 新增 `export-wechat` CLI 命令：支持输入微信公众号文章 URL，导出为 Markdown 文件
- 新增 `WeChatArticleImporter`：支持文章元数据提取、正文转 Markdown、图片下载与本地替换

## [0.2.0] - 2026-02-01

### 🚀 Major Refactoring

#### SDK 架构重构
- **组合模式重构** - SDK 从单体类拆分为 7 个职责清晰的子模块：
  - `sdk.docx` - 云文档操作
  - `sdk.sheet` - 电子表格操作
  - `sdk.bitable` - 多维表格操作
  - `sdk.wiki` - 知识库操作
  - `sdk.media` - 媒体资源操作
  - `sdk.contact` - 联系人操作
  - `sdk.apaas` - APaaS 数据库操作
- **懒加载机制** - 子模块按需初始化，提升启动性能
- **完全向后兼容** - 旧 API 保持可用

#### CLI 模块拆分
- **模块化重构** - 1110 行 `main.py` 拆分为 7 个独立模块：
  - `main.py` - 入口，命令注册
  - `common.py` - 共享工具函数
  - `cmd_export.py` - 导出命令
  - `cmd_write.py` - 写入命令
  - `cmd_apaas.py` - APaaS 命令
  - `cmd_auth.py` - 认证命令
  - `cmd_config.py` - 配置命令
  - `cmd_tui.py` - TUI 命令

### Added
- **知识空间批量导出 API** - `FeishuExporter.export_wiki_space()` 方法，支持 Python API 调用
- `WikiAPI.get_space_info()` - 获取知识空间名称
- 导出目录自动使用 space_name 命名子目录
- 所有 CLI 命令新增 `--auth-mode` 参数，支持命令行指定认证模式
- 新增环境变量 `FEISHU_AUTH_MODE` 支持
- `get_credentials()` 三参数独立优先级：命令行 > 环境变量 > 配置文件

### Changed
- 认证逻辑统一化，`app_id`、`app_secret`、`auth_mode` 遵循相同优先级规则
- Parser 使用组合模式 SDK，代码更简洁
- Wiki SDK 方法失败时抛出异常而不是返回 None

---

## [0.1.5] - 2026-01-29

### Changed
- 改进获取文档块列表的逻辑以支持分页获取所有blocks
- 使用官方的Block模型
- 新增 larkoffice.com 域名文件解析(部分文档图片无权限下载)
- 支持 Markdown 本地转换与图片回填，创建时可上传完整文档

## [0.1.4] - 2026-01-16

### Added
- 文件/附件 Block 支持，生成带临时下载链接的 markdown（📎 格式）

---

## [0.1.3] - 2026-01-12

### Added
- CLI `--stdout` / `-c` 参数，直接输出内容到标准输出（适合 AI Agent）
- TUI Access Token 输入框支持
- TUI URL 输入历史（上下箭头浏览）
- TUI 动态进度回调，实时显示解析进度
- TUI 详细错误日志（显示 traceback 最后 3 行）
- OAuth 授权页面简约重新设计（深色主题）
- GitHub Actions 自动发布到 PyPI

### Changed
- README 图片链接改为 GitHub raw 链接（PyPI 可显示）
- OAuth 页面模板抽取到 `auth/templates.py`

### Fixed
- README 中英文切换链接修复

---

## [0.1.0] - 2026-01-10

### Added
- 初始版本发布
- 云文档 (docx) 导出为 Markdown
- 电子表格 (sheet) 导出为 Markdown 表格
- 多维表格 (bitable) 导出为 Markdown 表格
- 知识库 (wiki) 节点自动解析导出
- 图片自动下载并本地引用
- 画板导出为图片
- OAuth 2.0 授权 + Token 自动刷新
- CLI 命令行工具
- TUI 终端界面（基于 Textual）
- Claude Skills 支持
