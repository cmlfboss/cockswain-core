from engine.internal_dialogue_store import run_and_store_internal_dialogue


if __name__ == "__main__":
    result = run_and_store_internal_dialogue(
        "如果要優先強化一個模組來幫助舵手成長，應該先動哪一層？",
        intent="prioritize_upgrade",
    )

    print("=== FINAL ANSWER ===")
    print(result["final"])
    print("\n=== SAVED TO ===")
    print(result["_saved_path"])
