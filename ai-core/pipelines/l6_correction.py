def process(data: dict, ctx: dict):
    data.setdefault("pipeline_notes", [])
    data["pipeline_notes"].append(f"processed by {__name__} for {ctx['agent']['name']}")
    return data
