# Cockswain Auto Coder v3.1 摘要

- `auto_coder/generator.py`
  - `from_doc <doc_id>`: 從 `tempstore/tasks/<doc_id>.json` 產生程式骨架
  - `from_prompt "<描述>"`: 從一句描述產生程式骨架
  - 自動在 `workspace/auto_code/meta/*.py.json` 寫入 meta 資訊

- `workspace/auto_code/`
  - `*.py`: 自動產生的程式骨架
  - `meta/*.py.json`: 每支程式的身分資訊（mode, doc_id, prompt, instruction...）
  - `meta/combined_logs_*.txt`: log_merger 的彙總輸出
  - `meta/actions.json`: 可用 action 列表

- `scripts/`
  - `merge_logs.sh`: 標準 log 彙總（會呼叫 log_merger 腳本）
  - `autocode_from_doc.sh <doc_id>`: 從指定 doc_id 產生程式骨架
  - `run_action.py <action_name> [args...]`: 行為總控台
    - `merge_logs`
    - `autocode_from_doc`
