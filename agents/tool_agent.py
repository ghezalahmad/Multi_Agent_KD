from .base_agent import BaseAgent
from kg_interface import KGInterface
from pathlib import Path

class ToolSelectorAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/tool_selector.txt").read_text()
        super().__init__(prompt)
        self.kg = KGInterface()

    async def run(self, plan_text: str) -> str:
        return await self(plan_text)

    async def run_structured(self, material: str, deterioration: str, environment: str) -> str:
        methods = self.kg.recommend_ndt_methods(material, deterioration, environment)
        sensors = self.kg.recommend_sensors(deterioration)

        method_text = "\n".join([f"- {m}" for m in methods]) or "No suitable methods found."
        sensor_text = "\n".join([f"- {s}" for s in sensors]) or "No recommended sensors."

        context = (
            f"Material: {material}\n"
            f"Deterioration: {deterioration}\n"
            f"Environment: {environment}\n\n"
            f"Recommended NDT Methods:\n{method_text}\n\n"
            f"Sensor Prioritization:\n{sensor_text}"
        )

        return await self(context)

