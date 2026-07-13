from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter
from typing import Any, Mapping

from slsdk.models.event import SL1Event


class SL1RuntimeError(RuntimeError):
    """Raised when the SL1 runtime environment is invalid."""


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    """
    Minimum runtime identity required to bootstrap
    an automation execution.
    """

    event_id: str
    automation_name: str


class SL1Runtime:
    """
    Adapter between the ScienceLogic SL1 runtime environment
    and the reusable automation SDK.

    Raw SL1 runtime values must not escape this adapter.
    """

    def __init__(
        self,
        values: Mapping[str, Any],
    ) -> None:
        self._values = values

    def get_identity(self) -> RuntimeIdentity:
        """
        Read the minimum SL1 runtime identity required
        to initialise the execution context and logger.
        """

        event_id = self._string_value("%e")
        automation_name = self._string_value("%N")

        if not event_id:
            raise SL1RuntimeError(
                "SL1 runtime event identifier is missing"
            )

        if not automation_name:
            raise SL1RuntimeError(
                "SL1 runtime automation name is missing"
            )

        return RuntimeIdentity(
            event_id=event_id,
            automation_name=automation_name,
        )

    def validate(
        self,
        logger: LoggerAdapter,
    ) -> None:
        """
        Validate the SL1 runtime environment.
        """

        logger.info("Validating SL1 runtime environment")

        required_keys = (
            "%e",
            "%N",
            "%M",
            "%x",
            "%X",
            "%3",
            "%_event_policy_name",
        )

        missing_keys = [
            key
            for key in required_keys
            if key not in self._values
        ]

        if missing_keys:
            logger.error(
                "SL1 runtime validation failed",
                extra={
                    "missing_runtime_keys": ",".join(missing_keys),
                },
            )

            raise SL1RuntimeError(
                "Missing required SL1 runtime values: "
                + ", ".join(missing_keys)
            )

        logger.info(
            "SL1 runtime environment validated successfully"
        )

    def create_event(
        self,
        logger: LoggerAdapter,
    ) -> SL1Event:
        """
        Build an SL1 event model from the runtime environment.
        """

        logger.info(
            "Creating SL1 event from runtime environment"
        )

        try:
            event = SL1Event.from_em7_values(
                values=self._values,
                logger=logger,
            )

            logger.info(
                "SL1 event created from runtime environment",
                extra={
                    "sl1_device_id": event.device.id,
                    "sl1_policy_id": event.policy.id,
                },
            )

            return event

        except Exception:
            logger.exception(
                "Failed to create SL1 event from runtime environment"
            )
            raise

    def _string_value(self, key: str) -> str:
        value = self._values.get(key)

        if value is None:
            return ""

        return str(value)