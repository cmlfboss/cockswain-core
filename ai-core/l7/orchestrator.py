# /srv/cockswain-core/ai-core/l7/orchestrator.py
import subprocess
from pathlib import Path
from datetime import datetime
import os

SAFE_SCRIPTS = {
    "record_progress": "/srv/cockswain-core/scripts/record_progress.sh",
    "check_node_state": "/srv/cockswain-core/scripts/health_check.sh",
    "sync_docs": "/srv/cockswain-core/scripts/reindex_docs.sh",
    "start_core": "/srv/cockswain-core/scripts/start_core.sh",
    "core_status": "/srv/cockswain-core/scripts/core_status.sh",
}

HIGH_RISK_INTENTS = {"start_core"}


class Orchestrator:
    """
    根據 decision 呼叫母機腳本
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.log_path = Path("/srv/cockswain-core/logs/actions")
        self.log_path.mkdir(parents=True, exist_ok=True)

    def _log(self, message: str):
        logfile = self.log_path / f"l7_action_{datetime.utcnow().date()}.log"
        with logfile.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {message}\n")

    def dispatch(self, decision: dict) -> list[dict]:
        intent = decision.get("intent", "unknown")
        params = decision.get("params") or {}
        requires_approval = decision.get("requires_approval", False)
        is_trusted = decision.get("is_trusted_caller", False)

        # 特別給 approve_intent 用的捷徑
        if intent == "approve_intent":
            target = params.get("target")
            if not target:
                msg = "approve_intent missing target"
                self._log(msg)
                return [{"type": "error", "payload": {"message": msg}}]
            script_path = SAFE_SCRIPTS.get(target)
            if not script_path:
                msg = f"approve_intent target '{target}' not in SAFE_SCRIPTS"
                self._log(msg)
                return [{"type": "error", "payload": {"message": msg}}]
            result = self._run_script(script_path, {})
            return [
                {
                    "type": "exec_script",
                    "intent": target,
                    "approved_by": "approve_intent",
                    "script": script_path,
                    "params": {},
                    "result": result,
                }
            ]

        # 一般 intent
        script_path = SAFE_SCRIPTS.get(intent)
        if not script_path:
            msg = f"no mapped action for intent '{intent}'"
            self._log(msg)
            return [{"type": "noop", "payload": {"message": msg}}]

        # 高風險的要嘛 decision 說不用審，要嘛 caller 是 trusted
        if intent in HIGH_RISK_INTENTS and requires_approval and not is_trusted:
            msg = f"intent '{intent}' pending approval, skip execution"
            self._log(msg)
            return [
                {
                    "type": "pending_approval",
                    "intent": intent,
                    "params": params,
                    "payload": {"message": msg},
                }
            ]

        # 正式執行
        result = self._run_script(script_path, params)
        return [
            {
                "type": "exec_script",
                "intent": intent,
                "script": script_path,
                "params": params,
                "result": result,
            }
        ]

    def _run_script(self, script_path: str, params: dict) -> dict:
        env = os.environ.copy()
        for k, v in params.items():
            env_key = f"L7_ARG_{str(k).upper()}"
            env[env_key] = str(v)

        try:
            proc = subprocess.run(
                [script_path],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            result = {
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._log(f"Ran {script_path} (exit={proc.returncode}) params={params}")
            return result
        except Exception as e:
            self._log(f"error running {script_path}: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
