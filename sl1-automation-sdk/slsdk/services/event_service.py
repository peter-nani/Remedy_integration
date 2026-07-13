# slsdk/services/event_service.py

from __future__ import annotations

from typing import Any

from slsdk.logging.logger import get_logger
from slsdk.models.event import Event
from slsdk.repositories.event_repository import EventRepository

logger = get_logger(__name__)


class EventService:
    """Service layer for event-related operations."""

    def __init__(self, repository: EventRepository) -> None:
        self._repository = repository

    def get_event(self, event_id: int) -> dict[str, Any] | None:
        logger.debug("Fetching event: event_id=%s", event_id)

        event = self._repository.get_by_id(event_id)

        if not event:
            logger.warning("Event not found: event_id=%s", event_id)
            return None

        logger.debug("Event found: event_id=%s", event_id)
        return event

    def get_active_events_by_device(
        self,
        device_id: int,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "Fetching active events for device: device_id=%s",
            device_id,
        )

        events = self._repository.get_active_by_device_id(device_id)

        logger.debug(
            "Active events fetched: device_id=%s count=%s",
            device_id,
            len(events),
        )

        return events

    def get_event_message(self, event_id: int) -> str | None:
        event = self.get_event(event_id)

        if not event:
            return None

        return (
            event.get("message")
            or event.get("event_message")
            or event.get("msg")
        )

    def get_event_severity(self, event_id: int) -> Any | None:
        event = self.get_event(event_id)

        if not event:
            return None

        return (
            event.get("severity")
            or event.get("event_severity")
        )

    def get_event_device_id(self, event_id: int) -> int | None:
        event = self.get_event(event_id)

        if not event:
            return None

        device_id = event.get("device_id") or event.get("did")

        if device_id is None:
            return None

        return int(device_id)

    def to_model(self, event_id: int) -> Event | None:
        event = self.get_event(event_id)

        if not event:
            return None

        logger.debug(
            "Converting event payload to Event model: event_id=%s",
            event_id,
        )

        return Event(**event)

    def event_exists(self, event_id: int) -> bool:
        exists = self._repository.get_by_id(event_id) is not None

        logger.debug(
            "Event existence check: event_id=%s exists=%s",
            event_id,
            exists,
        )

        return exists