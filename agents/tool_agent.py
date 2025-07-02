from .base_agent import BaseAgent
from kg_interface import KGInterface
from pathlib import Path
from langchain.schema import SystemMessage, HumanMessage # Keep for entity extraction if used
from langchain.tools import Tool
# Note: AgentExecutor and create_react_agent might require more specific imports
# depending on LangChain version and chosen agent type.
# For now, these are common imports.
# from langchain.agents import AgentExecutor, create_react_agent
# from langchain import hub

class ToolSelectorAgent(BaseAgent):
    def __init__(self):
        # The system prompt for this agent will now be more about its overall goal
        # and how it should use tools. This will be defined in prompts/tool_selector.txt
        # and loaded during the agent execution setup.
        # For BaseAgent, we can pass a generic placeholder or the path to the new prompt.
        # The actual ReAct prompt or function-calling prompt is more specialized.

        # Let's load the main prompt that will guide the LLM in its reasoning with tools.
        # This prompt (from prompts/tool_selector.txt) will be used in the LangChain agent setup.
        # For now, BaseAgent's system_prompt is less critical as the AgentExecutor will use its own.
        # We'll set a simple one for BaseAgent.
        super().__init__("You are an NDT Tool Selection assistant. Your goal is to select and justify NDT tools based on provided context and by using available tools to gather more information.")
        self.kg = KGInterface()

        # Define tools based on KGInterface methods
        # These descriptions are crucial for the LLM to know when to use each tool.
        self.tools = [
            Tool(
                name="get_initial_recommendations",
                func=self._get_initial_recommendations_wrapper, # Wrapper to handle string input
                description="Use this tool to get initial NDT method and sensor recommendations. Input must be a comma-separated string: 'material,defect,environment'. Example: 'Concrete,Cracking,Humid'",
            ),
            Tool(
                name="get_ndt_method_details",
                func=self.kg.get_ndt_method_structured_details,
                description="Use this tool to get detailed information about a specific NDT method (description, category, cost, capabilities, limitations, risks). Input is the exact NDT method name.",
            ),
            Tool(
                name="get_material_details",
                func=self.kg.get_material_structured_details,
                description="Use this tool to get details about a specific material (description, common applications). Input is the exact material name.",
            ),
            Tool(
                name="get_defect_details",
                func=self.kg.get_defect_structured_details,
                description="Use this tool to get a detailed description of a specific defect/observation. Input is the exact defect name.",
            ),
        ]

        # Placeholder for AgentExecutor - full setup is complex and deferred.
        # For now, we will simulate a simplified flow in run/run_structured
        # to use the tools' functions directly for context gathering.
        self.agent_executor = None
        # try:
        #     react_prompt_template = hub.pull("hwchase17/react") # Requires internet
        #     agent = create_react_agent(self.llm, self.tools, react_prompt_template)
        #     self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True, max_iterations=5)
        # except Exception as e:
        #     print(f"Could not initialize ReAct agent executor: {e}. ToolSelectorAgent will use a simplified direct LLM call.")
        #     self.agent_executor = None


    def _get_initial_recommendations_wrapper(self, input_str: str) -> dict:
        try:
            parts = [s.strip() for s in input_str.split(",")]
            if len(parts) == 3:
                material, defect, environment = parts
                return self.kg.get_initial_recommendations_structured(material, defect, environment)
            else:
                return {"error": "Input string for get_initial_recommendations must be 3 comma-separated values: material, defect, environment."}
        except Exception as e:
            return {"error": f"Error in get_initial_recommendations_wrapper: {str(e)}"}

    def _parse_list_from_llm_output(self, llm_output: str, header: str) -> list[str]:
        try:
            for line in llm_output.splitlines():
                if line.startswith(header):
                    content = line.split(header, 1)[1].strip()
                    if content.startswith("[") and content.endswith("]"):
                        content = content[1:-1]
                        if not content: return []
                        return [item.strip() for item in content.split(",")]
            return []
        except Exception as e:
            print(f"Error parsing list with header '{header}' from LLM output: {e}")
            return []

    async def _call_llm_with_constructed_context(self, material: str, defect: str, environment: str) -> str:
        """
        Helper to construct context and call LLM. This simulates a single RAG-enhanced call
        instead of a full agentic loop for now.
        """
        # 1. Get initial recommendations
        initial_recs = self.kg.get_initial_recommendations_structured(material, defect, environment)
        rec_methods = initial_recs.get("recommended_methods", [])
        rec_sensors = initial_recs.get("recommended_sensors", [])

        # 2. Get details for recommended methods
        method_details_rag_parts = []
        if rec_methods:
            for method_name in rec_methods:
                details = self.kg.get_ndt_method_structured_details(method_name)
                if details:
                    # Format details nicely for the prompt
                    detail_str = f"Details for NDT Method '{method_name}':\n"
                    for key, value in details.items():
                        if value: # Only include if value exists
                            if isinstance(value, list) and key == "potential_risks":
                                if value: # If list is not empty
                                    detail_str += f"  Potential Risks:\n"
                                    for risk in value:
                                        detail_str += f"    - {risk.get('riskName', 'Unnamed Risk')}: {risk.get('riskDescription', 'N/A')} (Mitigation: {risk.get('mitigationSuggestion', 'N/A')})\n"
                            else:
                                detail_str += f"  {key.replace('_', ' ').title()}: {value}\n"
                    method_details_rag_parts.append(detail_str)

        # 3. Get material and defect details
        material_details_dict = self.kg.get_material_structured_details(material)
        defect_details_dict = self.kg.get_defect_structured_details(defect)

        rag_context_parts = []
        if material_details_dict:
            rag_context_parts.append(f"--- Material Details for {material} ---\n{str(material_details_dict)}")
        if defect_details_dict:
            rag_context_parts.append(f"--- Defect Details for {defect} ---\n{str(defect_details_dict)}")
        if method_details_rag_parts:
            rag_context_parts.append("--- NDT Method Details (from KG) ---\n" + "\n".join(method_details_rag_parts))

        full_rag_context = "\n\n".join(rag_context_parts)

        # This is the context that the prompt in prompts/tool_selector.txt expects
        llm_input_context = (
            f"Material: {material}\n"
            f"Defect/Observation: {defect}\n"
            f"Environment: {environment}\n\n"
            f"KG Recommended NDT Method Names (Initial): {', '.join(rec_methods) if rec_methods else 'None'}\n"
            f"KG Recommended Sensor Names (Initial): {', '.join(rec_sensors) if rec_sensors else 'None'}\n\n"
            f"Detailed Information from Knowledge Graph:\n{full_rag_context if full_rag_context else 'No specific details retrieved.'}\n\n"
            f"--- End of automatically provided context ---\n"
        )

        # Use the main prompt for this agent, which is now loaded from prompts/tool_selector.txt by BaseAgent
        # The BaseAgent's __call__ method will use its self.system_prompt
        # We need to ensure BaseAgent is initialized with the content of prompts/tool_selector.txt
        # This was a misunderstanding in my previous BaseAgent init for ToolSelectorAgent.
        # The BaseAgent should be initialized with the specific detailed prompt.

        # For this call, we will temporarily set the system prompt if BaseAgent wasn't initialized correctly,
        # or rely on the fact that it IS initialized with the correct prompt.
        # The `super().__init__(system_prompt_from_file)` should handle this.

        # The content of prompts/tool_selector.txt is the system message.
        # llm_input_context is the human message.

        # This is a temporary measure. The ideal way is to re-initialize BaseAgent with the right system prompt
        # or ensure the prompt in prompts/tool_selector.txt is used as system prompt.
        # For now, I'll assume the BaseAgent was initialized with the content of 'prompts/tool_selector.txt'

        return await self(llm_input_context) # self() is BaseAgent.__call__


    async def run(self, plan_text: str) -> dict:
        # Step 1: Extract material, defect, environment from plan_text (as before)
        extraction_prompt_content = """\
You are an expert entity extractor. From the provided inspection plan text, extract the primary material being inspected, the main defect or observation of concern, and the relevant environment.
Return the information as a simple JSON object with keys "material", "defect", and "environment".
If any piece of information is not clearly stated, use "unknown".
Example:
Plan Text: "Preliminary Inspection Plan for Concrete with observed Cracking in Humid environment..."
Output: {"material": "Concrete", "defect": "Cracking", "environment": "Humid"}"""

        # Temporarily use a different system prompt for extraction
        original_system_prompt = self.system_prompt
        self.system_prompt = extraction_prompt_content

        extracted_json_str = await self(plan_text) # Call LLM for extraction

        self.system_prompt = original_system_prompt # Restore original system prompt

        material, defect, environment = "unknown", "unknown", "unknown"
        try:
            import json
            entities = json.loads(extracted_json_str)
            material = entities.get("material", "unknown")
            defect = entities.get("defect", "unknown")
            environment = entities.get("environment", "unknown")
        except json.JSONDecodeError:
            print(f"ToolSelectorAgent (run): Failed to parse JSON from extraction: {extracted_json_str}")
        except Exception as e:
            print(f"ToolSelectorAgent (run): Error processing extraction: {e}")


        if material == "unknown" or defect == "unknown":
            raw_llm_output = "Could not extract sufficient material/defect information from the input plan to proceed with tool selection."
        else:
            # Now call the refactored LLM call with constructed context
            raw_llm_output = await self._call_llm_with_constructed_context(material, defect, environment)

        recommended_methods = self._parse_list_from_llm_output(raw_llm_output, "Recommended Method Names:")
        recommended_sensors = self._parse_list_from_llm_output(raw_llm_output, "Recommended Sensor Names:")
        return {
            "summary_text": raw_llm_output,
            "recommended_methods": recommended_methods,
            "recommended_sensors": recommended_sensors
        }

    async def run_structured(self, material: str, defect: str, environment: str) -> dict:
        raw_llm_output = await self._call_llm_with_constructed_context(material, defect, environment)

        recommended_methods = self._parse_list_from_llm_output(raw_llm_output, "Recommended Method Names:")
        recommended_sensors = self._parse_list_from_llm_output(raw_llm_output, "Recommended Sensor Names:")
        return {
            "summary_text": raw_llm_output,
            "recommended_methods": recommended_methods,
            "recommended_sensors": recommended_sensors
        }

