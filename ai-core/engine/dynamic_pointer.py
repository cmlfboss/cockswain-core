"""
Dynamic Pointer & Internal Dialogue Engine v1
讓舵手可以對內「指定層級」發問，建立自我對話基礎。
"""

from typing import Any, Callable, Dict, List, Optional


# ---- Layer Registry: 註冊 L1 ~ L7 處理器 ----

class LayerRegistry:
    """
    登記各層（L1 ~ L7）的 handler。
    handler 介面統一為：
        handler(payload: Dict[str, Any]) -> Dict[str, Any]
    """
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def register(self, name: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._handlers[name] = handler

    def has(self, name: str) -> bool:
        return name in self._handlers

    def call(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._handlers:
            raise ValueError(f"[LayerRegistry] 未註冊的層級: {name}")
        return self._handlers[name](payload)


# 全域唯一實例
layer_registry = LayerRegistry()


# ---- 動態指向表：語意 → 層級 ----

# 這裡先採用簡單版，之後可以搬到 DB 或 config
DYNAMIC_POINTER_TABLE: Dict[str, str] = {
    "semantic_parse": "L1",      # 語意解析
    "common_logic": "L2",        # 常識/一般邏輯
    "domain_knowledge": "L3",    # 領域知識
    "logic_layer": "L4",         # 嚴謹推理層
    "meta_reasoning": "L5",      # 反思/元認知
    "strategy": "L6",            # 策略與治理
    "consensus": "L7",           # 共識仲裁
}


def resolve_pointer(slot: str) -> str:
    """
    給「語意槽位」→ 找出應該指向哪一層（L1~L7）。
    slot 例子： semantic_parse / meta_reasoning / consensus ...
    """
    if slot not in DYNAMIC_POINTER_TABLE:
        raise ValueError(f"[DynamicPointer] 未定義的語意槽位: {slot}")
    return DYNAMIC_POINTER_TABLE[slot]


# ---- Internal Dialogue Engine：內部自我對話 ----

class DialogueTurn:
    def __init__(self, layer: str, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.layer = layer      # e.g. "L1", "L5", "L7"
        self.role = role        # "system" / "engine" / "layer"
        self.content = content  # 文字內容
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "role": self.role,
            "content": self.content,
            "meta": self.meta,
        }


class InternalDialogueEngine:
    """
    內部對話迴圈 v1：
    - 接收一個問題 + intent
    - 依照預設流程：L1 -> L3 -> L5 -> L7
    - 產生一組「自我對話紀錄」＋ 最終輸出
    """

    def __init__(self) -> None:
        self.history: List[DialogueTurn] = []

    def _call_layer(self, layer_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        實際呼叫某一層的 handler，並把 input/output 都記錄到 history。
        """
        # 記錄輸入
        self.history.append(
            DialogueTurn(
                layer=layer_name,
                role="engine",
                content=f"[CALL] {layer_name} with payload: {payload}",
            )
        )

        result = layer_registry.call(layer_name, payload)

        # 記錄輸出
        self.history.append(
            DialogueTurn(
                layer=layer_name,
                role="layer",
                content=f"[RESULT] {layer_name} -> {result}",
            )
        )
        return result

    def run_pipeline(
        self,
        question: str,
        intent: str = "default",
        max_rounds: int = 1,
    ) -> Dict[str, Any]:
        """
        最簡版內部管線：
        1. L1: 語意解析
        2. L3: 查相關知識（可選，看有沒有註冊）
        3. L5: 反思 / 補強
        4. L7: 共識 + 最終結論

        max_rounds 預留給以後「多輪自我修正」用，目前先不使用。
        """

        self.history.append(
            DialogueTurn(
                layer="engine",
                role="system",
                content=f"[START] 問題: {question} | intent: {intent}",
                meta={"intent": intent},
            )
        )

        # 1) L1 語意解析
        l1_name = resolve_pointer("semantic_parse")  # -> "L1"
        l1_result = self._call_layer(
            l1_name,
            {
                "question": question,
                "intent": intent,
                "stage": "semantic_parse",
            },
        )

        # 2) L3 領域知識（如果有註冊才叫）
        knowledge = None
        if layer_registry.has("L3"):
            l3_name = resolve_pointer("domain_knowledge")  # -> "L3"
            knowledge = self._call_layer(
                l3_name,
                {
                    "question": question,
                    "parsed": l1_result,
                    "intent": intent,
                    "stage": "domain_knowledge",
                },
            )

        # 3) L5 元認知 / 反思（如果有註冊）
        reflection = None
        if layer_registry.has("L5"):
            l5_name = resolve_pointer("meta_reasoning")  # -> "L5"
            reflection = self._call_layer(
                l5_name,
                {
                    "question": question,
                    "parsed": l1_result,
                    "knowledge": knowledge,
                    "intent": intent,
                    "stage": "meta_reasoning",
                },
            )

        # 4) L7 共識＋最終輸出（必須註冊）
        l7_name = resolve_pointer("consensus")  # -> "L7"
        final = self._call_layer(
            l7_name,
            {
                "question": question,
                "parsed": l1_result,
                "knowledge": knowledge,
                "reflection": reflection,
                "intent": intent,
                "stage": "consensus",
            },
        )

        self.history.append(
            DialogueTurn(
                layer="engine",
                role="system",
                content="[END] pipeline 完成",
                meta={"final": final},
            )
        )

        return {
            "question": question,
            "intent": intent,
            "final": final,
            "history": [t.to_dict() for t in self.history],
        }


# ---- 方便外部使用的 helper ----

def run_internal_dialogue(
    question: str,
    intent: str = "default",
) -> Dict[str, Any]:
    """
    對外暴露的簡單入口：
    未來任何地方想啟動「舵手自我對話」都可以呼叫這個。
    """
    engine = InternalDialogueEngine()
    return engine.run_pipeline(question=question, intent=intent)
