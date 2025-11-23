#!/usr/bin/env python3
import subprocess, pathlib
print("[*] Running self-test...")

def run(p):
    out = subprocess.run(["/usr/bin/python3", "-m", p], capture_output=True, text=True)
    print(f"[{p}]", out.returncode, out.stdout.strip() or "-", out.stderr.strip() or "-")

run("hybrid_engine.core.hybrid_core")
run("hybrid_engine.orchestrator.orchestrator_main")
print("[*] Done.")
