"""
Agent Factory - create Skill-aware Agent.
目的：把 Registry + Middleware + Config + System Prompt 组合起来，创建一个可运行的 Skill Agent。
"""
from typing import Optional, Callable, Any, Dict, List
from pathlib import Path
import logging

# 模型基类
from langchain_core.language_models import BaseChatModel

# LangChain 1.0 agent factory + middleware
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware

# 本地模块
from .core.registry import SkillRegistry
from .core.state import SkillState, SkillStateAccumulative, SkillStateFIFO
from .core.base_skill import SkillMetadata
from .middleware import SkillMiddleware
from .config import SkillSystemConfig, load_config
from .utils import setup_logger, generate_system_prompt

logger = logging.getLogger(__name__)


class SkillAgent:
    """
    代理 + 注册表 的简单包装器。
    """

    def __init__(
        self,
        agent: Any,
        registry: SkillRegistry,
        config: SkillSystemConfig
    ):
        self.agent = agent
        self.registry = registry
        self.config = config

    # 用户输入方法
    def invoke(self, input_data: Dict[str, Any], **kwargs) -> Any:
        return self.agent.invoke(input_data, **kwargs)

    # 异步调用
    async def ainvoke(self, input_data: Dict[str, Any], **kwargs) -> Any:
        return await self.agent.ainvoke(input_data, **kwargs)

    # 流式输出
    def stream(self, input_data: Dict[str, Any], **kwargs):
        return self.agent.stream(input_data, **kwargs)

    async def astream(self, input_data: Dict[str, Any], **kwargs):
        return self.agent.astream(input_data, **kwargs)

    # list skills
    def list_skills(self) -> List[str]:
        return self.registry.list_skills()

    def get_skill_info(self, skill_name: str) -> SkillMetadata:
        return self.registry.get_metadata(skill_name)

    # 搜索技能
    def search_skills(
        self,
        query: str = "",
        tags: Optional[List[str]] = None
    ) -> List[SkillMetadata]:
        return self.registry.search(query=query, tags=tags)

    def __repr__(self) -> str:
        return f"<SkillAgent: {len(self.registry)} skills loaded>"


def create_skill_agent(
    model: BaseChatModel,
    config: Optional[SkillSystemConfig] = None,
    config_path: Optional[Path] = None,
    custom_system_prompt: Optional[str] = None,
    filter_fn: Optional[Callable[[SkillMetadata], bool]] = None,
) -> SkillAgent:
    """
    Create a skill-aware agent.
    """
    # 1) 载入 config
    if config is None:
        config = load_config(config_path)

    # 启用日志设置（仅在 verbose 时）
    if config.verbose:
        setup_logger(level=config.log_level)

    logger.info(f"初始化 skill agent 的 config: {config.to_dict()}")

    # 2) 初始化 registry
    registry = SkillRegistry()

    # 3) 自动发现技能
    if config.auto_discover and config.skills_dir.exists():
        loaded_count = registry.discover_and_load(
            skills_dir=config.skills_dir,
            module_name=config.skill_module_name
        )
        logger.info(f"Loaded {loaded_count} skills")
    else:
        logger.warning(
            f"Skill directory not found or auto-discover disabled: {config.skills_dir}"
        )

    # 提示无技能加载的情况
    if len(registry) == 0:
        logger.warning("No skills loaded. Agent will have no skill capabilities.")

    # 4) 定义可见性过滤器
    def visibility_filter(meta: SkillMetadata) -> bool:
        if not config.filter_by_visibility:
            return True
        return meta.visibility in config.allowed_visibilities

    # 5) 组合过滤器（可见性 + 用户过滤器）
    if filter_fn:
        combined_filter = lambda meta: visibility_filter(meta) and filter_fn(meta)
    else:
        combined_filter = visibility_filter

    # 6) 注册所有工具给 agent
    all_tools = registry.get_all_tools(filter_fn=combined_filter)

    # 7) 选择 state schema
    if config.state_mode == "replace":
        state_schema = SkillState
    elif config.state_mode == "accumulate":
        state_schema = SkillStateAccumulative
    elif config.state_mode == "fifo":
        state_schema = SkillStateFIFO
    else:
        raise ValueError(f"Invalid state_mode: {config.state_mode}")

    # 8) 建立中间件列表
    middleware_list: List[AgentMiddleware] = []
    if config.middleware_enabled:
        skill_middleware = SkillMiddleware(
            skill_registry=registry,
            verbose=config.verbose,
            filter_fn=combined_filter
        )
        middleware_list.append(skill_middleware)

    # 9) 系统提示词
    # 基于可见性过滤得到可用技能列表
    available_skills = registry.list_skills(filter_fn=combined_filter)
    system_prompt = custom_system_prompt or generate_system_prompt(
        available_skill_names=available_skills,
        custom_instructions=""
    )

    # 10) 创建 agent (LangChain 1.0)
    # 尝试创建带 middleware 和 state_schema 的 Agent
    try:
        agent = create_agent(
            model=model,
            tools=all_tools,
            middleware=middleware_list if middleware_list else (),
            state_schema=state_schema,
            system_prompt=system_prompt,
            debug=config.verbose
        )
        logger.info("Agent created with middleware and state_schema support")
    # 兼容性回退：去掉 state_schema
    except TypeError as e:
        logger.warning(f"Falling back to simplified agent creation: {e}")
        try:
            agent = create_agent(
                model=model,
                tools=all_tools,
                middleware=middleware_list if middleware_list else (),
                system_prompt=system_prompt,
            )
            logger.info("Agent created with middleware support (no state_schema)")
        # 最小回退：仅注册工具
        except TypeError:
            agent = create_agent(
                model=model,
                tools=all_tools,
            )
            logger.warning("Agent created without middleware - dynamic filtering disabled!")

    return SkillAgent(agent=agent, registry=registry, config=config)


def create_custom_agent(
    model: BaseChatModel,
    skills_dir: Path,
    state_mode: str = "replace",
    verbose: bool = False,
    **kwargs
) -> SkillAgent:
    # build custom config and create agent
    config = SkillSystemConfig(
        skills_dir=skills_dir,
        state_mode=state_mode,
        verbose=verbose,
        **kwargs
    )
    return create_skill_agent(model=model, config=config)
