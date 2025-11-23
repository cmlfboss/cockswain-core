#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core/ai-core"
AUTO_DIR="$BASE_DIR/auto_coder"
SCRIPT_DIR="$BASE_DIR/scripts"
LOG_DIR="$BASE_DIR/logs"
WORKSPACE_DIR="$BASE_DIR/workspace"

mkdir -p "$AUTO_DIR" "$SCRIPT_DIR" "$LOG_DIR" "$WORKSPACE_DIR"

echo "[auto_coder] installing into $AUTO_DIR"

########################
# auto_coder/__init__.py
########################
cat > "$AUTO_DIR/__init__.py" << 'PYEOF'
"""
Cockswain Auto Coder Core v1.1
"""
PYEOF

############################
# auto_coder/task_model.py
############################
cat > "$AUTO_DIR/task_model.py" << 'PYEOF'
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Literal


TaskStatus = Literal[
    "queued",
    "analyzing",
    "planning",
    "generating_code",
    "validating",
    "executing",
    "completed",
    "failed",
]


@dataclass
class TaskSpec:
    task_id: str
    created_at: str
    created_by: str      # e.g. "local-cli" / "hybrid" / "agent"
    source: str          # "cli" / "http" / "hybrid"
    raw_request: str     # 使用者原始自然語言需求

    # pipeline 狀態欄位
    status: TaskStatus = "queued"
    goal: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    plan: Optional[List[Dict[str, Any]]] = None
    code_files: Optional[Dict[str, str]] = None

    # 執行結果
    exec_cwd: Optional[str] = None
    exec_returncode: Optional[int] = None
    exec_stdout: Optional[str] = None
    exec_stderr: Optional[str] = None

    # 錯誤欄位
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
PYEOF

############################
# auto_coder/analyzer.py
############################
cat > "$AUTO_DIR/analyzer.py" << 'PYEOF'
from .task_model import TaskSpec


def analyze_task(spec: TaskSpec) -> TaskSpec:
    """
    v1: 超簡單版，只是把 raw_request 當成 goal，順便塞一些預設限制。
    未來：這裡會被混合引擎 / 新語言接管。
    """
    text = (spec.raw_request or "").strip()
    spec.goal = text if text else "未指定目標"
    spec.context = {
        "language": "python",
        "allowed_dirs": ["/srv/cockswain-core/ai-core/workspace"],
    }
    spec.status = "analyzing"
    return spec
PYEOF

############################
# auto_coder/planner.py
############################
cat > "$AUTO_DIR/planner.py" << 'PYEOF'
from .task_model import TaskSpec


def plan_task(spec: TaskSpec) -> TaskSpec:
    """
    v1: 固定模板步驟。
    之後可改為根據 goal/context 動態規劃。
    """
    spec.plan = [
        {"step": 1, "action": "理解需求與輸入/輸出"},
        {"step": 2, "action": "產生主程式骨架"},
        {"step": 3, "action": "加入錯誤處理與日誌輸出"},
        {"step": 4, "action": "準備基本測試案例"},
    ]
    spec.status = "planning"
    return spec
PYEOF

############################
# auto_coder/generator.py
############################
cat > "$AUTO_DIR/generator.py" << 'PYEOF'
from __future__ import annotations

from textwrap import dedent as _dedent

from .task_model import TaskSpec


def _generate_systemd_checker() -> dict[str, str]:
    code = _dedent(
        """\
        import subprocess
        import sys


        def check_service(name: str) -> int:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", name],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except Exception as e:  # noqa: BLE001
                print(f"[ERROR] 無法呼叫 systemctl: {e}")
                return 1

            status = result.stdout.strip() or result.stderr.strip()
            print(f"service={name!r} status={status!r} rc={result.returncode}")
            return 0 if result.returncode == 0 else 1


        def main(argv: list[str]) -> int:
            if len(argv) < 2:
                print("用法: python3 main.py <service-name>")
                print("例:   python3 main.py cockswain-core.service")
                return 0
            name = argv[1]
            return check_service(name)


        if __name__ == "__main__":
            raise SystemExit(main(sys.argv))
        """
    )
    return {"main.py": code}


