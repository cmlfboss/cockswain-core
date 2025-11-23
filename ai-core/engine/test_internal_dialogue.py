from engine.dynamic_pointer import run_internal_dialogue
from engine.demo_handlers import register_demo_layers


if __name__ == "__main__":
    # 先註冊 demo 的 L1 / L3 / L5 / L7
    register_demo_layers()

    question = "如何讓舵手可以自己跟自己對話？"
    result = run_internal_dialogue(question, intent="internal_dev")

    print("=== FINAL ANSWER ===")
    print(result["final"])
    print("\n=== HISTORY ===")
    for turn in result["history"]:
        print(f"[{turn['layer']}] {turn['role']}: {turn['content']}")
