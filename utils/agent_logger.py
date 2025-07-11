import os
import json
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_agent_interaction(agent_name: str, input_text: str, output_text: str, context: dict = None):
    try:
        timestamp = datetime.now().isoformat(timespec="seconds")
        log_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "input": input_text,
            "output": output_text,
            "context": context or {}
        }

        log_path = os.path.join(LOG_DIR, f"{agent_name}_log.jsonl")
        print(f"📁 Writing to: {log_path}")  # << DEBUG PRINT

        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        print("❌ Failed to write agent log:", e)

