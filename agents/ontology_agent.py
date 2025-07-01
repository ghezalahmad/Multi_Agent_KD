from .base_agent import BaseAgent
from pathlib import Path

class OntologyBuilderAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/ontology_builder.txt").read_text()
        super().__init__(prompt, temperature=0.0)

    async def run(self, cq: str) -> str:
        return await self(cq)
