import asyncio
from agents.ontology_agent import OntologyBuilderAgent

agent = OntologyBuilderAgent()

async def run():
    cq = "Which sensors are suitable for detecting delamination in wooden beams exposed to dry environments?"
    result = await agent.run(cq)
    print(result)

asyncio.run(run())
