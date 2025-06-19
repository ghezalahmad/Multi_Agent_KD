from .base_agent import BaseAgent
from pathlib import Path
import datetime as dt

class ForecasterAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/forecaster.txt").read_text()
        super().__init__(prompt)

    async def run(self, context: str) -> str:
        today = dt.date.today().isoformat()
        msg   = f"{context}\nToday is {today}. Predict degradation trajectory."
        return await self(msg)
