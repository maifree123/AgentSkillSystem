"""
状态管理，轨道负载技能。
"""

from typing import List, Annotated
from langgraph.graph import MessagesState

#替换模式： 总是使用新的list
    # replace mode: always use the new list
def skill_list_reducer(current: List[str], new: List[str]) -> List[str]:
    return new

#累积模式：合并和重复数据删除
def skill_list_accumulator(current: List[str], new: List[str]) -> List[str]:
    if not current:
        return new
    combined = current + [s for s in new if s not in current]
    return combined

#FIFO 模式 reducer 工厂
# FIFO mode: keep only the latest N skills
def skill_list_fifo(max_skills: int = 3):
    def reducer(current: List[str], new: List[str]) -> List[str]:
        if not current:
            return new[:max_skills]
        combined = current + [s for s in new if s not in current]
        return combined[-max_skills:]
    return reducer

class SkillState(MessagesState):
    """
    State schema with loaded skills.
    """
    skills_loaded: Annotated[List[str], skill_list_reducer] = []


class SkillStateAccumulative(MessagesState):
    """Accumulate mode."""
    skills_loaded: Annotated[List[str], skill_list_accumulator] = []

class SkillStateFIFO(MessagesState):
    """FIFO mode: max 3 skills."""
    skills_loaded: Annotated[List[str], skill_list_fifo(3)] = []
