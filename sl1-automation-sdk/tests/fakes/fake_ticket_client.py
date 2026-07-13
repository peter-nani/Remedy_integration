from __future__ import annotations

from typing import Any, Mapping

from slsdk.clients.base import BaseClient
from slsdk.logging.logger import get_logger

logger = get_logger(__name__)


class FakeTicketClient(BaseClient):
    """Fake ticket client for local and SL1 SDK testing."""

    def create(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        logger.info("FAKE ticket creation requested")
        logger.info("FAKE payload: %s", dict(payload))

        return {
            "ticket_id": "DUMMY-10001",
            "status": "created",
            "payload": dict(payload),
        }

    def get(
        self,
        resource_id: str,
    ) -> dict[str, Any] | None:
        logger.info(
            "FAKE ticket fetch: resource_id=%s",
            resource_id,
        )

        return {
            "ticket_id": resource_id,
            "status": "open",
        }

    def update(
        self,
        resource_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "FAKE ticket update: resource_id=%s payload=%s",
            resource_id,
            dict(payload),
        )

        return {
            "ticket_id": resource_id,
            "status": "updated",
            "payload": dict(payload),
        }

    def close(
        self,
        resource_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "FAKE ticket close: resource_id=%s",
            resource_id,
        )

        return {
            "ticket_id": resource_id,
            "status": "closed",
            "payload": dict(payload or {}),
        }