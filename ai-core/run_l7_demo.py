from l7 import HelmsmanCore

def run_single(core):
    print("== single: sync_docs with params ==")
    res = core.tick({
        "l1": { "semantic": { "intent": "sync_docs", "text": "sync docs fully" } },
        "l4": { "exec": { "params": { "mode": "full", "source": "specs" } } },
        "l6": { "system_state": { "mother_node": "online" } }
    })
    print(res)

def run_sequence(core):
    print("\n== sequence: record → core_status → start_core (should pending) ==")
    res = core.tick({
        "steps": [
            { "l1": { "semantic": { "intent": "record_progress", "text": "log" } }, "l6": { "system_state": { "mother_node": "online" } } },
            { "l1": { "semantic": { "intent": "core_status", "text": "check core" } }, "l6": { "system_state": { "mother_node": "online" } } },
            { "l1": { "semantic": { "intent": "start_core", "text": "start core" } }, "l6": { "system_state": { "mother_node": "online" } } }
        ]
    })
    print(res)

def run_approve(core):
    print("\n== approve: approve_intent → start_core ==")
    res = core.tick({
        "l1": { "semantic": { "intent": "approve_intent", "text": "approve start_core" } },
        "l4": { "exec": { "params": { "target": "start_core" } } },
        "l6": { "system_state": { "mother_node": "online" } }
    })
    print(res)

if __name__ == "__main__":
    core = HelmsmanCore({})
    run_single(core)
    run_sequence(core)
    run_approve(core)
