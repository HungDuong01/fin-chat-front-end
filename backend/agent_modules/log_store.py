import os
import json
from datetime import datetime
from typing import Optional

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def _get_today_log_path() -> str:
    """Tạo đường dẫn log file theo ngày."""
    today_str = datetime.today().strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"{today_str}.jsonl")

def log_conversation(message: str, response: str, agent_name: str, metadata: Optional[dict] = None):
    """
    Ghi log toàn bộ hội thoại vào file theo ngày.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "message": message,
        "response": response,
        "metadata": metadata or {}
    }
    log_path = _get_today_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def log_agent_usage(agent_name: str):
    """
    Ghi tên agent được sử dụng vào file usage.log.
    """
    usage_log_path = os.path.join(LOG_DIR, "agent_usage.log")
    with open(usage_log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {agent_name}\n")
