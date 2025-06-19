from .base_agent import BaseAgent
from pathlib import Path

class PlannerAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/planner.txt").read_text()
        super().__init__(prompt, temperature=0.0)

    async def run(self, user_input: str) -> str:
        return await self(user_input)
