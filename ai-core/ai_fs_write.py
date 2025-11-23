#!/usr/bin/env python3
"""
ai_fs_write.py — Cockswain 安全檔案寫入服務 v1.0
---------------------------------------------------
此模組是「舵手自動編程」的核心寫入管道。

安全規範：
1. 僅允許寫入下列白名單路徑：
   - /srv/cockswain-core/ai-core/auto_coder/
2. 禁止覆蓋與擴寫：
   - systemd、/etc、/usr、/boot、/root、/home、/var、/srv/... 其他非白名單
3. 必須附帶 "signature"，作為舵手授權識別（簡易版 token）
4. 必須附帶 "hash"（內容 SHA256），避免傳輸過程遭竄改
5. 一律完整覆蓋寫入，不做 append（安全且可審計）
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Tuple

# ====== 可寫入的根目錄（白名單） ======
ALLOWED_ROOT = Path("/srv/cockswain-core/ai-core/auto_coder")

# ====== 簽章 ======
# 初期使用簡單 token，後續可改為：
# 舵手內部簽章 → DAO 簽章 → 新語言內部簽章
AI_SIGNATURE = "cockswain-internal-write-v1"


# ==========================================================
# 工具：檢查是否在白名單內
# ==========================================================
def _is_allowed(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(ALLOWED_ROOT)
    except Exception:
        return False


# ==========================================================
# 工具：計算 SHA256
# ==========================================================
def _sha256(data: str) -> str:
    h = hashlib.sha256()
    h.update(data.encode("utf-8"))
    return h.hexdigest()


# ==========================================================
# 寫入主函數
# ==========================================================
def fs_write(payload: dict) -> Tuple[bool, str]:
    """
    payload 包含：
    {
        "path": "/srv/.../auto_coder/generator.py",
        "content": "新的程式碼內容",
        "hash": "<sha256>",
        "signature": "cockswain-internal-write-v1"
    }
    """

    # --- 1) 欄位檢查 ---
    required = ["path", "content", "hash", "signature"]
    for r in required:
        if r not in payload:
            return False, f"missing field: {r}"

    target_path = Path(payload["path"])
    content = payload["content"]
    provided_hash = payload["hash"]
    signature = payload["signature"]

    # --- 2) 簽章驗證 ---
    if signature != AI_SIGNATURE:
        return False, "invalid signature"

    # --- 3) hash 驗證 ---
    real_hash = _sha256(content)
    if real_hash != provided_hash:
        return False, "hash mismatch (content corrupted)"

    # --- 4) 白名單檢查 ---
    if not _is_allowed(target_path):
        return False, f"path not allowed: {target_path}"

    # --- 5) 寫入 ---
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return False, f"write error: {e}"

    return True, f"write OK: {target_path}"


# ==========================================================
# CLI 模式（方便你直接用 CLI 測試）
# ==========================================================
def main():
    import sys

    if len(sys.argv) != 2:
        print("用法：python3 ai_fs_write.py '<json_payload>'")
        return

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print("payload 必須是 JSON 字串")
        return

    ok, msg = fs_write(payload)
    print(json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False))


if __name__ == "__main__":
    main()
