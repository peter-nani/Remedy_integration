# slsdk/services/payload_service.py

from __future__ import annotations

from typing import Any, Mapping

from slsdk.helpers.payload_helper import PayloadHelper
from slsdk.logging.logger import get_logger

logger = get_logger(__name__)


class PayloadService:
    """Builds normalized outbound ticket payloads."""

    def build(
        self,
        event_data: Mapping[str, Any],
        *,
        defaults: Mapping[str, Any] | None = None,
        overrides: Mapping[str, Any] | None = None,
        remove_empty: bool = False,
    ) -> dict[str, Any]:
        event_id = event_data.get("event_id")

        logger.info(
            "Building outbound payload: event_id=%s",
            event_id,
        )

        payload = PayloadHelper.merge(
            defaults,
            event_data,
            overrides,
            remove_none=True,
        )

        if remove_empty:
            payload = PayloadHelper.remove_empty_values(payload)

        logger.info(
            "Outbound payload built: event_id=%s fields=%s",
            event_id,
            len(payload),
        )

        return payload

    def build_json(
        self,
        event_data: Mapping[str, Any],
        *,
        defaults: Mapping[str, Any] | None = None,
        overrides: Mapping[str, Any] | None = None,
        remove_empty: bool = False,
        indent: int | None = None,
    ) -> str:
        payload = self.build(
            event_data,
            defaults=defaults,
            overrides=overrides,
            remove_empty=remove_empty,
        )

        return PayloadHelper.to_json(
            payload,
            indent=indent,
        )