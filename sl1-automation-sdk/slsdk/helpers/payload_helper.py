# slsdk/helpers/payload_helper.py

from __future__ import annotations

import json
from typing import Any, Mapping


class PayloadHelper:
    """Utility methods for building and normalizing payloads."""

    @staticmethod
    def remove_none_values(payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in payload.items()
            if value is not None
        }

    @staticmethod
    def remove_empty_values(payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in payload.items()
            if value not in (None, "", [], {}, ())
        }

    @staticmethod
    def merge(
        *payloads: Mapping[str, Any] | None,
        remove_none: bool = True,
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}

        for payload in payloads:
            if payload:
                merged.update(payload)

        if remove_none:
            return PayloadHelper.remove_none_values(merged)

        return merged

    @staticmethod
    def to_json(
        payload: Mapping[str, Any],
        *,
        indent: int | None = None,
        default: Any = str,
    ) -> str:
        return json.dumps(
            payload,
            indent=indent,
            default=default,
        )

    @staticmethod
    def from_json(payload: str) -> dict[str, Any]:
        data = json.loads(payload)

        if not isinstance(data, dict):
            raise ValueError("JSON payload must contain an object")

        return data

    @staticmethod
    def get_nested(
        payload: Mapping[str, Any],
        path: str,
        default: Any = None,
        separator: str = ".",
    ) -> Any:
        value: Any = payload

        for key in path.split(separator):
            if not isinstance(value, Mapping):
                return default

            value = value.get(key)

            if value is None:
                return default

        return value

    @staticmethod
    def set_nested(
        payload: dict[str, Any],
        path: str,
        value: Any,
        separator: str = ".",
    ) -> dict[str, Any]:
        keys = path.split(separator)
        target = payload

        for key in keys[:-1]:
            nested = target.get(key)

            if not isinstance(nested, dict):
                nested = {}
                target[key] = nested

            target = nested

        target[keys[-1]] = value

        return payload