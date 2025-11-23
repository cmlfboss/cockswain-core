import json
import time
from pathlib import Path
from datetime import datetime

from .task_handler import find_next_task, process_one_task


STATUS_FILE = Path("/srv/cockswain-core/logs/hybrid_engine_status.json")


def write_status(status: str) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.utcnow().timestamp(),
        "iso_time": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "component": "hybrid-core",
    }
    with STATUS_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def main_loop(poll_interval: float = 10.0) -> None:
    write_status("starting")
    print("[HybridCore] 舵手混合引擎核心啟動成功")
    print(f"[HybridCore] poll_interval = {poll_interval}s")

    while True:
        try:
            # 更新心跳
            write_status("running")

            # 嘗試抓一個任務
            task_path = find_next_task()
            if task_path:
                print(f"[HybridCore] 發現任務：{task_path}")
                process_one_task(task_path)
                print(f"[HybridCore] 任務完成：{task_path}")

        except Exception as e:  # noqa: BLE001
            # 如果整個 loop 爆掉，至少寫一條錯誤狀態
            print(f"[HybridCore] Error in main loop: {e!r}")
            write_status(f"error: {e!r}")

        time.sleep(poll_interval)


if __name__ == "__main__":
    main_loop()
