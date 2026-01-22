"""
Compatibility shim for settings module name.
"""

from .setting import SkillSystemConfig, load_config, DEFAULT_CONFIG

__all__ = [
    "SkillSystemConfig",
    "load_config",
    "DEFAULT_CONFIG",
]
