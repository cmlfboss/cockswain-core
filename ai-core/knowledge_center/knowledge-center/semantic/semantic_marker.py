#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Three-Net Semantic Marker v0.1
功能：
- 根據三魂映射表（three_nets_map.yaml）
- 自動將一段文字標記為：F（事實）、S（結構）、M（意義）
- 提供給 kc_entries 在寫入時自動加 semantic_seed / semantic_path
"""

import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent
MAP_FILE = BASE / "three_nets_map.yaml"


def load_map():
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


MAP = load_map()


def mark_text(content: str):
    """回傳 ('F'/'S'/'M', 'semantic_path', 'eco_path')"""
    content = content.lower()

    for net_key, net in MAP["three_nets"].items():
        for rule in net.get("detect_rules", []):
            if rule["keyword"] in content:
                return (
                    net["id"],
                    net["semantic_root"],
                    net["eco_root"],
                )

    # 若沒有命中任何規則：預設視為結構網（最安全）
    s = MAP["three_nets"]["structure_net"]
    return s["id"], s["semantic_root"], s["eco_root"]


if __name__ == "__main__":
    # 測試用
    test = "我們要將規劃寫成七層核心，作為新語言的基底"
    print(mark_text(test))
