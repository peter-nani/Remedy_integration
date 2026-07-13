# slsdk/workflows/event_ticket_workflow.py

from __future__ import annotations

from typing import Any, Mapping

from slsdk.logging.logger import get_logger
from slsdk.services.enrichment_service import EnrichmentService
from slsdk.services.event_service import EventService
from slsdk.services.payload_service import PayloadService
from slsdk.services.ticket_service import TicketService

logger = get_logger(__name__)


class EventTicketWorkflow:
    """Coordinates the SL1 event-to-ticket execution flow."""

    def __init__(
        self,
        event_service: EventService,
        enrichment_service: EnrichmentService,
        payload_service: PayloadService,
        ticket_service: TicketService,
    ) -> None:
        self._event_service = event_service
        self._enrichment_service = enrichment_service
        self._payload_service = payload_service
        self._ticket_service = ticket_service

    def execute(
        self,
        event_id: int,
        *,
        defaults: Mapping[str, Any] | None = None,
        overrides: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Starting event ticket workflow: event_id=%s",
            event_id,
        )

        event = self._event_service.to_model(event_id)

        if event is None:
            logger.error(
                "Workflow stopped because event was not found: event_id=%s",
                event_id,
            )
            raise ValueError(f"Event not found: {event_id}")

        logger.debug(
            "Enriching event data: event_id=%s",
            event_id,
        )

        enriched_data = self._enrichment_service.enrich(event)

        logger.debug(
            "Building ticket payload: event_id=%s",
            event_id,
        )

        payload = self._payload_service.build(
            enriched_data,
            defaults=defaults,
            overrides=overrides,
            remove_empty=True,
        )

        logger.info(
            "Submitting ticket payload: event_id=%s",
            event_id,
        )

        ticket = self._ticket_service.create_ticket(payload)

        logger.info(
            "Event ticket workflow completed: event_id=%s ticket_id=%s",
            event_id,
            self._extract_ticket_id(ticket),
        )

        return ticket

    @staticmethod
    def _extract_ticket_id(
        ticket: Mapping[str, Any],
    ) -> str | None:
        ticket_id = (
            ticket.get("ticket_id")
            or ticket.get("incident_id")
            or ticket.get("id")
        )

        if ticket_id is None:
            return None

        return str(ticket_id)