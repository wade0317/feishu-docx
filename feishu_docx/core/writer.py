# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：writer.py
# @Date   ：2026/03/11 11:20
# @Author ：leemysw
# 2026/01/18 17:55   Create
# 2026/01/28 10:20   Add image refill pipeline
# 2026/01/28 12:05   Use safe console output
# 2026/01/28 12:45   Use local converter for tables
# 2026/01/28 13:10   Fill table cells after creation
# 2026/01/28 13:25   Fetch table cell blocks on demand
# 2026/03/11 11:20   Fix nested list recursion and table chunk creation
# 2026/03/19 19:35   Add Mermaid-to-whiteboard write pipeline
# 2026/03/20 00:35   Add PlantUML/UML write pipeline
# =====================================================
"""
飞书文档写入器

[INPUT]: 依赖 sdk.py 和 converters/md_to_blocks.py
[OUTPUT]: 对外提供 FeishuWriter 类，支持创建文档和写入 Markdown
[POS]: core 模块的高层写入接口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import copy
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from feishu_docx.core.converters import MarkdownToBlocks
from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.utils.console import get_console

console = get_console()


class FeishuWriter:
    """
    飞书文档写入器

    提供高层接口：
    - 创建文档并写入 Markdown 内容
    - 向现有文档追加内容
    - 更新文档特定 Block
    """

    def __init__(self, sdk: Optional[FeishuSDK] = None):
        """
        初始化写入器

        Args:
            sdk: FeishuSDK 实例，不传则自动创建
        """
        self.sdk = sdk or FeishuSDK()
        self.converter = MarkdownToBlocks()

    @staticmethod
    def _block_id(block: Any) -> Optional[str]:
        if isinstance(block, dict):
            return block.get("block_id")
        return getattr(block, "block_id", None)

    @staticmethod
    def _block_type(block: Any) -> Optional[int]:
        if isinstance(block, dict):
            return block.get("block_type")
        return getattr(block, "block_type", None)

    @staticmethod
    def _block_children(block: Any) -> List[str]:
        if isinstance(block, dict):
            return block.get("children") or []
        return getattr(block, "children", []) or []

    @staticmethod
    def _extract_markdown_title(raw_md_content: str) -> Optional[str]:
        for line in raw_md_content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                return title or None
        return None

    def _resolve_document_title(
            self,
            raw_md_content: str,
            file_path: Optional[Union[str, Path]] = None,
    ) -> Optional[str]:
        if file_path:
            stem = Path(file_path).stem.strip()
            if stem:
                return stem
        return self._extract_markdown_title(raw_md_content)

    def _ordered_blocks(self, document_id: str, user_access_token: str) -> List[Any]:
        blocks = self.sdk.docx.get_block_list(document_id, user_access_token)
        if not blocks:
            return []

        block_map = {
            self._block_id(b): b
            for b in blocks
            if self._block_id(b)
        }
        root_id = document_id if document_id in block_map else next(
            (self._block_id(b) for b in blocks if self._block_type(b) == 1),
            document_id,
        )

        ordered = []
        visited = set()

        def dfs(block_id: str) -> None:
            if block_id in visited:
                return
            visited.add(block_id)
            block = block_map.get(block_id)
            if not block:
                return
            ordered.append(block)
            for child_id in self._block_children(block):
                dfs(child_id)

        dfs(root_id)
        return ordered

    def _resolve_link_for_mention_doc(self, url: str, user_access_token: str) -> Optional[Dict[str, Any]]:
        patterns = {
            "doc": r"(?:feishu|larksuite)\.cn/doc/([a-zA-Z0-9]+)|larkoffice\.com/doc/([a-zA-Z0-9]+)",
            "docx": r"(?:feishu|larksuite)\.cn/docx/([a-zA-Z0-9]+)|larkoffice\.com/docx/([a-zA-Z0-9]+)",
            "wiki": r"(?:feishu|larksuite)\.cn/wiki/([a-zA-Z0-9]+)|larkoffice\.com/wiki/([a-zA-Z0-9]+)",
        }

        parsed_type = None
        parsed_token = None
        for node_type, pattern in patterns.items():
            match = re.search(pattern, url)
            if match:
                parsed_type = node_type
                parsed_token = match.group(1) or match.group(2)
                break

        if not parsed_type or not parsed_token:
            return None

        if parsed_type == "wiki":
            node = self.sdk.wiki.get_node_metadata(parsed_token, user_access_token)
            if not node or getattr(node, "obj_type", None) not in ("docx", "doc"):
                return None
            parsed_type = getattr(node, "obj_type")
            parsed_token = getattr(node, "obj_token", None)
            if not parsed_token:
                return None

        if parsed_type not in {"docx", "doc"}:
            return None

        return {
            "obj_type": parsed_type,
            "token": parsed_token,
            "url": url,
            "fallback_type": 0,
        }

    def _prepare_table_blocks(
            self, blocks: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        normalized_blocks: List[Dict[str, Any]] = []
        table_plans: List[Dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                normalized_blocks.append(block)
                continue
            if block.get("block_type") != self.converter.BLOCK_TYPE_TABLE:
                normalized_blocks.append(block)
                continue

            cell_blocks = block.get("children") or []
            cell_contents = []
            for cell in cell_blocks:
                if isinstance(cell, dict):
                    cell_contents.append(cell.get("children") or [])
                    cell.pop("children", None)
                else:
                    cell_contents.append([])

            expected_cells = None
            table_prop = (block.get("table") or {}).get("property") or {}
            row_size = table_prop.get("row_size")
            column_size = table_prop.get("column_size")
            if isinstance(row_size, int) and isinstance(column_size, int):
                expected_cells = row_size * column_size

            if expected_cells is not None and expected_cells > len(cell_blocks):
                for _ in range(expected_cells - len(cell_blocks)):
                    cell_blocks.append(
                        {
                            "block_type": self.converter.BLOCK_TYPE_TABLE_CELL,
                            "table_cell": {},
                        }
                    )
                    cell_contents.append([])
            elif expected_cells is not None and expected_cells < len(cell_blocks):
                cell_blocks = cell_blocks[:expected_cells]
                cell_contents = cell_contents[:expected_cells]

            if not isinstance(row_size, int) or not isinstance(column_size, int) or column_size <= 0:
                normalized_blocks.append(block)
                continue

            # 飞书单次创建 Table Block 最多支持 9 行，这里按 9 行拆分。
            max_rows_per_table = 9
            for row_start in range(0, row_size, max_rows_per_table):
                chunk_rows = min(max_rows_per_table, row_size - row_start)
                start_idx = row_start * column_size
                end_idx = start_idx + chunk_rows * column_size

                table_block = copy.deepcopy(block)
                table_block.pop("children", None)
                table_block["table"] = {
                    "property": {
                        **table_prop,
                        "row_size": chunk_rows,
                        "column_size": column_size,
                    }
                }
                normalized_blocks.append(table_block)
                table_plans.append(
                    {
                        "cell_contents": cell_contents[start_idx:end_idx],
                    }
                )

        return normalized_blocks, table_plans

    def _table_cell_ids(self, table_block: Any) -> List[str]:
        if isinstance(table_block, dict):
            children = table_block.get("children") or []
            if children:
                return children
            return (table_block.get("table") or {}).get("cells") or []
        return []

    @staticmethod
    def _whiteboard_token(block: Any) -> Optional[str]:
        if isinstance(block, dict):
            board = block.get("board") or {}
            if isinstance(board, dict):
                return board.get("token") or board.get("whiteboard_id") or board.get("id")
            return None

        board = getattr(block, "board", None)
        if not board:
            return None
        return (
            getattr(board, "token", None)
            or getattr(board, "whiteboard_id", None)
            or getattr(board, "id", None)
        )

    def _fill_table_cells(
            self,
            document_id: str,
            created_table_block: Dict[str, Any],
            cell_contents: List[List[Dict[str, Any]]],
            user_access_token: str,
    ) -> None:
        cell_ids = self._table_cell_ids(created_table_block)
        if not cell_ids:
            table_block_id = self._block_id(created_table_block)
            if table_block_id:
                try:
                    cell_blocks = self.sdk.docx.get_block_children(
                        document_id=document_id,
                        block_id=table_block_id,
                        access_token=user_access_token,
                    )
                    cell_ids = [self._block_id(b) for b in cell_blocks if self._block_id(b)]
                except Exception as e:
                    console.print(f"[yellow]![/yellow] 获取表格单元格失败: {e}")
            if not cell_ids:
                console.print("[yellow]![/yellow] 未能获取表格单元格 ID，跳过单元格内容写入")
                return

        if len(cell_ids) != len(cell_contents):
            console.print(
                f"[yellow]![/yellow] 表格单元格数量不匹配，返回 {len(cell_ids)}，期望 {len(cell_contents)}"
            )

        count = min(len(cell_ids), len(cell_contents))
        for idx in range(count):
            cell_id = cell_ids[idx]
            content_blocks = cell_contents[idx]
            if not content_blocks:
                continue
            self.sdk.docx.create_blocks(
                document_id=document_id,
                block_id=cell_id,
                children=content_blocks,
                access_token=user_access_token,
                )
            time.sleep(0.35)

    def _replace_board_with_code_block(
            self,
            document_id: str,
            parent_block_id: str,
            created_block: Dict[str, Any],
            board_source_plan: Dict[str, Any],
            user_access_token: str,
            insert_index: int,
    ) -> None:
        self.sdk.docx.delete_blocks(
            document_id=document_id,
            block_id=parent_block_id,
            start_index=insert_index,
            end_index=insert_index + 1,
            access_token=user_access_token,
        )

        fallback_block = self.converter._make_plain_code_block(  # noqa: SLF001
            board_source_plan.get("code", ""),
            board_source_plan.get("language", ""),
        )
        self.sdk.docx.create_blocks(
            document_id=document_id,
            block_id=parent_block_id,
            children=[fallback_block],
            access_token=user_access_token,
            index=insert_index,
        )

    def _create_blocks_recursive(
            self,
            document_id: str,
            parent_block_id: str,
            blocks: List[Dict[str, Any]],
            user_access_token: str,
    ) -> List[Dict[str, Any]]:
        """递归创建块，避免将嵌套 children 直接放入单次创建请求。"""
        request_blocks: List[Dict[str, Any]] = []
        child_plans: List[List[Dict[str, Any]]] = []
        board_source_plans: List[Optional[Dict[str, Any]]] = []

        for block in blocks:
            block_copy = dict(block)
            nested_children = [
                child for child in (block_copy.pop("children", []) or [])
                if isinstance(child, dict)
            ]
            board_source_plan = block_copy.pop("_feishu_docx_board_source", None)
            request_blocks.append(block_copy)
            child_plans.append(nested_children)
            board_source_plans.append(board_source_plan)

        created_blocks = self.sdk.docx.create_blocks(
            document_id=document_id,
            block_id=parent_block_id,
            children=request_blocks,
            access_token=user_access_token,
        )

        for sibling_index, (created_block, nested_children, board_source_plan) in enumerate(
                zip(created_blocks, child_plans, board_source_plans)
        ):
            if board_source_plan:
                whiteboard_id = self._whiteboard_token(created_block)
                if not whiteboard_id:
                    raise RuntimeError("文本图表画板创建成功，但未返回 whiteboard token")
                try:
                    self.sdk.media.create_whiteboard_plantuml_node(
                        whiteboard_id=whiteboard_id,
                        source_code=board_source_plan.get("code", ""),
                        access_token=user_access_token,
                        syntax_type=board_source_plan.get("syntax_type", 2),
                        style_type=board_source_plan.get("style_type", 1),
                        diagram_type=board_source_plan.get("diagram_type", 0),
                    )
                except RuntimeError as e:
                    error_text = str(e)
                    if (
                            "parse Mermaid failed" in error_text
                            or "Lexical error" in error_text
                            or "Syntax Error" in error_text
                            or "parse error" in error_text
                    ):
                        console.print(
                            "[yellow]![/yellow] 图表画板解析失败，已回退为普通代码块"
                        )
                        self._replace_board_with_code_block(
                            document_id=document_id,
                            parent_block_id=parent_block_id,
                            created_block=created_block,
                            board_source_plan=board_source_plan,
                            user_access_token=user_access_token,
                            insert_index=sibling_index,
                        )
                    else:
                        raise

            if not nested_children:
                continue
            created_block_id = self._block_id(created_block)
            if not created_block_id:
                continue
            self._create_blocks_recursive(
                document_id=document_id,
                parent_block_id=created_block_id,
                blocks=nested_children,
                user_access_token=user_access_token,
            )

        return created_blocks

    def create_document(
            self,
            title: str,
            content: Optional[str] = None,
            file_path: Optional[Union[str, Path]] = None,
            folder_token: Optional[str] = None,
            user_access_token: str = "",
    ) -> Dict:
        """
        创建文档并写入 Markdown 内容

        Args:
            title: 文档标题
            content: Markdown 内容字符串（与 file_path 二选一）
            file_path: Markdown 文件路径（与 content 二选一）
            folder_token: 目标文件夹 token
            user_access_token: 用户访问凭证

        Returns:
            包含 document_id, url 的字典
        """
        # 创建空白文档
        doc = self.sdk.docx.create_document(title, user_access_token, folder_token)
        document_id = doc["document_id"]

        # 写入内容
        if content or file_path:
            self.write_content(
                document_id=document_id,
                content=content,
                file_path=file_path,
                user_access_token=user_access_token,
            )

        return {
            "document_id": document_id,
            "url": f"https://feishu.cn/docx/{document_id}",
            "title": title,
        }

    def write_content(
            self,
            document_id: str,
            content: Optional[str] = None,
            file_path: Optional[Union[str, Path]] = None,
            user_access_token: str = "",
            append: bool = True,
            use_native_api: bool = True,
    ) -> List[Dict]:
        """
        向文档写入 Markdown 内容

        Args:
            document_id: 文档 ID
            content: Markdown 内容字符串
            file_path: Markdown 文件路径
            user_access_token: 用户访问凭证
            append: True 追加到末尾，False 清空后写入
            use_native_api: 使用飞书原生 API 转换（推荐）

        Returns:
            创建的 Block 列表
        """
        # 读取内容
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_md_content = f.read()
            base_dir = Path(file_path).parent
        elif content:
            raw_md_content = content
            base_dir = Path.cwd()
        else:
            raise ValueError("必须提供 content 或 file_path")

        document_title = self._resolve_document_title(raw_md_content, file_path)
        if document_title:
            try:
                self.sdk.docx.update_document_title(document_id, document_title, user_access_token)
            except Exception as title_err:
                console.print(f"[yellow]![/yellow] 更新文档标题失败，继续写入内容: {title_err}")

        md_content = self.converter.preprocess_markdown(raw_md_content)
        self.converter.link_resolver = lambda url: self._resolve_link_for_mention_doc(url, user_access_token)

        # 转换为 Block
        blocks: List[Dict[str, Any]] = []
        image_paths: List[str] = []
        use_local_blocks = False

        if use_native_api:
            local_blocks, local_images = self.converter.convert(md_content)
            has_nested_lists = self.converter.has_nested_list(md_content)
            has_tables = any(
                isinstance(b, dict) and b.get("block_type") == self.converter.BLOCK_TYPE_TABLE
                for b in local_blocks
            )
            has_board_source = any(
                isinstance(b, dict) and b.get("_feishu_docx_board_source")
                for b in local_blocks
            )
            has_mention_doc = self._blocks_have_mention_doc(local_blocks)
            if local_images or has_nested_lists or has_tables or has_board_source or has_mention_doc:
                blocks, image_paths = local_blocks, local_images
                use_local_blocks = True
            else:
                blocks = self.sdk.docx.convert_markdown(md_content, user_access_token)
        else:
            blocks, image_paths = self.converter.convert(md_content)
            use_local_blocks = True

        if not blocks:
            return []

        table_plans: List[Dict[str, Any]] = []
        if use_local_blocks:
            blocks, table_plans = self._prepare_table_blocks(blocks)

        console.print(f"[yellow]>[/yellow] 已转换 {len(blocks)} 个 Blocks，正在写入飞书...")

        if not append:
            try:
                deleted = self.sdk.docx.clear_document(document_id, user_access_token)
                console.print(f"  - 已清空文档内容（删除约 {deleted} 个块）")
            except Exception as clear_err:
                console.print(f"[yellow]![/yellow] 清空文档失败，继续写入: {clear_err}")

        created_blocks = self._create_blocks_recursive(
            document_id=document_id,
            parent_block_id=document_id,
            blocks=blocks,
            user_access_token=user_access_token,
        )

        if use_local_blocks and table_plans:
            created_table_blocks = [
                b for b in created_blocks
                if isinstance(b, dict) and b.get("block_type") == self.converter.BLOCK_TYPE_TABLE
            ]
            if len(created_table_blocks) != len(table_plans):
                console.print(
                    f"[yellow]![/yellow] 表格块数量不匹配，创建 {len(created_table_blocks)}，计划 {len(table_plans)}"
                )

            resolved_table_blocks: Dict[str, Any] = {}
            if created_table_blocks:
                try:
                    all_blocks = self.sdk.docx.get_block_list(document_id, user_access_token)
                    resolved_table_blocks = {
                        self._block_id(b): b
                        for b in all_blocks
                        if self._block_type(b) == self.converter.BLOCK_TYPE_TABLE
                    }
                except Exception as e:
                    console.print(f"[yellow]![/yellow] 获取表格块信息失败: {e}")

            for table_block, plan in zip(created_table_blocks, table_plans):
                cell_contents = plan.get("cell_contents") or []
                if not cell_contents:
                    continue
                table_block_id = self._block_id(table_block)
                resolved_block = resolved_table_blocks.get(table_block_id) if table_block_id else None
                self._fill_table_cells(
                    document_id=document_id,
                    created_table_block=resolved_block or table_block,
                    cell_contents=cell_contents,
                    user_access_token=user_access_token,
                )

        if image_paths:
            console.print(f"> 正在为 [blue]{len(image_paths)}[/blue] 个图片 Block 回填内容...")
            console.print("  - 等待 10s 以确保 Block 一致性...")
            time.sleep(10)

            ordered_blocks = self._ordered_blocks(document_id, user_access_token)
            image_blocks = [
                b
                for b in ordered_blocks
                if self._block_type(b) == 27 and self._block_id(b) != document_id
            ]

            if len(image_blocks) != len(image_paths):
                console.print(
                    f"[yellow]![/yellow] 警告：图片 Block 数量 ({len(image_blocks)}) 与路径数量 ({len(image_paths)}) 不匹配"
                )
                count = min(len(image_blocks), len(image_paths))
            else:
                count = len(image_paths)

            for i in range(count):
                img_url = image_paths[i]
                img_block = image_blocks[i]
                block_id = self._block_id(img_block)
                if not block_id:
                    continue

                img_path = base_dir / img_url
                if img_path.exists():
                    try:
                        console.print(f"  - 上传图片: [dim]{img_url}[/dim]")
                        file_token = self.sdk.media.upload_image(
                            str(img_path),
                            block_id,
                            document_id,
                            user_access_token,
                        )
                        self.sdk.docx.replace_image(
                            document_id=document_id,
                            block_id=block_id,
                            file_token=file_token,
                            access_token=user_access_token,
                        )
                    except Exception as e:
                        console.print(f"[red]![/red] 上传图片失败 [dim]{img_url}[/dim]: {e}")
                        try:
                            self.sdk.docx.delete_block(document_id, block_id, user_access_token)
                            console.print(f"  - 已清理占位符 Block [dim]{block_id}[/dim]")
                        except Exception as delete_err:
                            console.print(f"  ! 清理占位符失败: {delete_err}")
                else:
                    console.print(f"[yellow]![/yellow] 找不到本地图片: [dim]{img_url}[/dim]")
                    try:
                        self.sdk.docx.delete_block(document_id, block_id, user_access_token)
                    except Exception:
                        pass

        console.print("[green]v[/green] 文档同步完成！")
        return created_blocks

    def _blocks_have_mention_doc(self, blocks: List[Dict[str, Any]]) -> bool:
        def has_mention(elements: List[Dict[str, Any]]) -> bool:
            return any(isinstance(element, dict) and element.get("mention_doc") for element in elements)

        for block in blocks:
            if not isinstance(block, dict):
                continue
            for value in block.values():
                if isinstance(value, dict) and has_mention(value.get("elements") or []):
                    return True
            if self._blocks_have_mention_doc(block.get("children") or []):
                return True
        return False

    def update_block(
            self,
            document_id: str,
            block_id: str,
            content: str,
            user_access_token: str = "",
    ) -> Dict:
        """
        更新指定 Block 的内容

        Args:
            document_id: 文档 ID
            block_id: Block ID
            content: 新的文本内容
            user_access_token: 用户访问凭证

        Returns:
            更新后的 Block
        """
        update_body = {
            "text": {
                "elements": [{"text_run": {"content": content}}]
            }
        }
        return self.sdk.docx.update_block(
            document_id=document_id,
            block_id=block_id,
            update_body=update_body,
            access_token=user_access_token,
        )

    def append_markdown(
            self,
            document_id: str,
            content: str,
            user_access_token: str = "",
    ) -> List[Dict]:
        """
        追加 Markdown 内容到文档末尾

        Args:
            document_id: 文档 ID
            content: Markdown 内容
            user_access_token: 用户访问凭证

        Returns:
            创建的 Block 列表
        """
        return self.write_content(
            document_id=document_id,
            content=content,
            user_access_token=user_access_token,
            append=True,
        )
