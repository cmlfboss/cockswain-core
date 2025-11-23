def summary():
    try:
        import psutil
        return {
            "cpu": psutil.cpu_percent(interval=0.1),
            "mem": psutil.virtual_memory().percent,
        }
    except Exception:
        return {"cpu": 0.0, "mem": 0.0}
