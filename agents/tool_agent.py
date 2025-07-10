from .base_agent import BaseAgent
from kg_interface import KGInterface
from pathlib import Path
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.prompts import PromptTemplate # For fallback prompt
import json

# Basic ReAct prompt template string (fallback if hub.pull fails)
# This is a simplified version of hwchase17/react. For best results, the hub version is preferred.
FALLBACK_REACT_PROMPT_TEMPLATE = """\
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question, which must include the specially formatted lists 'Recommended Method Names: [...]' and 'Recommended Sensor Names: [...]' as specified in the main task.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

class ToolSelectorAgent(BaseAgent):
    def __init__(self):
        # Load the main system prompt for this agent from the file.
        # This prompt contains the detailed instructions for the ReAct agent.
        prompt_file_path = Path("prompts/tool_selector.txt")
        try:
            system_prompt_for_agent = prompt_file_path.read_text()
        except FileNotFoundError:
            print(f"ERROR: prompts/tool_selector.txt not found. ToolSelectorAgent may not function correctly.")
            system_prompt_for_agent = "You are an NDT Tool Selection assistant. Select tools and justify." # Basic fallback

        super().__init__(system_prompt_for_agent) # Initialize BaseAgent with the correct system prompt
        self.kg = KGInterface()

        self.tools = [
            Tool(
                name="get_initial_recommendations",
                func=self._get_initial_recommendations_wrapper,
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

        try:
            # The prompt from prompts/tool_selector.txt will contain the core instructions for the LLM's reasoning.
            # This will be used as the 'instructions' part of the ReAct prompt.
            # The ReAct prompt template itself (hwchase17/react) provides the Thought/Action/Observation structure.
            # LangChain's create_react_agent typically expects a prompt that can format {tools}, {tool_names}, {input}, {agent_scratchpad}.
            # The prompt from tool_selector.txt needs to be the main instruction set.
            # For ReAct, we often don't pass a full prompt object to create_react_agent, but rather use a template
            # that includes placeholders for instructions, tools, etc.
            # The instructions will come from our prompts/tool_selector.txt file.

            # For now, we'll load our specific instructions and they will be part of the input to the agent executor.
            # The ReAct prompt template from the hub will provide the structure.
            react_prompt_template = hub.pull("hwchase17/react")
        except Exception as e:
            print(f"ERROR: Could not pull ReAct prompt from LangChain Hub: {e}. Using basic fallback. Functionality may be limited.")
            react_prompt_template = PromptTemplate.from_template(FALLBACK_REACT_PROMPT_TEMPLATE)

        agent = create_react_agent(self.llm, self.tools, react_prompt_template)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors="Check your output and make sure it conforms to the expected A ROUGH PARSING OF THE OUTPUT OF YOUR ACTION IS AVAILABLE TO YOU. IF IT IS NOT PERFECTLY PARSED, YOU SHOULD TRY TO PARSE MORE CAREFULLY. IF THE OUTPUT IS NOT AS EXPECTED, YOU SHOULD TRY A DIFFERENT ACTION.", # More robust error handling
            max_iterations=10 # Increased max_iterations
        )

    def _get_initial_recommendations_wrapper(self, input_str: str) -> dict:
        try:
            parts = [s.strip().strip("'\"") for s in input_str.split(",")]
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
            # Fallback: Check if the entire output is just the list (e.g. "Method1, Method2")
            if header == "Recommended Method Names:" and not any(h in llm_output for h in ["Recommended Sensor Names:", "Thought:", "Action:"]) :
                 if llm_output.strip().startswith("[") and llm_output.strip().endswith("]"):
                     content = llm_output.strip()[1:-1]
                     if not content: return []
                     return [item.strip() for item in content.split(",")]

            return []
        except Exception as e:
            print(f"Error parsing list with header '{header}' from LLM output: {e}")
            return []

    async def run(self, plan_text: str) -> dict:
        # Step 1: Extract material, defect, environment from plan_text
        extraction_prompt_content = """\
