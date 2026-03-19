# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：media.py
# @Date   ：2026/01/29 15:15
# @Author ：leemysw
# 2026/02/01 18:40   Refactor - 组合模式重构
# 2026/02/04 10:15   Add domain-based download fallback
# 2026/03/19 19:35   Add whiteboard Mermaid import API
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 MediaAPI
[POS]: SDK 图片/附件/画板 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
from pathlib import Path
from typing import List, Optional

import lark_oapi as lark
from lark_oapi.api.board.v1 import (
    CreatePlantumlWhiteboardNodeRequest,
    CreatePlantumlWhiteboardNodeRequestBody,
    CreatePlantumlWhiteboardNodeResponse,
    DownloadAsImageWhiteboardRequest,
    DownloadAsImageWhiteboardResponse,
)
from lark_oapi.api.drive.v1 import DownloadMediaRequest, DownloadMediaResponse
from lark_oapi.core import BaseResponse

from feishu_docx.utils.console import get_console
from .base import SubModule

console = get_console()


class MediaAPI(SubModule):
    """图片 & 附件 API"""

    def create_whiteboard_plantuml_node(
            self,
            whiteboard_id: str,
            source_code: str,
            access_token: str,
            syntax_type: int = 2,
            style_type: int = 1,
            diagram_type: int = 0,
            overwrite: bool = True,
    ) -> dict:
        """向画板导入 Mermaid / PlantUML 源码。"""
        request = (
            CreatePlantumlWhiteboardNodeRequest.builder()
            .whiteboard_id(whiteboard_id)
            .request_body(
                CreatePlantumlWhiteboardNodeRequestBody.builder()
                .plant_uml_code(source_code)
                .syntax_type(syntax_type)
                .style_type(style_type)
                .diagram_type(diagram_type)
                .overwrite(overwrite)
                .build()
            )
            .build()
        )
        option = self._build_option(access_token)
        response: CreatePlantumlWhiteboardNodeResponse = (
            self.client.board.v1.whiteboard_node.create_plantuml(request, option)
        )

        if not response.success():
            self._log_error("board.v1.whiteboard_node.create_plantuml", response)
            raise RuntimeError(f"导入 Mermaid/PlantUML 到画板失败: {response.msg}")

        return {
            "node_id": getattr(response.data, "node_id", None) if response.data else None,
            "extra": getattr(response.data, "extra", None) if response.data else None,
        }

    def upload_image(
            self,
            file_path: str,
            parent_node: str,
            document_id: str,
            access_token: str,
    ) -> str:
        """上传本地图片到云空间"""
        import mimetypes
        from lark_oapi.api.drive.v1 import (
            UploadAllMediaRequest,
            UploadAllMediaRequestBody,
            UploadAllMediaResponse,
        )

        p = Path(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "image/jpeg"

        def _try_upload(parent_type: str, node: str) -> Optional[str]:
            with open(file_path, "rb") as f:
                body_builder = (
                    UploadAllMediaRequestBody.builder()
                    .file_name(p.name)
                    .parent_type(parent_type)
                    .parent_node(node)
                    .size(p.stat().st_size)
                    .file(f)
                )
                if node != document_id:
                    body_builder = body_builder.extra(
                        json.dumps({"drive_route_token": document_id})
                    )
                request = (
                    UploadAllMediaRequest.builder()
                    .request_body(body_builder.build())
                    .build()
                )
                option = self._build_option(access_token)
                response: UploadAllMediaResponse = self.client.drive.v1.media.upload_all(request, option)
            if not response.success():
                self._log_error("drive.v1.media.upload_all", response)
                return None
            return response.data.file_token

        token = _try_upload("docx_image", parent_node)
        if token:
            return token

        token = _try_upload("doc_image", document_id)
        if token:
            return token

        raise RuntimeError(f"上传图片失败 ({p.name})")

    def get_image(self, file_token: str, access_token: str) -> Optional[str]:
        """下载云文档中的图片或返回可下载 URL

        策略：
        1. 首先尝试直接下载（适用于有权限的文档）
        2. 如果失败（403/401等权限错误或空响应），使用临时下载 URL（适用于只读文档）
        3. 如果临时 URL 失败，返回拼接的下载 URL（不再下载）
        """
        import httpx

        # 策略1: 尝试直接下载
        request = DownloadMediaRequest.builder().file_token(file_token).build()
        option = self._build_option(access_token)
        response: DownloadMediaResponse = self.client.drive.v1.media.download(request, option)

        extension = ".png"
        if response.success():
            if hasattr(response, "file_name") and response.file_name:
                if "." in response.file_name:
                    extension = f".{response.file_name.split('.')[-1]}"

            file_path = self.temp_dir / f"{file_token}{extension}"
            file_path.write_bytes(response.file.read())
            return str(file_path)

        # 策略2: 直接下载失败，尝试使用临时下载 URL
        # 检查是否为权限错误或空响应
        error_code = response.code if hasattr(response, "code") else None
        permission_errors = {403, 401, 99991663, 99991400}  # 飞书常见权限错误码

        # 检测需要降级的情况：
        # 1. 权限错误码
        # 2. 空响应（code=None, msg=None, response=b''）
        should_fallback = (
            error_code in permission_errors or
            (error_code is None and
             (not hasattr(response, "msg") or response.msg is None) and
             (not hasattr(response, "raw") or not response.raw or response.raw.content == b''))
        )

        if should_fallback:
            console.print(f"[yellow]直接下载失败 (code: {error_code})，尝试使用临时下载 URL...[/yellow]")

            tmp_url = self.get_file_download_url(file_token, access_token)
            if tmp_url:
                try:
                    # 使用临时 URL 下载
                    tmp_response = httpx.get(tmp_url, timeout=30.0)
                    if tmp_response.status_code == 200:
                        file_path = self.temp_dir / f"{file_token}{extension}"
                        file_path.write_bytes(tmp_response.content)
                        console.print(f"[green]✓ 使用临时 URL 下载成功[/green]")
                        return str(file_path)
                    else:
                        console.print(f"[red]临时 URL 下载失败 (HTTP {tmp_response.status_code})[/red]")
                except Exception as e:
                    console.print(f"[red]临时 URL 下载异常: {e}[/red]")
            else:
                console.print(f"[red]获取临时下载 URL 失败[/red]")

            # 策略3: 临时 URL 获取/下载失败，返回拼接域名下载 URL
            document_domain = getattr(self._core, "document_domain", None)
            if document_domain:
                direct_url = (
                    f"https://internal-api-drive-stream.{document_domain}.com/"
                    f"space/api/box/stream/download/v2/cover/{file_token}"
                )
                console.print("[yellow]使用拼接 URL 作为最终降级（不再下载）[/yellow]")
                return direct_url
            else:
                console.print("[red]未设置文档域名，无法拼接下载 URL[/red]")

        # 记录最终失败
        self._log_error("drive.v1.media.download", response)
        return None

    def get_whiteboard(self, whiteboard_id: str, access_token: str) -> Optional[str]:
        """导出画板为图片"""
        request = DownloadAsImageWhiteboardRequest.builder().whiteboard_id(whiteboard_id).build()
        option = self._build_option(access_token)
        response: DownloadAsImageWhiteboardResponse = self.client.board.v1.whiteboard.download_as_image(
            request, option
        )

        if not response.success():
            self._log_error("board.v1.whiteboard.download_as_image", response)
            return None

        file_path = self.temp_dir / f"{whiteboard_id}.png"
        file_path.write_bytes(response.file.read())
        return str(file_path)

    def get_whiteboard_nodes(self, whiteboard_id: str, access_token: str) -> Optional[List[dict]]:
        """获取画板节点元数据"""
        request = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri(f"/open-apis/board/v1/whiteboards/{whiteboard_id}/nodes")
            .token_types({self._get_token_type()})
            .build()
        )
        option = self._build_option(access_token)
        response: BaseResponse = self.client.request(request, option)

        if not response.success():
            self._log_error("board.v1.whiteboard.nodes.get", response)
            return None

        try:
            content = response.raw.content.decode("utf-8")
            resp_json = json.loads(content)
            nodes_data = resp_json.get("data", {}).get("nodes", [])

            nodes = []
            for node in nodes_data:
                node_info = {
                    "node_id": node.get("id", ""),
                    "type": node.get("type", "unknown"),
                }
                if "x" in node and "y" in node:
                    node_info["position"] = {"x": node.get("x"), "y": node.get("y")}
                if "width" in node and "height" in node:
                    node_info["size"] = {"width": node.get("width"), "height": node.get("height")}
                if "parent_id" in node and node.get("parent_id"):
                    node_info["parent_id"] = node.get("parent_id")
                if "children" in node and node.get("children"):
                    node_info["children"] = node.get("children")

                text_content = self._extract_node_text(node)
                if text_content:
                    node_info["text"] = text_content

                nodes.append(node_info)

            return nodes
        except Exception as e:
            console.print(f"[red]解析画板节点失败: {e}[/red]")
            return None

    @staticmethod
    def _extract_node_text(node: dict) -> Optional[str]:
        """提取节点中的文本内容"""
        texts = []

        if "text" in node:
            text_data = node.get("text", {})
            if "text" in text_data and text_data.get("text"):
                texts.append(text_data.get("text"))
            elif "rich_text" in text_data:
                rich_text = text_data.get("rich_text", {})
                paragraphs = rich_text.get("paragraphs", [])
                for para in paragraphs:
                    elements = para.get("elements", [])
                    for elem in elements:
                        if "text_element" in elem:
                            text_elem = elem.get("text_element", {})
                            if "text" in text_elem:
                                texts.append(text_elem.get("text"))
                        elif "link_element" in elem:
                            link_elem = elem.get("link_element", {})
                            if "text" in link_elem:
                                texts.append(link_elem.get("text"))

        if "connector" in node:
            connector = node.get("connector", {})
            captions = connector.get("captions", {})
            caption_data = captions.get("data", [])
            for caption in caption_data:
                if "text" in caption and caption.get("text"):
                    texts.append(caption.get("text"))

        if "section" in node:
            section = node.get("section", {})
            if "title" in section and section.get("title"):
                texts.append(section.get("title"))

        if "table" in node:
            table = node.get("table", {})
            if "title" in table and table.get("title"):
                texts.append(table.get("title"))

        if texts:
            return " | ".join(texts)
        return None

    def get_whiteboard_with_metadata(
            self,
            whiteboard_id: str,
            access_token: str,
            export_image: bool = True,
            export_metadata: bool = False,
    ) -> Optional[dict]:
        """获取画板（支持导出图片和元数据）"""
        result = {}

        if export_image:
            image_path = self.get_whiteboard(whiteboard_id, access_token)
            if image_path:
                result["image_path"] = image_path

        if export_metadata:
            nodes = self.get_whiteboard_nodes(whiteboard_id, access_token)
            if nodes:
                result["nodes"] = nodes
                result["node_count"] = len(nodes)

        return result if result else None

    def get_file_download_url(self, file_token: str, access_token: str) -> Optional[str]:
        """获取文件临时下载 URL"""
        from lark_oapi.api.drive.v1 import (
            BatchGetTmpDownloadUrlMediaRequest,
            BatchGetTmpDownloadUrlMediaResponse,
        )

        request = (
            BatchGetTmpDownloadUrlMediaRequest.builder()
            .file_tokens([file_token])
            .build()
        )
        option = self._build_option(access_token)
        response: BatchGetTmpDownloadUrlMediaResponse = self.client.drive.v1.media.batch_get_tmp_download_url(
            request, option
        )

        if not response.success():
            self._log_error("drive.v1.media.batch_get_tmp_download_url", response)
            return None

        if response.data and response.data.tmp_download_urls:
            for item in response.data.tmp_download_urls:
                if item.file_token == file_token:
                    return item.tmp_download_url
        return None
