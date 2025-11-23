
import time
from typing import Dict, Tuple

class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = capacity
        self.updated_at = time.monotonic()

    def allow(self, cost: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.updated_at = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

class MemoryRateLimiter:
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.buckets: Dict[str, TokenBucket] = {}

    def check(self, key: str, cost: int = 1) -> bool:
        b = self.buckets.get(key)
        if not b:
            b = TokenBucket(self.capacity, self.refill_per_sec)
            self.buckets[key] = b
        return b.allow(cost)
