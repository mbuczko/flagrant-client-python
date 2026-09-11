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
        """Return the cached value, or None if missing or expired.

        A hit only bumps recency (moves the key to the end of the
        underlying OrderedDict) when it's within TTL; expired entries
        are reported as missing but left in place, untouched, so
        get_stale() can still recover them for failure fallback.
        """
        entry = self._data.get(key)

        if entry is None:
            return None

        timestamp, value = entry
        if self.ttl is not None and time.monotonic() - timestamp > self.ttl:
            return None
        self._data.move_to_end(key)
        return value

    def get_stale(self, key: K) -> V | None:
        """Return the cached value even if its TTL has expired, without evicting it.

        Used as a fallback when a fresh fetch fails (e.g. an upstream
        error), so callers can still serve a previously known value
        instead of nothing.
        """
        entry = self._data.get(key)
        return entry[1] if entry is not None else None

    def set(self, key: K, value: V) -> None:
        self._data[key] = (time.monotonic(), value)
        self._data.move_to_end(key)
        if len(self._data) > self.max_size:
            self._data.popitem(last=False)
