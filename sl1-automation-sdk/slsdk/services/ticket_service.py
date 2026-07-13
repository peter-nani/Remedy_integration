# slsdk/services/ticket_service.py

from __future__ import annotations

from typing import Any, Mapping

from slsdk.clients.base import BaseClient
from slsdk.logging.logger import get_logger

logger = get_logger(__name__)


class TicketService:
    """Coordinates external ticket lifecycle operations."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def create_ticket(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "Creating ticket: event_id=%s",
            payload.get("event_id"),
        )

        response = self._client.create(payload)

        logger.info(
            "Ticket creation completed: event_id=%s ticket_id=%s",
            payload.get("event_id"),
            self._extract_ticket_id(response),
        )

        return response

    def get_ticket(
        self,
        ticket_id: str,
    ) -> dict[str, Any] | None:
        logger.debug(
            "Fetching ticket: ticket_id=%s",
            ticket_id,
        )

        return self._client.get(ticket_id)

    def update_ticket(
        self,
        ticket_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "Updating ticket: ticket_id=%s",
            ticket_id,
        )

        response = self._client.update(
            ticket_id,
            payload,
        )

        logger.info(
            "Ticket update completed: ticket_id=%s",
            ticket_id,
        )

        return response

    def close_ticket(
        self,
        ticket_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Closing ticket: ticket_id=%s",
            ticket_id,
        )

        response = self._client.close(
            ticket_id,
            payload,
        )

        logger.info(
            "Ticket close completed: ticket_id=%s",
            ticket_id,
        )

        return response

    @staticmethod
    def _extract_ticket_id(
        response: Mapping[str, Any],
    ) -> str | None:
        ticket_id = (
            response.get("ticket_id")
            or response.get("incident_id")
            or response.get("id")
        )

        if ticket_id is None:
            return None

        return str(ticket_id)