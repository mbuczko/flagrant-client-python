from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from flagrant.cache import LRUCache
from flagrant.models import Feature
from flagrant.transport import Transport, TransientError

DefaultFlagHandler = Callable[[str, str], list[Feature] | None]

@dataclass(frozen=True)
class FlagsmithOpts:
    cache_ttl: float | None = None
    cache_size: int | None = None


class FlagrantClient:
    def __init__(
        self,
        project: str,
        transport: Transport,
        *,
        default_handler: DefaultFlagHandler | None = None,
        opts: FlagsmithOpts = FlagsmithOpts()
    ) -> None:
        self.project = project
        self.transport = transport
        self.opts = opts
        self.default_handler = default_handler

        self._cache: LRUCache[tuple[str, str], list[Feature]] | None = (
            LRUCache(max_size=opts.cache_size, ttl=opts.cache_ttl)
            if opts.cache_size
            else None
        )

    def get_features(self, environment: str, identity: str) -> list[Feature] | None:
        key = (environment, identity)
        if self._cache is not None:
            if cached := self._cache.get(key):
                return cached

        try:
            features = self.transport.fetch(self.project, environment, identity)
        except TransientError:
            if self._cache is not None and (stale := self._cache.get_stale(key)) is not None:
                return stale
            if self.default_handler is None:
                raise
            return self.default_handler(environment, identity)

        if self._cache is not None:
            self._cache.set(key, features)

        return features

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> "FlagrantClient":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()