def _generate_log_tail() -> dict[str, str]:
    code = _dedent(
        """\
        import sys
        from pathlib import Path
        from collections import deque


        def tail(path: Path, lines: int = 100) -> None:
            if not path.exists():
                print(f"[ERROR] 檔案不存在: {path}")
                return

            buf: deque[str] = deque(maxlen=lines)
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    buf.append(line.rstrip("\\n"))

            for line in buf:
                print(line)


        def main(argv: list[str]) -> int:
            if len(argv) < 2:
                print("用法: python3 main.py <log-file> [lines]")
                print("例:   python3 main.py /var/log/syslog 100")
                return 0

            path = Path(argv[1])
            lines = int(argv[2]) if len(argv) >= 3 else 100
            tail(path, lines)
            return 0


        if __name__ == "__main__":
            raise SystemExit(main(sys.argv))
        """
    )
    return {"main.py": code}


def _generate_generic_demo(spec: TaskSpec) -> dict[str, str]:
    goal_str = spec.goal or spec.raw_request or "Auto coder demo"
    code = _dedent(
        f"""\
        import sys

        def main(argv: list[str]) -> int:
            print("=== Auto-coder generic tool ===")
            print("Goal:", {goal_str!r})
            print("Args:", argv[1:])
            return 0


        if __name__ == "__main__":
            raise SystemExit(main(sys.argv))
        """
    )
    return {"main.py": code}


def generate_code(spec: TaskSpec) -> TaskSpec:
    """
    v1.1: 最小可用「規則型自動編程」
    - systemd / 服務 相關
    - log / 日誌 相關
    - 其他 → 通用示範腳本
    未來如果接上大模型，只要在這裡多一層 model 呼叫即可。
    """
    goal = (spec.goal or spec.raw_request or "").lower()

    if any(k in goal for k in ["systemd", "服務狀態", "service status"]):
        spec.code_files = _generate_systemd_checker()
    elif any(k in goal for k in ["log", "日誌", "日誌檔案", "日志", "log file"]):
        spec.code_files = _generate_log_tail()
    else:
        spec.code_files = _generate_generic_demo(spec)

    spec.status = "generating_code"
    return spec
PYEOF

############################
# auto_coder/validator.py
############################
cat > "$AUTO_DIR/validator.py" << 'PYEOF'
from .task_model import TaskSpec

# 簡單防呆，之後可升級為 AST 檢查
FORBIDDEN = [
    "rm -rf /",
    "rm -rf --no-preserve-root /",
    "shutdown",
    "reboot",
    "systemctl poweroff",
]


def validate_code(spec: TaskSpec) -> TaskSpec:
    if not spec.code_files:
        spec.status = "failed"
        spec.error = "no code generated"
        return spec

    all_code = "\n".join(spec.code_files.values())
    for pattern in FORBIDDEN:
        if pattern in all_code:
            spec.status = "failed"
            spec.error = f"forbidden pattern detected: {pattern}"
            return spec

    spec.status = "validating"
    return spec
PYEOF

############################
# auto_coder/executor.py
############################
cat > "$AUTO_DIR/executor.py" << 'PYEOF'
import subprocess
import tempfile
from pathlib import Path

from .task_model import TaskSpec


