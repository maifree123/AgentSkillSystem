"""
Basic tests for skill_system2.
"""
from pathlib import Path
import sys

# add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skill_system2.core.registry import SkillRegistry
from skill_system2.core.base_skill import BaseSkill, SkillMetadata
from skill_system2.core.exceptions import SkillNotFoundError

from langchain_core.tools import tool

class TestSkill(BaseSkill):
    # minimal metadata
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="test_skill",
            description="Test skill",
            version="1.0.0"
        )

    # one real tool
    def get_tools(self):
        @tool
        def test_tool() -> str:
            """A test tool."""
            return "ok"
        return [test_tool]

    # loader tool
    def get_loader_tool(self):
        @tool
        def test_loader() -> str:
            """Load test skill."""
            return "loaded"
        return test_loader

def test_registry_init():
    # registry starts empty
    registry = SkillRegistry()
    assert len(registry) == 0

def test_register_and_get():
    registry = SkillRegistry()
    registry.register(TestSkill())
    assert "test_skill" in registry
    assert registry.get("test_skill").metadata.name == "test_skill"

def test_get_nonexistent():
    registry = SkillRegistry()
    try:
        registry.get("missing")
        assert False, "expected SkillNotFoundError"
    except SkillNotFoundError:
        assert True
