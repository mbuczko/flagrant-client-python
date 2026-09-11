# flagrant-client-python

A Python client for fetching feature flags from a [Flagrant](https://github.com/mbuczko/flagrant) server, with pluggable transports, optional caching, and stale-on-error fallback.

## Transports

`FlagrantClient` doesn't talk to the network itself - it delegates to a `Transport`, a small protocol with a single `fetch(project, environment, identity) -> list[Feature]` method (plus `close()`). This keeps the client's caching/fallback logic independent of how features are actually retrieved, and makes it easy to add new transports or swap them in tests.

Two transports ship today:

- **`HttpTransport`**  - calls the endpoint `GET /api/v1/projects/{project}/envs/{environment}/features` over HTTP via `httpx`, sending the identity as an `X-Flagrant-Identity` header.
- **`GrpcTransport`**  - calls for the features over gRPC, sending the identity as an `x-flagrant-identity` metadata entry. Accepts any grpc-core target string, including `unix:` sockets.

Both transports retry on transient failures with exponential backoff (`retries`, `backoff_factor`), and both classify errors into one of two exceptions defined in `transport.py`:

- `TransientError` - the fetch failed in a way that might be resolved by falling back to a stale cache entry or a default handler (e.g. server errors, `UNAVAILABLE`/`UNKNOWN`/`INTERNAL`/`RESOURCE_EXHAUSTED` gRPC codes, connection
  errors).
- `PermanentError` - the failure should propagate to the caller immediately (e.g. 4xx responses, malformed feature payloads).

This split lets `FlagrantClient.get_features` react differently depending on whether a retry-worthy or a nonrecoverable failure occurred, regardless of which transport raised it.

## Caching and fallback

`FlagrantClient` optionally wraps fetches in an `LRUCache` (per `(environment, identity)` key), configured via `FlagsmithOpts(cache_size=..., cache_ttl=...)`. On a `TransientError`, the client tries a stale cache entry before falling back to a user-supplied `default_handler`, and only re-raises if neither is available.

## Testing in IPython

With the dev dependencies installed and a Flagrant gRPC server listening on a Unix socket at `/tmp/flagrant/grpc.sock`:

```bash
uv run ipython
```

```python
import flagrant.client as c
import flagrant.grpc_transport as gt

t = gt.GrpcTransport("unix:/tmp/flagrant/grpc.sock")
client = c.FlagrantClient(project="demo", transport=t)
client.get_features(environment="prod", identity="foo")
```

Swap in `flagrant.http_transport.HttpTransport("http://localhost:3030")` to hit an HTTP server instead - the rest of the snippet stays the same, since `FlagrantClient` only depends on the `Transport` protocol.
