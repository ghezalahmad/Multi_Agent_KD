import uuid
import json
from pathlib import Path

def generate_plan_id():
    return str(uuid.uuid4())

def log_agent_response(plan_id, agent_name, content, user_input=None):
    log_path = Path("logs/session_trace.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "plan_id": plan_id,
        "agent": agent_name,
        "content": content
    }
    if user_input:
        entry["user_input"] = user_input
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
