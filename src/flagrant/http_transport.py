import time

import httpx
from pydantic import TypeAdapter

from flagrant.models import Feature
from flagrant.transport import PermanentError, TransientError

_features_adapter = TypeAdapter(list[Feature])


class HttpTransport:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        retries: int = 5,
        backoff_factor: float = 0.5,
    ) -> None:
        transport = httpx.HTTPTransport(retries=retries)
        
        self.retries = retries
        self.backoff_factor = backoff_factor
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )

    def fetch(self, project: str, environment: str, identity: str) -> list[Feature]:
        attempt = 0
        while True:
            try:
                response = self._http.get(
                    f"/api/v1/projects/{project}/envs/{environment}/features",
                    headers={"X-Flagrant-Identity": identity},
                )
            except httpx.TransportError as exc:
                raise TransientError from exc

            if response.status_code >= 500:
                if attempt < self.retries:
                    time.sleep(self.backoff_factor * (2**attempt))
                    attempt += 1
                    continue
                raise TransientError(f"server error: {response.status_code}")

            if response.status_code >= 400:
                raise PermanentError(f"client error: {response.status_code}")

            return _features_adapter.validate_python(response.json())

    def close(self) -> None:
        self._http.close()
