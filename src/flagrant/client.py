import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import TypeAdapter

from flagrant.cache import LRUCache
from flagrant.models import Feature

_features_adapter = TypeAdapter(list[Feature])

DefaultFlagHandler = Callable[[str, str], list[Feature] | None]


@dataclass(frozen=True)
class FlagsmithOpts:
    timeout: float = 5.0
    cache_ttl: float | None = None
    cache_size: int | None = None
    retries: int = 5
    backoff_factor: float = 0.5


class FlagrantClient:
    def __init__(
        self,
        base_url: str,
        project: str,
        *,
        default_handler: DefaultFlagHandler | None = None,
        opts: FlagsmithOpts = FlagsmithOpts()
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.project = project
        self.opts = opts
        self.default_handler = default_handler
        
        transport = httpx.HTTPTransport(retries=opts.retries)
        self._http = httpx.Client(
            base_url=self.base_url, timeout=opts.timeout, transport=transport
        )
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
            features = self._fetch_features(environment, identity)
        except httpx.TransportError:
            if self.default_handler is None:
                raise
            return self.default_handler(environment, identity)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500 or self.default_handler is None:
                raise
            return self.default_handler(environment, identity)

        if self._cache is not None:
            self._cache.set(key, features)

        return features

    def _fetch_features(self, environment: str, identity: str) -> list[Feature]:
        attempt = 0
        while True:
            response = self._http.get(
                f"/api/v1/projects/{self.project}/envs/{environment}/features",
                headers={"X-Flagrant-Identity": identity},
            )
            if response.status_code >= 500 and attempt < self.opts.retries:
                time.sleep(self.opts.backoff_factor * (2**attempt))
                attempt += 1
                continue
            response.raise_for_status()
            return _features_adapter.validate_python(response.json())

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "FlagrantClient":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()
