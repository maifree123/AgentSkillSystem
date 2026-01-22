from pathlib import Path
from langchain_openai import ChatOpenAI

from skill_system2 import create_skill_agent, SkillSystemConfig

# build config
config = SkillSystemConfig(
    skills_dir=Path("skill_system2/skills"),
    state_mode="replace",
    verbose=True
)

# create agent
agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4o-mini"),
    config=config
)

# invoke
result = agent.invoke({
    "messages": [{"role": "user", "content": "Load hello world and greet Bob."}]
})

print(result)
