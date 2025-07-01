from .base_agent import BaseAgent
from kg_interface import KGInterface
from pathlib import Path
from langchain.schema import SystemMessage, HumanMessage # Added this import
from langchain.schema import SystemMessage, HumanMessage # Added this import

class ToolSelectorAgent(BaseAgent):
    def __init__(self):
        prompt = Path("prompts/tool_selector.txt").read_text()
        super().__init__(prompt)
        self.kg = KGInterface()

    async def run(self, plan_text: str) -> str:
        # Step 1: Extract entities from the plan_text using an LLM call
        # For this, we'll use the base agent's __call__ method with a specific extraction prompt
        # We need a temporary SystemMessage for this specific task
        extraction_prompt = """\
You are an expert entity extractor. From the provided inspection plan text, extract the primary material being inspected, the main defect or observation of concern, and the relevant environment.
Return the information as a simple JSON object with keys "material", "defect", and "environment".
If any piece of information is not clearly stated, use "unknown".

Example:
Plan Text: "Preliminary Inspection Plan for Concrete with observed Cracking in Humid environment..."
Output: {"material": "Concrete", "defect": "Cracking", "environment": "Humid"}

Plan Text: "Visual inspection of steel components is required. Look for signs of corrosion. The area is often wet."
Output: {"material": "Steel", "defect": "Corrosion", "environment": "wet"}
"""

        # Temporarily modify history for the extraction call
        # Ensure SystemMessage and HumanMessage are available from langchain.schema
        from langchain.schema import SystemMessage, HumanMessage # Explicit import inside method
        original_history = self.history.copy()
        self.history = [SystemMessage(content=extraction_prompt), HumanMessage(content=plan_text)]

        try:
            extraction_response = await self.llm.agenerate([self.history])
            extracted_json_str = extraction_response.generations[0][0].text
            # Restore original history
            self.history = original_history

            import json
            try:
                entities = json.loads(extracted_json_str)
                material = entities.get("material", "unknown")
                defect = entities.get("defect", "unknown")
                environment = entities.get("environment", "unknown")
            except json.JSONDecodeError:
                print(f"❌ ToolSelectorAgent: Failed to parse JSON from extraction: {extracted_json_str}")
                # Fallback or error handling - for now, pass "unknown" and let the main prompt handle it
                material, defect, environment = "unknown", "unknown", "unknown"

        except Exception as e:
            # Restore original history in case of error
            self.history = original_history
            print(f"❌ ToolSelectorAgent: LLM call for entity extraction failed: {str(e)}")
            return "# ERROR: Entity extraction failed in ToolSelectorAgent"

        if material == "unknown" or defect == "unknown":
            # If critical info is missing, we might not be able to proceed effectively.
            # The main prompt for tool selection might still work, or return a message asking for more clarity.
            print(f"⚠️ ToolSelectorAgent: Could not extract sufficient entities. Material: {material}, Defect: {defect}")
            # Proceeding with potentially "unknown" values, the LLM might ask for clarification or provide general advice.

        # Step 2: Use extracted entities with the existing structured logic
        # This part is similar to run_structured, but uses the extracted entities
        methods = self.kg.recommend_ndt_methods(material, defect, environment)
        sensors = self.kg.recommend_sensors(defect) # Assuming defect is the primary key for sensors

        method_text = "\n".join([f"- {m}" for m in methods]) or "No suitable NDT methods found in KG for extracted entities."
        sensor_text = "\n".join([f"- {s}" for s in sensors]) or "No recommended sensors found in KG for extracted defect."

        # Step 3: Pass KG recommendations and extracted entities to the main LLM prompt
        # The main prompt for ToolSelectorAgent (in prompts/tool_selector.txt) expects material, defect, environment context.
        context_for_main_prompt = (
            f"Material: {material}\n"
            f"Defect/Observation: {defect}\n"
            f"Environment: {environment}\n\n"
            f"KG Recommended NDT Methods based on these entities:\n{method_text}\n\n"
            f"KG Recommended Sensor Prioritization based on these entities:\n{sensor_text}\n\n"
            f"Based on the above information extracted from an initial plan and queried from the Knowledge Graph, "
            f"please summarize the best NDT methods and recommend top 1-2 sensors, explaining why they are appropriate."
        )

        # This call uses the agent's actual system prompt and history
        return await self(context_for_main_prompt)

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

