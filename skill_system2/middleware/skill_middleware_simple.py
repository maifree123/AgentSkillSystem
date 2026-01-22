"""
Simple skill middleware for environments without full middleware support.
"""

import logging
from typing import List, Optional, Callable

from langchain_core.tools import BaseTool

from skill_system2.core.registry import SkillRegistry

logger = logging.getLogger(__name__)


# 简化版中间件：根据已加载技能返回工具列表
class SimpleSkillMiddleware:
    """
    Simple helper that returns tools based on loaded skills.
    """

    # 初始化简化中间件
    def __init__(
        self,
        skill_registry: SkillRegistry,
        verbose: bool = False,
        filter_fn: Optional[Callable] = None
    ):
        self.registry = skill_registry
        self.verbose = verbose
        self.filter_fn = filter_fn

    # 根据当前技能状态获取工具列表
    def get_tools_for_state(self, skills_loaded: List[str]) -> List[BaseTool]:
        tools = self.registry.get_tools_for_skills(skills_loaded)

        if self.filter_fn:
            tools = [t for t in tools if self.filter_fn(t)]

        if self.verbose:
            logger.info(f"Skills loaded: {skills_loaded}")
            logger.info(f"Available tools: {[t.name for t in tools]}")

        return tools


# 便捷函数：基于已加载技能返回工具列表
def create_skill_aware_tools(
    registry: SkillRegistry,
    skills_loaded: Optional[List[str]] = None
) -> List[BaseTool]:
    if skills_loaded is None:
        skills_loaded = []

    return registry.get_tools_for_skills(skills_loaded)


# 兼容旧用法的占位中间件
class SkillMiddleware:
    """
    Placeholder class for compatibility with older usage patterns.
    """

    # 初始化占位中间件
    def __init__(
        self,
        skill_registry: SkillRegistry,
        verbose: bool = False,
        filter_fn: Optional[Callable] = None
    ):
        self.registry = skill_registry
        self.verbose = verbose
        self.filter_fn = filter_fn
        logger.warning(
            "SkillMiddleware: using simplified implementation. "
            "Full runtime tool filtering requires middleware support."
        )

    # 根据已加载技能返回工具列表
    def get_tools_for_skills(self, skills_loaded: List[str]) -> List[BaseTool]:
        tools = self.registry.get_tools_for_skills(skills_loaded)

        if self.filter_fn:
            tools = [t for t in tools if self.filter_fn(t)]

        if self.verbose:
            logger.info(f"Skills loaded: {skills_loaded}")
            logger.info(f"Available tools: {[t.name for t in tools]}")

        return tools
