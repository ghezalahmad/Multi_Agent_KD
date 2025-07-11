from .base_agent import BaseAgent
from agents.critique_agent import CritiqueAgent
from agents.forecaster_agent import ForecasterAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from pathlib import Path
from datetime import date


class PlannerAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/planner.txt").read_text()
        super().__init__(prompt, temperature=0.0)

    async def __call__(self, user_msg: str) -> str:
        # 🧭 Step 1: Planner generates initial plan
        plan_text = await super().__call__(user_msg)

        # 🧐 Step 2: CritiqueAgent evaluates the plan
        critique_agent = CritiqueAgent()
        critique_input = f"""**Scenario Context (from user input & planner):**
User Input: {user_msg}
Planner Output: {plan_text}

**Proposed NDT Approach by ToolSelectorAgent:**
Agent stopped due to iteration limit or time limit.
**Detailed NDT Method Information (from Knowledge Graph for RAG):**
"""
        critique_response = await critique_agent(critique_input)

        # 🔮 Step 3: ForecasterAgent predicts defect evolution
        forecaster_agent = ForecasterAgent()
        today = date.today().isoformat()
        forecast_input = f"""{critique_response}

Today is {today}. Predict degradation trajectory."""
        forecast_response = await forecaster_agent(forecast_input)

        # ⚠️ Step 4: RiskAssessmentAgent analyzes potential inspection risks
        risk_agent = RiskAssessmentAgent()
        risk_input = f"""User Input: {user_msg}
Planner Output: {plan_text}
Forecast Summary: {forecast_response}

Evaluate potential safety, access, and equipment-related risks for the proposed NDT scenario."""
        risk_response = await risk_agent(risk_input)

        # 📦 Step 5: Combine everything
        final_response = f"""🧭 **Planner's Proposed Plan:**
{plan_text}

🧐 **Critique Agent's Feedback:**
{critique_response}

🔮 **Forecaster Agent's Prediction:**
{forecast_response}

⚠️ **Risk Assessment Agent's Analysis:**
{risk_response}
"""
        return final_response
