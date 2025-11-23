
import time

class CircuitBreaker:
    def __init__(self, fail_threshold: int, cooldown_seconds: float):
        self.fail_threshold = fail_threshold
        self.cooldown_seconds = cooldown_seconds
        self.fail_count = 0
        self.state = "closed"
        self.opened_at = 0.0

    def record_success(self):
        self.fail_count = 0
        if self.state != "closed":
            self.state = "closed"

    def record_failure(self):
        self.fail_count += 1
        if self.fail_count >= self.fail_threshold and self.state != "open":
            self.state = "open"
            self.opened_at = time.monotonic()

    def allow(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if (time.monotonic() - self.opened_at) >= self.cooldown_seconds:
                self.state = "half-open"
                return True
            return False
        if self.state == "half-open":
            return True
        return True
