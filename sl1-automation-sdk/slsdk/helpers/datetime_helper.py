from __future__ import annotations

from datetime import datetime, timezone
from logging import LoggerAdapter

from slsdk.core.exceptions import TransformationError


class DateTimeHelper:
    def __init__(
        self,
        logger: LoggerAdapter,
    ) -> None:
        self._logger = logger

        self._logger.info(
            "Datetime helper initialised"
        )

    def utc_now(self) -> datetime:
        self._logger.debug(
            "Retrieving current UTC datetime"
        )

        return datetime.now(
            timezone.utc
        )

    def utc_timestamp(self) -> int:
        self._logger.debug(
            "Retrieving current UTC timestamp"
        )

        return int(
            self.utc_now().timestamp()
        )

    def from_timestamp(
        self,
        timestamp: int | float,
    ) -> datetime:
        self._logger.debug(
            "Converting timestamp to UTC datetime"
        )

        try:
            return datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
            OSError,
        ) as error:
            self._logger.exception(
                "Failed to convert timestamp to UTC datetime"
            )

            raise TransformationError(
                "Unable to convert timestamp to UTC datetime",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def to_timestamp(
        self,
        value: datetime,
    ) -> int:
        self._logger.debug(
            "Converting datetime to timestamp"
        )

        try:
            normalized_value = self.ensure_utc(
                value
            )

            return int(
                normalized_value.timestamp()
            )

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to convert datetime to timestamp"
            )

            raise TransformationError(
                "Unable to convert datetime to timestamp",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def ensure_utc(
        self,
        value: datetime,
    ) -> datetime:
        self._logger.debug(
            "Normalising datetime to UTC"
        )

        if not isinstance(
            value,
            datetime,
        ):
            raise TransformationError(
                "Value must be a datetime instance",
                details={
                    "received_type": type(value).__name__,
                },
            )

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    def elapsed_seconds(
        self,
        start: datetime,
        end: datetime | None = None,
    ) -> int:
        self._logger.debug(
            "Calculating elapsed seconds"
        )

        try:
            start_value = self.ensure_utc(
                start
            )

            end_value = self.ensure_utc(
                end or self.utc_now()
            )

            elapsed = (
                end_value - start_value
            ).total_seconds()

            return int(elapsed)

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to calculate elapsed seconds"
            )

            raise TransformationError(
                "Unable to calculate elapsed seconds",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def has_elapsed(
        self,
        start: datetime,
        interval_seconds: int,
        *,
        end: datetime | None = None,
    ) -> bool:
        self._logger.debug(
            "Checking datetime interval",
            extra={
                "interval_seconds": interval_seconds,
            },
        )

        if interval_seconds < 0:
            raise TransformationError(
                "Interval seconds cannot be negative",
                details={
                    "interval_seconds": interval_seconds,
                },
            )

        elapsed = self.elapsed_seconds(
            start=start,
            end=end,
        )

        return elapsed >= interval_seconds

    def format_iso(
        self,
        value: datetime,
    ) -> str:
        self._logger.debug(
            "Formatting datetime as ISO string"
        )

        try:
            return self.ensure_utc(
                value
            ).isoformat()

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to format datetime as ISO string"
            )

            raise TransformationError(
                "Unable to format datetime as ISO string",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error