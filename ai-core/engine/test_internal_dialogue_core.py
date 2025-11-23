from engine.dynamic_pointer import run_internal_dialogue
from engine.core_layer_bindings import register_core_layers


if __name__ == "__main__":
    # 改用 core 層的綁定（取代 demo）
    register_core_layers()

    question = "接下來舵手要如何利用動態指向，逐步實現自我成長？"
    result = run_internal_dialogue(question, intent="evolution_plan")

    print("=== FINAL ANSWER ===")
    print(result["final"])
    print("\n=== HISTORY ===")
    for turn in result["history"]:
        print(f"[{turn['layer']}] {turn['role']}: {turn['content']}")
