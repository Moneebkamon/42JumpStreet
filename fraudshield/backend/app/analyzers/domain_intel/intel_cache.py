"""Tiny in-memory TTL cache for domain lookups. Swap for Redis later without changing callers."""
import threading
import time

DEFAULT_TTL = 3600  # successful lookups: 1 hour
FAILURE_TTL = 300  # failed lookups: retry after 5 minutes


class IntelCache:
    def __init__(self) -> None:
        self._data: dict = {}
        self._lock = threading.Lock()

    def get(self, key) -> tuple[bool, object]:
        with self._lock:
            entry = self._data.get(key)
            if entry and entry[0] > time.monotonic():
                return True, entry[1]
            self._data.pop(key, None)
            return False, None

    def set(self, key, value, ttl: float = DEFAULT_TTL) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


cache = IntelCache()
