# agents/planner_agent.py

from .base_agent import BaseAgent
from pathlib import Path
from .base_agent import BaseAgent
from agents.critique_agent import CritiqueAgent
from agents.forecaster_agent import ForecasterAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.tool_agent import ToolSelectorAgent
from utils.session_utils import log_agent_response  # ✅ Import the logger
from pathlib import Path
from datetime import date
import asyncio


class PlannerAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/planner.txt").read_text()
        super().__init__(prompt, temperature=0.0)

    # In agents/planner_agent.py
    async def __call__(self, user_msg: str, plan_id: str = None) -> str:
        plan_text = await super().__call__(user_msg)
        if plan_id:
            log_agent_response(plan_id, "PlannerAgent", plan_text, user_input=user_msg)
        return plan_text

