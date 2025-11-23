#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Three-Net Semantic Marker v0.1

功能：
- 根據三魂映射表（three_nets_map.yaml）
- 自動將一段文字標記為：F（事實）、S（結構）、M（意義）
- 提供給 kc_entries 在寫入時自動加 semantic_seed / semantic_path / eco_path
"""

from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent          # .../knowledge_center/semantic
MAP_FILE = BASE / "three_nets_map.yaml"


def load_map():
    if not MAP_FILE.exists():
        # 若還沒有定義映射表，給一個極簡預設，避免整體崩潰
        return {
            "three_nets": {
                "fact_net": {
                    "id": "F",
                    "semantic_root": "lang.fact",
                    "eco_root": "ecosystem.fact",
                    "detect_rules": [],
                },
                "structure_net": {
                    "id": "S",
                    "semantic_root": "lang.structure",
                    "eco_root": "ecosystem.structure",
                    "detect_rules": [],
                },
                "meaning_net": {
                    "id": "M",
                    "semantic_root": "lang.meaning",
                    "eco_root": "ecosystem.meaning",
                    "detect_rules": [],
                },
            }
        }
    with MAP_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


MAP = load_map()


def mark_text(content: str):
    """
    回傳：
    - seed: 'F' / 'S' / 'M'
    - semantic_path: e.g. 'lang.fact'
    - eco_path: e.g. 'ecosystem.fact'
    """
    if content is None:
        content = ""
    text = content.lower()

    three_nets = MAP.get("three_nets", {})

    # 依序檢查每一個 net 的關鍵字規則
    for net_key, net in three_nets.items():
        rules = net.get("detect_rules") or []
        for rule in rules:
            keyword = (rule.get("keyword") or "").lower()
            if keyword and keyword in text:
                return (
                    net.get("id", "S"),
                    net.get("semantic_root", "lang.structure"),
                    net.get("eco_root", "ecosystem.structure"),
                )

    # 若沒有命中任何規則：預設視為結構網（最安全）
    s = three_nets.get("structure_net") or {}
    return (
        s.get("id", "S"),
        s.get("semantic_root", "lang.structure"),
        s.get("eco_root", "ecosystem.structure"),
    )


if __name__ == "__main__":
    # 簡單測試
    demo = "我們要把母機的規劃寫成七層核心，作為新語言的基底。"
    print(mark_text(demo))
