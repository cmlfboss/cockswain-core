# v3_autocode/debug_run_pipeline.py
from v3_autocode.parsers.task_spec_builder import TaskSpecBuilder
from v3_autocode.routing.engine_router import EngineRouter, EnvironmentInfo, EngineRoute
from v3_autocode.generators.execution_plan_builder import ExecutionPlanBuilder
from v3_autocode.generators.code_generator import CodeGenerator
from v3_autocode.executors.sandbox_runner import SandboxRunner
from v3_autocode.storage.task_registry import TaskRegistry


def run_example(text: str, title: str) -> None:
    print(f"========== {title} ==========")

    builder = TaskSpecBuilder()
    router = EngineRouter(local_threshold=2.0, mother_threshold=4.0)
    plan_builder = ExecutionPlanBuilder()
    codegen = CodeGenerator(
        scripts_dir="/srv/cockswain-core/ai-core/v3_autocode/tmp_scripts"
    )
    runner = SandboxRunner()
    registry = TaskRegistry()

    # 1) NL → TaskSpec
    spec = builder.build_from_nl(
        user_id="demo_user",
        text=text,
        source="local_butler",
    )

    # 2) Routing
    env_info = EnvironmentInfo(locality="local_butler")
    decision = router.route(spec, env_info)

    print("[Routing]")
    print("  route :", decision.route)
    print("  reason:", decision.reason)
    print()

    # 記錄任務 + routing
    registry.register_task(
        task=spec,
        route=decision.route,
        env={
            "locality": env_info.locality,
            "cpu_load": env_info.cpu_load,
            "memory_load": env_info.memory_load,
        },
    )

    # 目前 demo 階段，不管是 LOCAL 還是 MOTHER，都一律走下面這套 pipeline

    # 3) TaskSpec → ExecutionPlan
    plan = plan_builder.build_for_task(spec)
    print("[ExecutionPlan]")
    for step in plan.steps:
        print(f"  - step {step.step_id}: {step.action} params={step.params}")
    print()

    # 記錄 ExecutionPlan
    registry.register_plan(spec, plan)

    # 4) ExecutionPlan → bash script
    script_content, script_path = codegen.generate_script(spec, plan)
    print("[Generated Script]")
    print("  path:", script_path)
    print("  preview:")
    print("-------------------")
    print("\n".join(script_content.splitlines()[:10]))
    print("-------------------")
    print()

    # 5) Sandbox 執行
    rc, out, err = runner.run_script(script_path)
    print("[SandboxRunner]")
    print("  return code:", rc)
    print("  stdout:")
    print("-------------------")
    print(out)
    print("-------------------")
    if err:
        print("  stderr:")
        print("-------------------")
        print(err)
        print("-------------------")
    print("\n\n")

    # 記錄執行結果
    registry.register_execution_result(
        task=spec,
        route=decision.route,
        return_code=rc,
        stdout=out,
        stderr=err,
    )


def main() -> None:
    text1 = "幫我每天晚上 11 點，把 ~/Downloads 裡的 .zip 移到 ~/backup 然後壓成一個檔案"
    text2 = (
        "我想建立一個監控系統，檢查多台伺服器的 CPU、記憶體 使用率，"
        "如果超過 80% 就發通知到我手機，同時記錄到一個 log 檔案，"
        "最好可以每 5 分鐘檢查一次，之後還可能會擴充成圖表介面。"
    )

    run_example(text1, "Example 1: File organize with schedule")
    run_example(text2, "Example 2: Monitor servers")


if __name__ == "__main__":
    main()
