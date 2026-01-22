"""
File Operations Skill

功能：
- 读取文本文件
- 解析 CSV 表格
- 提取数值列为数组
"""

from pathlib import Path
from typing import List
import csv
import json
import os

from langchain_core.tools import tool, BaseTool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from skill_system2.core.base_skill import BaseSkill, SkillMetadata


# 文件操作技能实现
class FileOperationsSkill(BaseSkill):
    """文件操作 Skill"""

    # 返回技能元数据
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="file_operations",
            description="文件读取与表格解析能力（文本、CSV）",
            version="1.0.0",
            tags=["file", "csv", "data", "io"],
            visibility="public",
            dependencies=[],
            author="MuyuCheney"
        )

    # 返回用于加载技能的工具
    def get_loader_tool(self) -> BaseTool:
        skill_instance = self

        # Loader 工具：激活技能并返回说明
        @tool
        def skill_file_operations(runtime) -> Command:
            """
            加载文件操作技能并返回使用说明。
            """
            instructions = skill_instance.get_instructions()
            return Command(
                update={
                    "messages": [ToolMessage(
                        content=instructions,
                        tool_call_id=runtime.tool_call_id
                    )],
                    "skills_loaded": ["file_operations"]
                }
            )

        return skill_file_operations

    # 返回技能内的实际工具列表
    def get_tools(self) -> List[BaseTool]:
        return [
            self._create_get_file_info_tool(),
            self._create_read_text_tool(),
            self._create_read_csv_tool(),
            self._create_csv_column_to_list_tool(),
        ]

    # 创建文件信息查询工具
    def _create_get_file_info_tool(self) -> BaseTool:
        @tool
        def get_file_info(file_path: str) -> str:
            """
            获取文件基础元信息。
            """
            path = Path(file_path)
            if not path.exists():
                return f"Error: file not found: {file_path}"

            info = {
                "name": path.name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "extension": path.suffix.lower(),
                "modified_time": path.stat().st_mtime,
            }
            return json.dumps(info, ensure_ascii=False, indent=2)

        return get_file_info

    # 创建文本读取工具
    def _create_read_text_tool(self) -> BaseTool:
        @tool
        def read_text_file(file_path: str, max_chars: int = 4000) -> str:
            """
            读取文本文件内容（支持截断）。
            """
            path = Path(file_path)
            if not path.exists():
                return f"Error: file not found: {file_path}"

            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="utf-8", errors="ignore")

            return content[:max_chars]

        return read_text_file

    # 创建 CSV 读取工具
    def _create_read_csv_tool(self) -> BaseTool:
        @tool
        def read_csv(file_path: str, max_rows: int = 50) -> str:
            """
            读取 CSV 文件并返回行数据（JSON 字符串）。
            """
            path = Path(file_path)
            if not path.exists():
                return f"Error: file not found: {file_path}"

            rows = []
            with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    rows.append(row)
                    if i + 1 >= max_rows:
                        break

            return json.dumps(rows, ensure_ascii=False, indent=2)

        return read_csv

    # 创建 CSV 数值列提取工具
    def _create_csv_column_to_list_tool(self) -> BaseTool:
        @tool
        def csv_column_to_list(file_path: str, column: str, max_rows: int = 1000) -> str:
            """
            提取 CSV 指定列为数值数组（JSON 字符串）。
            """
            path = Path(file_path)
            if not path.exists():
                return f"Error: file not found: {file_path}"

            values: List[float] = []
            with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    raw = row.get(column)
                    if raw is None:
                        continue
                    try:
                        values.append(float(raw))
                    except ValueError:
                        continue

            return json.dumps(values, ensure_ascii=False)

        return csv_column_to_list


# 工厂函数：用于注册中心加载技能
def create_skill(skill_dir: Path) -> BaseSkill:
    return FileOperationsSkill(skill_dir)
