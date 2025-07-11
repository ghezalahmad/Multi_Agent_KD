import json
import os
from datetime import datetime

LOG_DIR = "logs"
SHARED_MEMORY_FILE = os.path.join(LOG_DIR, "shared_memory.json")

def save_memory(agent_name: str, key: str, value: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    data = {}
    if os.path.exists(SHARED_MEMORY_FILE):
        with open(SHARED_MEMORY_FILE, "r") as f:
            data = json.load(f)

    if agent_name not in data:
        data[agent_name] = []

    data[agent_name].append({
        "timestamp": datetime.utcnow().isoformat(),
        "key": key,
        "value": value
    })

    with open(SHARED_MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_recent_context(agent_name: str, key: str, limit: int = 3) -> list[str]:
    if not os.path.exists(SHARED_MEMORY_FILE):
        return []

    with open(SHARED_MEMORY_FILE, "r") as f:
        data = json.load(f)

    if agent_name not in data:
        return []

    return [entry["value"] for entry in data[agent_name] if entry["key"] == key][-limit:]