```
**Important Changes & Notes on this Overwrite:**

*   **No AgentExecutor Yet:** I have *commented out* the `AgentExecutor` setup (`hub.pull`, `create_react_agent`, `AgentExecutor(...)`). Fully implementing and debugging a ReAct agent with Ollama is complex and prone to issues with prompt templates, parsing, and iteration limits, especially without live testing.
*   **Simulated RAG Call:** Instead, I've created a helper `_call_llm_with_constructed_context`. This method now performs the sequence of KG calls (get initial recs, then details for methods, material, defect) and constructs a single large context string. This context is then passed to the LLM in one go using the agent's main prompt (from `prompts/tool_selector.txt`). This is similar to the previous RAG but uses the new structured KG methods. This is an *intermediate step* towards full function calling. The LLM doesn't call tools itself yet.
*   **Tool Definitions:** The `self.tools` list is defined with `Tool` objects. These are ready for when we implement the `AgentExecutor`. The `_get_initial_recommendations_wrapper` is included to handle the string input expected by ReAct tools.
*   **BaseAgent Initialization:** I've noted that `BaseAgent` for `ToolSelectorAgent` should ideally be initialized with the content of `prompts/tool_selector.txt` as its system prompt for the `_call_llm_with_constructed_context` to work as intended. I will make this adjustment to `ToolSelectorAgent.__init__` now.
*   **Entity Extraction in `run()`:** The `run()` method still uses a separate LLM call to extract entities from `plan_text`. This could also become a tool call in a full AgentExecutor setup.

Let me first adjust the `ToolSelectorAgent.__init__` to correctly load its main prompt.
