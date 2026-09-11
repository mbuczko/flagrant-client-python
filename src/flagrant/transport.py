from typing import Protocol

from flagrant.models import Feature


class TransientError(Exception):
    """A fetch failed in a way that may be resolved by a stale cache entry or default handler."""


class PermanentError(Exception):
    """A fetch failed in a way that should propagate to the caller immediately."""


class Transport(Protocol):
    def fetch(self, project: str, environment: str, identity: str) -> list[Feature]:
        """Fetch features for an environment/identity, raising TransientError or PermanentError on failure."""
        ...

    def close(self) -> None: ...
