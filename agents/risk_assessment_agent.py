from .base_agent import BaseAgent
from pathlib import Path
from kg_interface import KGInterface # Will be needed for RAG data access via app/main.py

class RiskAssessmentAgent(BaseAgent):
    def __init__(self):
        prompt_path = Path("prompts/risk_assessment_agent.txt")
        if not prompt_path.exists():
            system_prompt = "You are a helpful NDT risk assessment agent."
            print(f"Warning: Prompt file {prompt_path} not found. Using default system prompt.")
        else:
            system_prompt = prompt_path.read_text()

        super().__init__(system_prompt, temperature=0.0) # Risks should be identified consistently
        # self.kg = KGInterface() # KG access will be indirect via context prepared by app/main.py

    async def run(self, risk_assessment_context: str) -> str:
        """
        Runs the RiskAssessmentAgent with the given context.
        The risk_assessment_context should be a pre-formatted string containing all necessary
        information as outlined in prompts/risk_assessment_agent.txt
        (scenario, proposed methods, and RAG details for these methods including their risks).
        """
        # The core logic for preparing risk_assessment_context (including RAG for method details & risks)
        # will be handled in app/main.py before calling this agent.

        risk_assessment_output = await self(risk_assessment_context) # Call BaseAgent's __call__
        return risk_assessment_output

if __name__ == '__main__':
    # Example usage (requires running an Ollama server with a model like mistral)
    import asyncio

    async def main():
        # This example assumes that the KGInterface and RAG data fetching
        # would be done externally and formatted into the context string.
        agent = RiskAssessmentAgent()

        example_context = """\
**Input Context Provided to You:**
1.  **Scenario Context:**
    *   Material: Concrete
    *   Defect/Observation: Cracking
    *   Environment: Outdoor, ground level
2.  **Proposed NDT Methods:**
    *   Visual Inspection, Ultrasonic Testing
3.  **Detailed NDT Method Information (from Knowledge Graph for RAG):**
    *   Method: Visual Inspection
        *   Description: The oldest and most common NDT method...
        *   Category: Surface
        *   Method Limitations: Only detects surface-breaking defects...
        *   Potential Risks:
            *   Safety Hazard - Working at Heights: Risk of falls... (Mitigation: Use fall arrest systems...)
                  (Note: This risk might be deemed not applicable by LLM if env is ground level)
    *   Method: Ultrasonic Testing
        *   Description: Uses high-frequency sound waves...
        *   Category: Volumetric
        *   Method Limitations: Requires skilled operator; surface must be accessible...
        *   Potential Risks:
            *   Equipment Accessibility Issue: The inspection area may be difficult to access... (Mitigation: Plan access routes...)

---
Begin Risk Assessment:
"""
        print("Sending example context to RiskAssessmentAgent:")
        # print(example_context)

        response = await agent.run(example_context)
        print("\nRiskAssessmentAgent Response:")
        print(response)

    # To run this example:
    # 1. Ensure Ollama is running with a model (e.g., `ollama run mistral`)
    # 2. Uncomment the asyncio.run(main()) line below.
    # 3. Run this file directly: `python agents/risk_assessment_agent.py`
    # asyncio.run(main()) # Commented out for typical module usage
```
