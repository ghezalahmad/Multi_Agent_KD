#from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from typing import List

# OLD (OpenAI)
# from langchain.chat_models import ChatOpenAI

# NEW (Ollama)
from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage, AIMessage

class BaseAgent:
    def __init__(self, system_prompt: str, model: str = "mistral", temperature: float = 0.1):
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.system_prompt = system_prompt
        self.history = [SystemMessage(content=system_prompt)]



    async def __call__(self, user_msg: str) -> str:
        self.history.append(HumanMessage(content=user_msg))
        try:
            response = await self.llm.agenerate([self.history])
            msg = response.generations[0][0].text
            print("🧠 Response from LLM:", msg)  # DEBUG
            self.history.append(AIMessage(content=msg))
            return msg.strip()
        except Exception as e:
            print("❌ LLM failed:", str(e))
            return "# ERROR: LLM call failed"
