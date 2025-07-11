#from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from typing import List

# OLD (OpenAI)
# from langchain.chat_models import ChatOpenAI

# NEW (Ollama)
from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from utils.agent_logger import log_agent_interaction
from utils.memory_store import save_memory, get_recent_context



class BaseAgent:
    def __init__(self, system_prompt: str, model: str = "mistral", temperature: float = 0.1):
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.system_prompt = system_prompt
        self.history = [SystemMessage(content=system_prompt)]



    async def __call__(self, user_msg: str) -> str:
        self.history.append(HumanMessage(content=user_msg))
        # Include recent memory context if exists
        recent_msgs = get_recent_context(self.__class__.__name__, key="user_intent")
        if recent_msgs:
            memory_str = "\n".join(f"Previous intent: {m}" for m in recent_msgs)
            self.history.append(SystemMessage(content=f"Context from memory:\n{memory_str}"))

        try:
            response = await self.llm.agenerate([self.history])
            # Save current user intent
            save_memory(self.__class__.__name__, key="user_intent", value=user_msg)

            msg = response.generations[0][0].text
            print("🧠 Response from LLM:", msg)  # DEBUG
            self.history.append(AIMessage(content=msg))

            # ✅ Log interaction
            log_agent_interaction(
                agent_name=self.__class__.__name__,
                input_text=user_msg,
                output_text=msg,
                context={"system_prompt": self.system_prompt}
            )

            return msg.strip()
        except Exception as e:
            print("❌ LLM failed:", str(e))
            return "# ERROR: LLM call failed"