def execute_task(
    spec: TaskSpec,
    workdir_base: str = "/srv/cockswain-core/ai-core/workspace",
) -> TaskSpec:
    """
    v1: 用暫存目錄執行 main.py。
    之後可改為 docker/chroot 等更強 sandbox。
    """
    if not spec.code_files:
        spec.status = "failed"
        spec.error = "no code to execute"
        return spec

    base = Path(workdir_base)
    base.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"task_{spec.task_id}_", dir=base) as tmpdir:
        workdir = Path(tmpdir)
        for name, content in spec.code_files.items():
            target = workdir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        spec.exec_cwd = str(workdir)

        try:
            proc = subprocess.run(
                ["python3", "main.py"],
                cwd=spec.exec_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:  # noqa: BLE001
            spec.status = "failed"
            spec.error = f"execute error: {e}"
            spec.exec_returncode = None
            spec.exec_stdout = ""
            spec.exec_stderr = str(e)
            return spec

        spec.exec_returncode = proc.returncode
        spec.exec_stdout = proc.stdout
        spec.exec_stderr = proc.stderr

        spec.status = "completed" if proc.returncode == 0 else "failed"
        return spec
PYEOF

############################
# auto_coder/feedback.py
############################
cat > "$AUTO_DIR/feedback.py" << 'PYEOF'
import datetime
from pathlib import Path

from .task_model import TaskSpec

# log 放在 ai-core/logs/auto_coder.log
BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "auto_coder.log"


def record_feedback(spec: TaskSpec) -> None:
    ts = datetime.datetime.utcnow().isoformat()
    line = f"{ts} | {spec.task_id} | {spec.status} | {spec.goal}\\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
PYEOF

############################
# auto_coder/orchestrator.py
############################
cat > "$AUTO_DIR/orchestrator.py" << 'PYEOF'
import datetime
import uuid

from .task_model import TaskSpec
from . import analyzer, executor, feedback, generator, planner, validator


def run_auto_coder(
    raw_request: str,
    created_by: str = "local-cli",
    source: str = "cli",
) -> TaskSpec:
    """
    自動編程主入口：
    - 現在給 CLI 使用
    - 未來母機上的舵手也會直接呼叫這一層
    """
    spec = TaskSpec(
        task_id=str(uuid.uuid4()),
        created_at=datetime.datetime.utcnow().isoformat(),
        created_by=created_by,
        source=source,
        raw_request=raw_request,
    )

    try:
        spec = analyzer.analyze_task(spec)
        spec = planner.plan_task(spec)
        spec = generator.generate_code(spec)
        spec = validator.validate_code(spec)

        if spec.status != "failed":
            spec = executor.execute_task(spec)
    except Exception as e:  # noqa: BLE001
        # 極簡保護，避免 CLI 直接炸掉
        spec.status = "failed"
        spec.error = f"orchestrator error: {e}"

    # 無論成功失敗，都寫一筆 log
    try:
        feedback.record_feedback(spec)
    except Exception:
        # log 寫不進去就算了，不能影響主流程
        pass

    return spec
PYEOF

################################
# scripts/auto_coder_cli.py
################################
cat > "$SCRIPT_DIR/auto_coder_cli.py" << 'PYEOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

# 確保可以 import auto_coder 套件
THIS_FILE = Path(__file__).resolve()
BASE_DIR = THIS_FILE.parents[1]  # /srv/cockswain-core/ai-core
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from auto_coder.orchestrator import run_auto_coder  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法:")
        print('  auto_coder_cli.py "用自然語言描述你想要的程式"')
        return 1

    raw_request = argv[1]
    spec = run_auto_coder(raw_request, created_by="local-cli", source="cli")

    print(f"Task ID : {spec.task_id}")
    print(f"Status  : {spec.status}")
    print(f"Goal    : {spec.goal}")

    print("=== STDOUT ===")
    if spec.exec_stdout:
        print(spec.exec_stdout, end="")

    print("\n=== STDERR ===")
    if spec.exec_stderr:
        print(spec.exec_stderr, end="")

    if spec.error:
        print("\n=== ERROR ===")
        print(spec.error)

    return 0 if spec.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
PYEOF

chmod +x "$SCRIPT_DIR/auto_coder_cli.py"

echo "[auto_coder] install done."
