"""
技能中间件-在每次模型调用之前进行动态工具过滤。
"""

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.tools import BaseTool

from skill_system2.core.registry import SkillRegistry
import logging
from typing import Dict, List, Optional, Callable, Any

logger = logging.getLogger(__name__)

# 按已加载技能动态过滤工具的中间件
class SkillMiddleware(AgentMiddleware):
    """
    基于技能加载的过滤工具。
    """
    # 初始化技能中间件
    def __init__(
            self,
            skill_registry: SkillRegistry,
            verbose: bool = False,
            filter_fn: Optional[Callable[[Any], bool]] = None

    ):
        super().__init__()
        self.registry = skill_registry
        self.verbose = verbose
        self.filter_fn = filter_fn

    # 构建筛选工具列表（加载器+加载技能）
    # 根据已加载技能构建工具列表
    def _get_filtered_tools(self, skills_loaded: List[str]) -> List[BaseTool]:
        tools = self.registry.get_tools_for_skills(skills_loaded)
        return tools
    
    # 同步模型调用拦截：覆盖工具列表
    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        skills_loaded = []
        if hasattr(request, "state") and request.state is not None:
            if isinstance(request.state, dict):
                skills_loaded = request.state.get("skills_loaded", [])
            else:
                skills_loaded = getattr(request.state, "skills_loaded", [])
        

        relevant_tools = self._get_filtered_tools(skills_loaded)

        if self.verbose:
            logger.info(f"[SkillMiddleware] Skills loaded: {skills_loaded}")
            logger.info(
                f"[SkillMiddleware] Filtered tools ({len(relevant_tools)}): "
                f"{[t.name for t in relevant_tools]}"
            )

        filtered_request = request.override(tools=relevant_tools)
        return handler(filtered_request)
    
        # 异步包装器
    # 异步模型调用拦截：覆盖工具列表
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        skills_loaded = []
        if hasattr(request, "state") and request.state is not None:
            if isinstance(request.state, dict):
                skills_loaded = request.state.get("skills_loaded", [])
            else:
                skills_loaded = getattr(request.state, "skills_loaded", [])

        relevant_tools = self._get_filtered_tools(skills_loaded)

        if self.verbose:
            logger.info(f"[SkillMiddleware] (async) Skills loaded: {skills_loaded}")
            logger.info(
                f"[SkillMiddleware] (async) Filtered tools ({len(relevant_tools)}): "
                f"{[t.name for t in relevant_tools]}"
            )

        filtered_request = request.override(tools=relevant_tools)
        return await handler(filtered_request)


# 带权限校验的技能中间件
class PermissionAwareSkillMiddleware(SkillMiddleware):
    """
    Skill middleware with permission checks.
    """

    # 初始化权限过滤策略
    def __init__(
        self,
        skill_registry: SkillRegistry,
        user_permissions: Optional[List[str]] = None,
        verbose: bool = False
    ):
        self.user_permissions = user_permissions or []

        # 权限过滤函数（可替换为更复杂逻辑）
        def permission_filter(tool: BaseTool) -> bool:
            return True

        super().__init__(
            skill_registry=skill_registry,
            verbose=verbose,
            filter_fn=permission_filter
        )


# 带调用频率限制入口的中间件
class RateLimitedSkillMiddleware(SkillMiddleware):
    """
    Skill middleware with a hook for rate limiting.
    """

    # 初始化计数器供限流逻辑使用
    def __init__(self, skill_registry: SkillRegistry, verbose: bool = False):
        super().__init__(skill_registry=skill_registry, verbose=verbose)
        self.call_counts = {}

    # 同步调用的限流占位逻辑
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        return super().wrap_model_call(request, handler)

    # 异步调用的限流占位逻辑
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        return await super().awrap_model_call(request, handler)
