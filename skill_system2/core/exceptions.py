"""
Custom exceptions for the skill system.
"""


# 统一异常基类
class SkillError(Exception):
    """Base exception for the skill system."""


# 未找到技能异常
class SkillNotFoundError(SkillError, KeyError):
    """Raised when a skill name is not registered."""

    # 生成未找到技能的错误信息
    def __init__(self, skill_name: str):
        super().__init__(f"Skill not found: {skill_name}")


# 加载技能异常
class SkillLoadError(SkillError, RuntimeError):
    """Raised when a skill module fails to load."""

    # 生成加载失败的错误信息
    def __init__(self, skill_name: str, reason: str):
        super().__init__(f"Failed to load skill '{skill_name}': {reason}")


# 权限不足异常
class SkillPermissionError(SkillError):
    """Raised when the caller lacks permission to use a skill."""

    # 生成权限不足的错误信息
    def __init__(self, skill_name: str, required_permission: str):
        super().__init__(
            f"Permission denied for skill '{skill_name}': "
            f"requires '{required_permission}'"
        )
