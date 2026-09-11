import time

import grpc

from flagrant.models import Feature, FeatureValue, JsonValue, TextValue, TomlValue
from flagrant.proto import features_pb2, features_pb2_grpc
from flagrant.transport import PermanentError, TransientError

_RETRYABLE_CODES = {
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.UNKNOWN,
    grpc.StatusCode.INTERNAL,
    grpc.StatusCode.RESOURCE_EXHAUSTED,
}


def _feature_from_proto(feature: features_pb2.Feature) -> Feature:
    variant = feature.value
    value: FeatureValue
    match variant.WhichOneof("kind"):
        case "text":
            value = TextValue(variant.text)
        case "json":
            value = JsonValue(variant.json)
        case "toml":
            value = TomlValue(variant.toml)
        case _:
            raise PermanentError(f"feature {feature.name!r} has no value set")

    return Feature(
        feature_id=feature.feature_id,
        name=feature.name,
        value=value,
        is_enabled=feature.is_enabled,
    )


class GrpcTransport:
    def __init__(
        self,
        target: str,
        *,
        credentials: grpc.ChannelCredentials | None = None,
        authority: str | None = None,
        timeout: float = 5.0,
        retries: int = 5,
        backoff_factor: float = 0.5,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor

        # For unix: targets, grpc-core derives :authority from the percent-encoded
        # socket path (e.g. "tmp%2Fflagrant%2Fgrpc.sock") instead of a plain host,
        # which strict/routing-aware HTTP/2 servers can reject. Default it to
        # "localhost" there, matching what grpcurl/grpc-go send.
        if authority is None and target.startswith("unix:"):
            authority = "localhost"

        options = [("grpc.default_authority", authority)] if authority is not None else []

        self._channel = (
            grpc.secure_channel(target, credentials, options=options)
            if credentials is not None
            else grpc.insecure_channel(target, options=options)
        )
        self._stub = features_pb2_grpc.FeatureResolverStub(self._channel)

    def fetch(self, project: str, environment: str, identity: str) -> list[Feature]:
        request = features_pb2.GetFeaturesRequest(project=project, environment=environment)
        attempt = 0
        while True:
            try:
                response = self._stub.GetFeatures(
                    request,
                    metadata=[("x-flagrant-identity", identity)],
                    timeout=self.timeout,
                )
            except grpc.RpcError as exc:
                code = exc.code()  # type: ignore[attr-defined]
                if code in _RETRYABLE_CODES:
                    if attempt < self.retries:
                        time.sleep(self.backoff_factor * (2**attempt))
                        attempt += 1
                        continue
                    raise TransientError(f"grpc error: {code}") from exc
                raise PermanentError(f"grpc error: {code}") from exc

            return [_feature_from_proto(feature) for feature in response.features]

    def close(self) -> None:
        self._channel.close()
