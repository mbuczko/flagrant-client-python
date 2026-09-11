from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetFeaturesRequest(_message.Message):
    __slots__ = ("project", "environment")
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    project: str
    environment: str
    def __init__(self, project: _Optional[str] = ..., environment: _Optional[str] = ...) -> None: ...

class GetFeaturesResponse(_message.Message):
    __slots__ = ("features",)
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    features: _containers.RepeatedCompositeFieldContainer[Feature]
    def __init__(self, features: _Optional[_Iterable[_Union[Feature, _Mapping]]] = ...) -> None: ...

class Feature(_message.Message):
    __slots__ = ("feature_id", "name", "value", "is_enabled")
    FEATURE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    IS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    feature_id: int
    name: str
    value: VariantValue
    is_enabled: bool
    def __init__(self, feature_id: _Optional[int] = ..., name: _Optional[str] = ..., value: _Optional[_Union[VariantValue, _Mapping]] = ..., is_enabled: _Optional[bool] = ...) -> None: ...

class VariantValue(_message.Message):
    __slots__ = ("text", "json", "toml")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    JSON_FIELD_NUMBER: _ClassVar[int]
    TOML_FIELD_NUMBER: _ClassVar[int]
    text: str
    json: str
    toml: str
    def __init__(self, text: _Optional[str] = ..., json: _Optional[str] = ..., toml: _Optional[str] = ...) -> None: ...
