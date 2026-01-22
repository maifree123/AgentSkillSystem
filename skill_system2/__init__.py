"""
Claude-style Skills System for LangChain/LangGraph (skill_system2).
"""

from .core import (
    BaseSkill,
    SkillMetadata,
    SkillState,
    SkillRegistry,
    skill_list_reducer,
    skill_list_accumulator,
    skill_list_fifo,
)
from .core.state import SkillStateAccumulative, SkillStateFIFO
from .middleware import SkillMiddleware
from .config import SkillSystemConfig, load_config
from .agent_factory import create_skill_agent, SkillAgent, create_custom_agent
from .utils import setup_logger, get_logger

try:
    from .models import DeepSeekReasonerChatModel
except ImportError:
    DeepSeekReasonerChatModel = None

__version__ = "1.0.0"
__author__ = "MuyuCheney"

__all__ = [
    "BaseSkill",
    "SkillMetadata",
    "SkillState",
    "SkillRegistry",
    "skill_list_reducer",
    "skill_list_accumulator",
    "skill_list_fifo",
    "SkillStateAccumulative",
    "SkillStateFIFO",
    "SkillMiddleware",
    "SkillSystemConfig",
    "load_config",
    "create_skill_agent",
    "create_custom_agent",
    "SkillAgent",
    "setup_logger",
    "get_logger",
    "DeepSeekReasonerChatModel",
]
