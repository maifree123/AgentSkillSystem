"""
Docstring for skill_system2.core.registry
Step 2 目的

目的：提供一个“技能注册中心”，负责注册、查找、列出、过滤、动态加载技能。
做什么：把技能统一存放到一个容器里，后续中间件/Agent 都通过它来获取工具列表。
为什么：如果没有 Registry，技能散落在各处，无法统一管理、搜索、过滤，也无法做自动发现加载。

"""
from typing import Dict, List, Optional, Callable
from pathlib import Path
import importlib.util
import logging

from langchain_core.tools import BaseTool

from .base_skill import BaseSkill, SkillMetadata
from .exceptions import SkillNotFoundError, SkillLoadError

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Docstring for SkillRegistry
    """

    #存储技能实例和元素据缓存

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._metadata_cache: Dict[str, SkillMetadata] = {}

    # 注册技能和缓存元数据
    def register(self, skill: BaseSkill) -> None:
        skill.validate()
        name = skill.metadata.name

        if name in self._skills:
            logger.warning(f"Skill '{name}' 已经注册")

        self._skills[name] = skill
        self._metadata_cache[name] = skill.metadata
        logger.info(f"注册技能: {name} v{skill.metadata.version}")

    # unregister a skill by name
    def unregister(self, skill_name: str) -> None:
        if skill_name in self._skills:
            del self._skills[skill_name]
            del self._metadata_cache[skill_name]
            logger.info(f"撤销技能: {skill_name}")

    #得到技能实例
    def get(self, skill_name: str) -> BaseSkill:
        if skill_name not in self._skills:
            raise SkillNotFoundError(skill_name)
        return self._skills[skill_name]

    #得到缓存元数据
    def get_metadata(self, skill_name: str) -> SkillMetadata:
        if skill_name not in self._metadata_cache:
            raise SkillNotFoundError(skill_name)
        return self._metadata_cache[skill_name]

    ##列出技能名称，可选择按元数据过滤
    def list_skills(
            self,
            filter_fn: Optional[Callable[[SkillMetadata], bool]] = None
    ) -> List[str]:
        if filter_fn is None:
            return list(self._skills.keys())

        return [
            name for name, meta in self._metadata_cache.items()
            if filter_fn(meta)
        ]

    #返回所有可用技能加载工具
    def get_all_loader_tools(
            self,
            filter_fn: Optional[Callable[[SkillMetadata], bool]] = None

    ) -> List[BaseTool]:
        skill_names = self.list_skills(filter_fn)
        loaders = []

        for name in skill_names:
            skill = self._skills[name]
            if skill.metadata.enabled:
                loaders.append(skill.get_loader_tool())

        return loaders

    #返回所有工具(loader和真工具)
    def get_all_tools(
            self,
            filter_fn: Optional[Callable[[SkillMetadata], bool]] = None
    ) -> List[BaseTool]:
        skill_name = self.list_skills(filter_fn)
        all_tools = []

        for name in skill_name:
            skill = self._skills[name]
            if skill.metadata.enabled:
                all_tools.append(skill.get_loader_tool())
                all_tools.extend(skill.get_tools())

        return all_tools

    #返回当前加载技能的工具+所有加载器
    def get_tools_for_skills(self, skill_names: List[str]) -> List[BaseTool]:
        tools = self.get_all_loader_tools()

        for name in skill_names:
            if name in self._skills:
                skill = self._skills[name]
                if skill.metadata.enabled:
                    tools.extend(skill.get_tools())

        return tools

    #自动发现技能在文件夹
    def discover_and_load(
            self,
            skills_dir: Path,
            module_name: str = "skill"
    ) -> int:
        if not skills_dir.exists():
            logger.warning(f"Skill directory not found: {skills_dir}")
            return 0

        loaded_count = 0

        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue

            skills_file = skill_path / f"{module_name}.py"
            if not skills_file.exists():
                continue

            try:
                skill = self._load_skill_from_file(skills_file, skill_path)
                self.register(skill)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_path}: {e}")
                continue

        logger.info(f"Loaded {loaded_count} skills from {skills_dir}")
        return loaded_count

    #加载一个技能模块并调用create_skill（）
    def _load_skill_from_file(
            self,
            skill_file: Path,
            skill_dir: Path,

    ) -> BaseSkill:
        spec = importlib.util.spec_from_file_location(
            f"skill_{skill_dir.name}",
            skill_file
        )
        if spec is None or spec.loader is None:
            raise SkillLoadError(skill_dir.name, "Failed to load module spec")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "create_skill"):
            raise SkillLoadError(
                skill_dir.name,
                "模块必须定义create_skill（）函数"
            )

        skill = module.create_skill(skill_dir)

        if not isinstance(skill, BaseSkill):
            raise SkillLoadError(
                skill_dir.name,
                "create_skill（）必须返回BaseSkill实例"
            )

        return skill

    #按名称/描述/标签/可见性搜索技能
    def search(
            self,
            query: str = "",
            tags: Optional[List[str]] = None,
            visibility: Optional[str] = None

    ) -> List[SkillMetadata]:
        results = []
        for meta in self._metadata_cache.values():
            if query:
                if query.lower() not in meta.name.lower() and \
                   query.lower() not in meta.description.lower():
                    continue

            if tags:
                if not any(tag in meta.tags for tag in tags):
                    continue
            if visibility and meta.visibility != visibility:
                continue

            results.append(meta)

        return results

    #技能数量
    def __len__(self) -> int:
        return len(self._skills)

    #成员确认
    def __contains__(self, skill_name: str) -> bool:
        return skill_name in self._skills

    def __repr__(self) -> str:
        return f"<技能注册:{len(self)} skills>"
