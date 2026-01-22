"""
Docstring for skill_system2.config.setting
目的：集中管理技能目录、状态模式、日志、过滤等配置，便于启动时统一加载。
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import yaml


@dataclass
class SkillSystemConfig:
    """
    Skill System config.
    """
    skills_dir: Path = Path("./skills")

    state_mode: str = "replace"
    max_concurrent_skills: int = 3

    verbose: bool = False
    log_level: str = "INFO"

    default_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    middleware_enabled: bool = True

    auto_discover: bool = True
    skill_module_name: str = "skill"

    filter_by_visibility: bool = True
    allowed_visibilities: List[str] = field(default_factory=lambda: ["public"])

    user_permissions: List[str] = field(default_factory=list)
    custom_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.skills_dir, Path):
            self.skills_dir = Path(self.skills_dir)

        valid_modes = ["replace", "accumulate", "fifo"]
        if self.state_mode not in valid_modes:
            raise ValueError(
                f"Invalid state_mode: {self.state_mode}. "
                f"Must be one of {valid_modes}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skills_dir": str(self.skills_dir),
            "state_mode": self.state_mode,
            "max_concurrent_skills": self.max_concurrent_skills,
            "verbose": self.verbose,
            "log_level": self.log_level,
            "default_model": self.default_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "middleware_enabled": self.middleware_enabled,
            "auto_discover": self.auto_discover,
            "skill_module_name": self.skill_module_name,
            "filter_by_visibility": self.filter_by_visibility,
            "allowed_visibilities": self.allowed_visibilities,
            "user_permissions": self.user_permissions,
            "custom_config": self.custom_config,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SkillSystemConfig":
        return cls(**config_dict)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "SkillSystemConfig":
        with open(yaml_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

    def save_to_yaml(self, yaml_path: Path) -> None:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


def load_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "SKILL_SYSTEM_"
) -> SkillSystemConfig:
    config_dict = {}

    if config_path and config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

    env_mappings = {
        f"{env_prefix}SKILLS_DIR": "skills_dir",
        f"{env_prefix}STATE_MODE": "state_mode",
        f"{env_prefix}MAX_CONCURRENT_SKILLS": "max_concurrent_skills",
        f"{env_prefix}VERBOSE": "verbose",
        f"{env_prefix}LOG_LEVEL": "log_level",
        f"{env_prefix}DEFAULT_MODEL": "default_model",
        f"{env_prefix}TEMPERATURE": "temperature",
        f"{env_prefix}MIDDLEWARE_ENABLED": "middleware_enabled",
        f"{env_prefix}AUTO_DISCOVER": "auto_discover",
    }

    for env_key, config_key in env_mappings.items():
        if env_key in os.environ:
            value = os.environ[env_key]
            if config_key in ["max_concurrent_skills"]:
                value = int(value)
            elif config_key in ["temperature"]:
                value = float(value)
            elif config_key in ["verbose", "middleware_enabled", "auto_discover"]:
                value = value.lower() in ["true", "1", "yes"]
            config_dict[config_key] = value

    return SkillSystemConfig.from_dict(config_dict)


DEFAULT_CONFIG = SkillSystemConfig()
