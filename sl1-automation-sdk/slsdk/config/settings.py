from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter
from typing import Any, Mapping

from slsdk.core.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class RetrySettings:
    interval_seconds: int
    max_attempts: int


@dataclass(frozen=True, slots=True)
class TicketingSettings:
    modification_interval_seconds: int
    ticketable_ack_user_id: int
    non_ticketable_ack_user_id: int
    force_ticket_uri: str


@dataclass(frozen=True, slots=True)
class SL1Settings:
    credential_id: int


@dataclass(frozen=True, slots=True)
class RemedySettings:
    credential_id: int


@dataclass(frozen=True, slots=True)
class CDBSettings:
    device_id: int
    device_name: str
    device_ip: str


@dataclass(frozen=True, slots=True)
class QRadarSettings:
    magnitude_threshold: int


@dataclass(frozen=True, slots=True)
class EventPolicySettings:
    availability_policy_id: int
    availability_latency_policy_id: int
    sl_cdb_ticket_policy_ids: frozenset[int]


@dataclass(frozen=True, slots=True)
class ApplicationSettings:
    retry: RetrySettings
    ticketing: TicketingSettings
    sl1: SL1Settings
    remedy: RemedySettings
    cdb: CDBSettings
    qradar: QRadarSettings
    event_policies: EventPolicySettings

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, Any],
        logger: LoggerAdapter,
    ) -> "ApplicationSettings":
        logger.info("Starting application configuration loading")

        try:
            settings = cls(
                retry=RetrySettings(
                    interval_seconds=_required_int(
                        values,
                        "retry_interval",
                    ),
                    max_attempts=_optional_int(
                        values,
                        "max_retry_attempts",
                        default=5,
                    ),
                ),
                ticketing=TicketingSettings(
                    modification_interval_seconds=_required_int(
                        values,
                        "modification_interval",
                    ),
                    ticketable_ack_user_id=_required_int(
                        values,
                        "ack_user_tktable_alert",
                    ),
                    non_ticketable_ack_user_id=_required_int(
                        values,
                        "ack_user_non_tktable_alert",
                    ),
                    force_ticket_uri=_required_string(
                        values,
                        "force_ticket_uri",
                    ),
                ),
                sl1=SL1Settings(
                    credential_id=_required_int(
                        values,
                        "sl_db_credential_id",
                    ),
                ),
                remedy=RemedySettings(
                    credential_id=_required_int(
                        values,
                        "remedy_create_update_ticket_webservice_credential_id",
                    ),
                ),
                cdb=CDBSettings(
                    device_id=_required_int(
                        values,
                        "cdb_device_id",
                    ),
                    device_name=_required_string(
                        values,
                        "cdb_device_name",
                    ),
                    device_ip=_required_string(
                        values,
                        "cdb_device_ip",
                    ),
                ),
                qradar=QRadarSettings(
                    magnitude_threshold=_required_int(
                        values,
                        "qradar_magnitude_ticketing_threshold",
                    ),
                ),
                event_policies=EventPolicySettings(
                    availability_policy_id=_required_int(
                        values,
                        "availability_ep_id",
                    ),
                    availability_latency_policy_id=_required_int(
                        values,
                        "availability_latency_ep_id",
                    ),
                    sl_cdb_ticket_policy_ids=_required_int_set(
                        values,
                        "ep_create_ticket_SLDB",
                    ),
                ),
            )

            _validate_settings(
                settings=settings,
                logger=logger,
            )

            logger.info(
                "Application configuration loaded successfully",
                extra={
                    "retry_interval_seconds":
                        settings.retry.interval_seconds,
                    "max_retry_attempts":
                        settings.retry.max_attempts,
                    "modification_interval_seconds":
                        settings.ticketing.modification_interval_seconds,
                    "sl_cdb_policy_count":
                        len(
                            settings
                            .event_policies
                            .sl_cdb_ticket_policy_ids
                        ),
                },
            )

            return settings

        except ConfigurationError:
            logger.exception(
                "Application configuration loading failed"
            )
            raise

        except Exception as error:
            logger.exception(
                "Unexpected error while loading application configuration"
            )

            raise ConfigurationError(
                "Unable to load application configuration",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error


def _validate_settings(
    settings: ApplicationSettings,
    logger: LoggerAdapter,
) -> None:
    logger.info("Validating application configuration")

    if settings.retry.interval_seconds < 0:
        raise ConfigurationError(
            "Retry interval cannot be negative",
            details={
                "retry_interval_seconds":
                    settings.retry.interval_seconds,
            },
        )

    if settings.retry.max_attempts < 1:
        raise ConfigurationError(
            "Maximum retry attempts must be at least one",
            details={
                "max_retry_attempts":
                    settings.retry.max_attempts,
            },
        )

    if settings.ticketing.modification_interval_seconds < 0:
        raise ConfigurationError(
            "Modification interval cannot be negative",
            details={
                "modification_interval_seconds":
                    settings.ticketing.modification_interval_seconds,
            },
        )

    if settings.qradar.magnitude_threshold < 0:
        raise ConfigurationError(
            "QRadar magnitude threshold cannot be negative",
            details={
                "qradar_magnitude_threshold":
                    settings.qradar.magnitude_threshold,
            },
        )

    logger.info("Application configuration validated successfully")


def _required_string(
    values: Mapping[str, Any],
    key: str,
) -> str:
    value = values.get(key)

    if value is None:
        raise ConfigurationError(
            f"Required configuration value is missing: {key}",
            details={
                "configuration_key": key,
            },
        )

    value = str(value).strip()

    if not value:
        raise ConfigurationError(
            f"Required configuration value is blank: {key}",
            details={
                "configuration_key": key,
            },
        )

    return value


def _required_int(
    values: Mapping[str, Any],
    key: str,
) -> int:
    value = values.get(key)

    if value is None:
        raise ConfigurationError(
            f"Required configuration value is missing: {key}",
            details={
                "configuration_key": key,
            },
        )

    try:
        return int(value)

    except (TypeError, ValueError) as error:
        raise ConfigurationError(
            f"Configuration value must be an integer: {key}",
            details={
                "configuration_key": key,
                "received_value": str(value),
            },
        ) from error


def _optional_int(
    values: Mapping[str, Any],
    key: str,
    *,
    default: int,
) -> int:
    value = values.get(key)

    if value is None or str(value).strip() == "":
        return default

    try:
        return int(value)

    except (TypeError, ValueError) as error:
        raise ConfigurationError(
            f"Configuration value must be an integer: {key}",
            details={
                "configuration_key": key,
                "received_value": str(value),
            },
        ) from error


def _required_int_set(
    values: Mapping[str, Any],
    key: str,
) -> frozenset[int]:
    raw_value = _required_string(
        values,
        key,
    )

    cleaned_value = (
        raw_value
        .strip()
        .strip("[")
        .strip("]")
    )

    if not cleaned_value:
        return frozenset()

    try:
        return frozenset(
            int(item.strip())
            for item in cleaned_value.split(",")
            if item.strip()
        )

    except ValueError as error:
        raise ConfigurationError(
            f"Configuration value must contain integer IDs: {key}",
            details={
                "configuration_key": key,
                "received_value": raw_value,
            },
        ) from error