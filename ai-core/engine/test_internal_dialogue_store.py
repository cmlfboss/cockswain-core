from engine.dynamic_pointer import run_internal_dialogue
from engine.core_layer_bindings import register_core_layers
from engine.internal_dialogue_store import save_dialogue_to_file


if __name__ == "__main__":
    register_core_layers()

    question = "舵手未來要如何運用內部對話，持續優化自己？"
    result = run_internal_dialogue(question, intent="self_evolve")

    path = save_dialogue_to_file(result)

    print("=== FINAL ANSWER ===")
    print(result["final"])
    print("\n=== SAVED TO ===")
    print(path)
