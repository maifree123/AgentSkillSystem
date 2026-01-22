"""
Skill base class and metadata.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_core.tools import BaseTool

@dataclass
class SkillMetadata:
    """
    Skill metadata.
    """
    name: str
    description: str
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    visibility: str = "public"  # public/internal/private
    dependencies: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    author: Optional[str] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "visibility": self.visibility,
            "dependencies": self.dependencies,
            "required_permissions": self.required_permissions,
            "author": self.author,
            "enabled": self.enabled,
        }

class BaseSkill(ABC):
    """
    Base class for all skills.
    """

    def __init__(self, skill_dir: Optional[Path] = None):
        self.skill_dir = skill_dir
        self._metadata: Optional[SkillMetadata] = None

    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata:
        pass

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        pass

    @abstractmethod
    def get_loader_tool(self) -> BaseTool:
        pass

    def get_instructions(self) -> str:
        if self.skill_dir:
            instructions_file = self.skill_dir / "instructions.md"
            if instructions_file.exists():
                return instructions_file.read_text(encoding="utf-8")

        tools_desc = "\n".join(
            [f"- {t.name}: {t.description}" for t in self.get_tools()]
        )
        return (
            f"{self.metadata.description}\n\n"
            f"Available tools:\n{tools_desc}\n\n"
            f"Use these tools to accomplish tasks related to: "
            f"{', '.join(self.metadata.tags)}"
        )

    def validate(self) -> bool:
        if not self.metadata.name:
            raise ValueError("Skill name cannot be empty")
        if not self.metadata.description:
            raise ValueError("Skill description cannot be empty")
        if not self.get_tools():
            raise ValueError("Skill must provide at least one tool")
        if not self.get_loader_tool():
            raise ValueError("Skill must provide a loader tool")
        return True

    def __repr__(self) -> str:
        return f"<Skill: {self.metadata.name} v{self.metadata.version}>"
