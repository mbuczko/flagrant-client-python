from typing import Any

from pydantic import BaseModel, Json, field_validator

_UNSET = object()


class TextValue(BaseModel):
    value: str

    def __init__(self, value: Any = _UNSET, **data: Any) -> None:
        if value is not _UNSET:
            data["value"] = value
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"


class JsonValue(BaseModel):
    # the API delivers json values as escaped JSON strings
    value: Json[dict[str, Any]]

    def __init__(self, value: Any = _UNSET, **data: Any) -> None:
        if value is not _UNSET:
            data["value"] = value
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"


class TomlValue(BaseModel):
    value: str

    def __init__(self, value: Any = _UNSET, **data: Any) -> None:
        if value is not _UNSET:
            data["value"] = value
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"


FeatureValue = TextValue | JsonValue | TomlValue

_VALUE_MODELS = {
    "text": TextValue,
    "json": JsonValue,
    "toml": TomlValue,
}


class Feature(BaseModel):
    feature_id: int
    name: str
    value: FeatureValue

    @field_validator("value", mode="before")
    @classmethod
    def _build_value(cls, v: Any) -> Any:
        # The API sends the value as a single-key map: {"text": "..."},
        # {"json": {...}} or {"toml": "..."}. The key tells us which
        # value model to build.
        if isinstance(v, dict) and len(v) == 1:
            type_, value = next(iter(v.items()))

            # Fall back to TextValue for unrecognized types, treating
            # the payload as plain text.
            model = _VALUE_MODELS.get(type_, TextValue)
            return model(value)
        return v