You are an expert entity extractor. From the provided inspection plan text, extract the primary material being inspected, the main defect or observation of concern, and the relevant environment.
Return the information as a simple JSON object with keys "material", "defect", and "environment".
If any piece of information is not clearly stated, use "unknown".
Example:
Plan Text: "Preliminary Inspection Plan for Concrete with observed Cracking in Humid environment..."
Output: {"material": "Concrete", "defect": "Cracking", "environment": "Humid"}"""

        temp_extraction_history = [SystemMessage(content=extraction_prompt_content), HumanMessage(content=plan_text)]
        raw_llm_output_for_extraction = ""
        try:
            extraction_llm_response = await self.llm.agenerate([temp_extraction_history])
            extracted_json_str = extraction_llm_response.generations[0][0].text
        except Exception as e:
            print(f"ToolSelectorAgent (run) entity extraction LLM call failed: {e}")
            extracted_json_str = "{}"

        material, defect, environment = "unknown", "unknown", "unknown"
        try:
            import json
            entities = json.loads(extracted_json_str)
            material = entities.get("material", "unknown")
            defect = entities.get("defect", "unknown")
            environment = entities.get("environment", "unknown")
            # Handle cases where defect/material/environment are lists
            if isinstance(material, list):
                material = ", ".join(str(x) for x in material)
            if isinstance(defect, list):
                defect = ", ".join(str(x) for x in defect)
            if isinstance(environment, list):
                environment = ", ".join(str(x) for x in environment)
        # ...existing code...
        except json.JSONDecodeError:
            print(f"ToolSelectorAgent (run): Failed to parse JSON from extraction: {extracted_json_str}")
            # Fallback: Try to extract keywords from the plan_text directly
            import re
            material_match = re.search(r"material\s*[:=]\s*([A-Za-z0-9_ -]+)", plan_text, re.IGNORECASE)
            defect_match = re.search(r"(defect|observation)\s*[:=]\s*([A-Za-z0-9_ -]+)", plan_text, re.IGNORECASE)
            environment_match = re.search(r"environment\s*[:=]\s*([A-Za-z0-9_ -]+)", plan_text, re.IGNORECASE)
            if material_match:
                material = material_match.group(1).strip()
            else:
                # Try to find common material keywords
                for mat in ["concrete", "steel", "aluminum", "wood"]:
                    if mat in plan_text.lower():
                        material = mat.capitalize()
                        break
            if defect_match:
                defect = defect_match.group(2).strip()
            else:
                for defect_kw in ["crack", "corrosion", "delamination", "void"]:
                    if defect_kw in plan_text.lower():
                        defect = defect_kw.capitalize()
                        break
            if environment_match:
                environment = environment_match.group(1).strip()
            else:
                for env in ["humid", "dry", "marine", "underground"]:
                    if env in plan_text.lower():
                        environment = env.capitalize()
                        break
        # ...existing code...

        if material == "unknown" or defect == "unknown" or environment == "unknown":
            print(f"ToolSelectorAgent (run): Entity extraction resulted in unknowns: M={material}, D={defect}, E={environment}")
            if material == "unknown" or defect == "unknown":
                raw_llm_output_for_extraction = "Could not extract sufficient material/defect information from the input plan to proceed with tool selection. Please provide clearer details."
                return {
                    "summary_text": raw_llm_output_for_extraction,
                    "recommended_methods": [],
                    "recommended_sensors": []
                }

        # Now, run the agent executor with the extracted entities
        # The prompt in prompts/tool_selector.txt will be formatted with these.
        # The actual task for the ReAct agent is defined by the content of prompts/tool_selector.txt
        # which is loaded by BaseAgent and used by the LLM within the AgentExecutor.
        # We need to construct the input for the agent_executor carefully.
        # The ReAct prompt template expects an "input" variable.

        # The main instructions for the agent are in prompts/tool_selector.txt (which becomes BaseAgent's system_prompt)
        # The specific task for *this run* needs to be formulated.
        # The ReAct agent's prompt will include the system message (from tool_selector.txt)
        # and then the specific input for this run.

        main_instructions = Path("prompts/tool_selector.txt").read_text()
        # We need to ensure the {tools} and {tool_names} are formatted correctly for the react_prompt_template
        # And then the {input} should be the task-specific part.

        # The input to AgentExecutor should be a dictionary.
        # The 'input' key will be formatted into the ReAct prompt.
        # The 'intermediate_steps' or 'agent_scratchpad' is handled by the executor.

        # The prompt file itself acts as the core instruction set.
        # The input variable for the ReAct agent should be the specific scenario.
        agent_input = (
            f"Material: {material}\n"
            f"Defect/Observation: {defect}\n"
            f"Environment: {environment}\n"
            f"Your task is to select and justify the best NDT methods and sensors for this scenario, "
            f"using the available tools to gather information. "
            f"Ensure your final answer includes the specially formatted lists: "
            f"'Recommended Method Names: [...]' and 'Recommended Sensor Names: [...]'."
        )

        raw_agent_output = ""
        try:
            if self.agent_executor:
                # The agent's system prompt (from BaseAgent, loaded from tool_selector.txt)
                # should ideally be part of the react_prompt_template's construction,
                # or the create_react_agent should be given the full prompt.
                # For now, we assume create_react_agent combines self.llm (with its system prompt) and tools.
                # Let's ensure the prompt from file is correctly used.
                # The `create_react_agent` takes `prompt` as an argument.
                # We passed `self.react_prompt` (from hub or fallback) to it.
                # This `self.react_prompt` is a template that expects {input}, {tools}, {tool_names}, {agent_scratchpad}.
                # The instructions from `prompts/tool_selector.txt` need to be part of this.
                # This is a common point of confusion. The `system_message` of the LLM in `BaseAgent`
                # might conflict or be ignored by the ReAct prompt structure.
                # The ReAct prompt itself should contain the core "persona" and overall instructions.
                # The content of prompts/tool_selector.txt should be formatted *into* the ReAct prompt template.

                # This is where the actual prompt for the ReAct agent needs to be constructed.
                # The hwchase17/react prompt has {{input}}, {{tools}}, {{tool_names}}, {{agent_scratchpad}}
                # The instructions from prompts/tool_selector.txt should be part of the {{input}} or a custom system message part of the ReAct prompt.
                # For simplicity, let's try to make the "input" to the agent executor contain the core task derived from tool_selector.txt.
                # This is not ideal. The prompt file itself should be structured for ReAct.
                # For now, we'll pass the agent_input which summarizes the task.

                # The system prompt used by self.llm (from BaseAgent) should be the one from tool_selector.txt.
                # This is correctly set in __init__.
                # The AgentExecutor will use this LLM.

                result = await self.agent_executor.ainvoke({"input": agent_input})
                raw_agent_output = result.get("output", "")
            else: # Fallback if AgentExecutor failed to initialize
                raw_agent_output = "AgentExecutor not initialized. Cannot perform tool selection."
        except Exception as e:
            print(f"Error during ToolSelectorAgent agent_executor.ainvoke: {e}")
            raw_agent_output = f"# ERROR: Agent execution failed: {str(e)}"

        recommended_methods = self._parse_list_from_llm_output(raw_agent_output, "Recommended Method Names:")
        recommended_sensors = self._parse_list_from_llm_output(raw_agent_output, "Recommended Sensor Names:")
        return {
            "summary_text": raw_agent_output,
            "recommended_methods": recommended_methods,
            "recommended_sensors": recommended_sensors
        }

    async def run_structured(self, material: str, defect: str, environment: str) -> dict:
        agent_input = (
            f"Material: {material}\n"
            f"Defect/Observation: {defect}\n"
            f"Environment: {environment}\n"
            f"Your task is to select and justify the best NDT methods and sensors for this scenario, "
            f"using the available tools to gather information. "
            f"Ensure your final answer includes the specially formatted lists: "
            f"'Recommended Method Names: [...]' and 'Recommended Sensor Names: [...]'."
        )
        raw_agent_output = ""
        try:
            if self.agent_executor:
                result = await self.agent_executor.ainvoke({"input": agent_input})
                raw_agent_output = result.get("output", "")
            else:
                raw_agent_output = "AgentExecutor not initialized. Cannot perform tool selection."
        except Exception as e:
            print(f"Error during ToolSelectorAgent (structured) agent_executor.ainvoke: {e}")
            raw_agent_output = f"# ERROR: Agent execution failed: {str(e)}"

        recommended_methods = self._parse_list_from_llm_output(raw_agent_output, "Recommended Method Names:")
        recommended_sensors = self._parse_list_from_llm_output(raw_agent_output, "Recommended Sensor Names:")
        return {
            "summary_text": raw_agent_output,
            "recommended_methods": recommended_methods,
            "recommended_sensors": recommended_sensors
        }
