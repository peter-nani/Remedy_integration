from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter

from slsdk.database.connection import DatabaseConnection
from slsdk.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class EventRecord:
    event_id: int
    device_id: int
    policy_id: int
    message: str
    severity: int
    acknowledged: bool
    user_note: str


class EventRepository(BaseRepository[EventRecord]):
    def __init__(
        self,
        database: DatabaseConnection,
        logger: LoggerAdapter,
    ) -> None:
        super().__init__(
            database=database,
            logger=logger,
        )

    def get_event(
        self,
        event_id: int,
    ) -> EventRecord | None:
        self._logger.debug(
            "Retrieving event",
            extra={
                "event_id": event_id,
            },
        )

        query = """
            SELECT
                e.id,
                e.did,
                e.event_policy_id,
                e.message,
                e.severity,
                e.acknowledged,
                e.user_note
            FROM master.events_active AS e
            WHERE e.id = %s
        """

        try:
            self._database.execute(
                query,
                (event_id,),
            )

            rows = self._database.fetchall()

            if not rows:
                self._logger.warning(
                    "Event not found",
                    extra={
                        "event_id": event_id,
                    },
                )

                return None

            row = rows[0]

            event = EventRecord(
                event_id=int(row[0]),
                device_id=int(row[1]),
                policy_id=int(row[2]),
                message=str(row[3] or ""),
                severity=int(row[4]),
                acknowledged=bool(row[5]),
                user_note=str(row[6] or ""),
            )

            self._logger.debug(
                "Event retrieved successfully",
                extra={
                    "event_id": event.event_id,
                    "device_id": event.device_id,
                    "policy_id": event.policy_id,
                },
            )

            return event

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve event",
                error,
                details={
                    "event_id": event_id,
                },
            ) from error

    def get_user_note(
        self,
        event_id: int,
    ) -> str | None:
        self._logger.debug(
            "Retrieving event user note",
            extra={
                "event_id": event_id,
            },
        )

        query = """
            SELECT user_note
            FROM master.events_active
            WHERE id = %s
        """

        try:
            value = self._database.fetch_value(
                query,
                (event_id,),
            )

            if value is None:
                self._logger.warning(
                    "Event user note not found",
                    extra={
                        "event_id": event_id,
                    },
                )

                return None

            self._logger.debug(
                "Event user note retrieved successfully",
                extra={
                    "event_id": event_id,
                },
            )

            return str(value)

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve event user note",
                error,
                details={
                    "event_id": event_id,
                },
            ) from error

    def acknowledge(
        self,
        *,
        event_id: int,
        user_id: int,
    ) -> None:
        self._logger.info(
            "Acknowledging event",
            extra={
                "event_id": event_id,
                "user_id": user_id,
            },
        )

        query = """
            UPDATE master.events_active
            SET
                acknowledged = 1,
                acknowledged_by = %s
            WHERE id = %s
        """

        try:
            self._database.execute(
                query,
                (
                    user_id,
                    event_id,
                ),
            )

            self._logger.info(
                "Event acknowledged successfully",
                extra={
                    "event_id": event_id,
                    "user_id": user_id,
                },
            )

        except Exception as error:
            raise self._repository_error(
                "Failed to acknowledge event",
                error,
                details={
                    "event_id": event_id,
                    "user_id": user_id,
                },
            ) from error

    def update_user_note(
        self,
        *,
        event_id: int,
        user_note: str,
    ) -> None:
        self._logger.info(
            "Updating event user note",
            extra={
                "event_id": event_id,
            },
        )

        query = """
            UPDATE master.events_active
            SET user_note = %s
            WHERE id = %s
        """

        try:
            self._database.execute(
                query,
                (
                    user_note,
                    event_id,
                ),
            )

            self._logger.info(
                "Event user note updated successfully",
                extra={
                    "event_id": event_id,
                },
            )

        except Exception as error:
            raise self._repository_error(
                "Failed to update event user note",
                error,
                details={
                    "event_id": event_id,
                },
            ) from error