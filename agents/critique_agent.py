from .base_agent import BaseAgent
from pathlib import Path
from kg_interface import KGInterface # Will be needed for RAG

class CritiqueAgent(BaseAgent):
    def __init__(self):
        prompt_path = Path("prompts/critique_agent.txt")
        if not prompt_path.exists():
            # Fallback or error if prompt file is missing, though it should have been created
            system_prompt = "You are a helpful NDT critique agent."
            print(f"Warning: Prompt file {prompt_path} not found. Using default system prompt.")
        else:
            system_prompt = prompt_path.read_text()

        super().__init__(system_prompt, temperature=0.1) # Critique should be fairly consistent
        self.kg = KGInterface() # For RAG access

    async def run(self, critique_context: str) -> str:
        """
        Runs the CritiqueAgent with the given context.
        The critique_context should be a pre-formatted string containing all necessary information
        as outlined in prompts/critique_agent.txt (scenario, proposed approach, RAG details).
        """
        # The core logic for preparing critique_context (including RAG) will be
        # handled in app/main.py before calling this agent.
        # This agent primarily passes the fully formed context to the LLM.

        critique_output = await self(critique_context) # Call the BaseAgent's __call__ method
        return critique_output

if __name__ == '__main__':
    # Example usage (requires running an Ollama server with a model like mistral)
    import asyncio

    async def main():
        agent = CritiqueAgent()

        # This example context needs to be carefully constructed to match what the prompt expects.
        # In real usage, this context will be built dynamically in app/main.py
        # using outputs from other agents and RAG data from KGInterface.
        example_context = """\
**Input Context Provided to You:**
1.  **Scenario:**
    *   Material: Concrete (Description: A composite material...)
    *   Defect/Observation: Cracking (Detailed Description: A linear fracture...)
    *   Environment: Humid
2.  **Proposed NDT Approach by ToolSelectorAgent:**
    *   Summary Text: "For cracking in humid concrete, Ultrasonic Testing is recommended due to its volumetric capabilities. A standard acoustic sensor should suffice."
    *   Recommended Method Names: [Ultrasonic Testing]
3.  **Detailed NDT Method Information (from Knowledge Graph for RAG):**
    *   For Ultrasonic Testing:
        *   Description: Uses high-frequency sound waves to detect internal flaws...
        *   Category: Volumetric
        *   Cost Estimate: Medium
        *   Detection Capabilities: Detects internal and surface flaws like cracks, voids...
        *   Applicable Materials Note: Requires good acoustic coupling...
        *   Method Limitations: Requires skilled operator; surface must be accessible...

---
Begin Critique:
"""
        print("Sending example context to CritiqueAgent:")
        # print(example_context) # Uncomment to see the full context being sent

        response = await agent.run(example_context)
        print("\nCritiqueAgent Response:")
        print(response)

    # asyncio.run(main()) # Commented out for typical module usage
```
