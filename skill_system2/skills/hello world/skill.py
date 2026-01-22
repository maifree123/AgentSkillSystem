from pathlib import Path
from langchain_core.tools import tool

from skill_system2.core.base_skill import BaseSkill, SkillMetadata

class HelloWorldSkill(BaseSkill):
    # metadata: name + description + tags
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="hello_world",
            description="A simple hello world skill.",
            version="1.0.0",
            tags=["demo", "hello"]
        )
    def get_tools(self):
        @tool
        def say_hello(name: str = "world") -> str:
            """Say hello to a name."""
            return f"Hello, {name}!"
        return [say_hello]
    
    #加载工具可见
    def get_loader_tool(self):
        @tool
        def load_hello_world() -> str:
            """Load hello_world skill."""
            return self.get_instructions()
        return load_hello_world
    
    #factory 功能要求注册
def create_skill(skill_dir: Path) -> BaseSkill:
    return HelloWorldSkill(skill_dir=skill_dir)