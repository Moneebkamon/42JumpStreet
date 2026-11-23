"""A tiny in-memory sliding-window limiter, enough to slow abuse of the public report form on one server.

Not shared between processes and reset on restart; a real deployment would put this in Redis.
"""
import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.max_hits, self.window, self.clock = max_hits, window_seconds, clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record a hit for `key` and say whether it is within the limit."""
        now = self.clock()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_hits:
            return False
        q.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()
