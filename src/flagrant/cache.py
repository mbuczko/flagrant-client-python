import time
from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """A dict-backed cache with LRU eviction and optional per-entry TTL."""

    def __init__(self, max_size: int, ttl: float | None) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self._data: OrderedDict[K, tuple[float, V]] = OrderedDict()

    def get(self, key: K) -> V | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if self.ttl is not None and time.monotonic() - timestamp > self.ttl:
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: K, value: V) -> None:
        self._data[key] = (time.monotonic(), value)
        self._data.move_to_end(key)
        if len(self._data) > self.max_size:
            self._data.popitem(last=False)
