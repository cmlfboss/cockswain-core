import time
import json

def prepare_task_response(task_type, content):
    return {
        "timestamp": time.time(),
        "task_type": task_type,
        "summary": f"L7 已接收任務 ({task_type})",
        "content_preview": content[:80] + ("..." if len(content) > 80 else ""),
        "status": "queued"
    }
