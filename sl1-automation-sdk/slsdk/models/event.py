from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Device:
    id: str
    name: str
    ip_address: str
    class_id: str
    class_name: str
    category_id: str
    category_name: str
    parent_id: str
    parent_name: str
    root_id: str
    root_name: str


@dataclass(frozen=True, slots=True)
class Entity:
    entity_type: str
    entity_id: str
    entity_name: str
    sub_entity_type: str
    sub_entity_id: str
    sub_entity_name: str


@dataclass(frozen=True, slots=True)
class EventPolicy:
    id: str
    name: str
    external_id: str
    cause_action_text: str


@dataclass(frozen=True, slots=True)
class Organization:
    id: str
    name: str
    billing_id: str
    crm_id: str
    impacted_organization: str


@dataclass(frozen=True, slots=True)
class Asset:
    serial: str
    device_id: str
    location: str
    room: str
    floor: str
    plate: str
    panel: str
    zone: str
    punch: str
    rack: str
    shelf: str
    tag: str
    model: str
    make: str


@dataclass(frozen=True, slots=True)
class EventTimes:
    first_occurrence: str
    last_occurrence: str
    active_at: str
    deleted_at: str


@dataclass(frozen=True, slots=True)
class Automation:
    action_name: str
    policy_name: str
    policy_note: str


@dataclass(frozen=True, slots=True)
class SL1Event:
    id: str
    message: str
    severity: str
    severity_numeric: str
    counter: str
    threshold: str
    result_value: str
    user_note: str
    cleared_by: str
    external_ticket_reference: str
    source: str
    source_numeric: str
    category: str
    stateful: str
    url: str
    system: str
    alert_id: str
    identifier_pattern: str

    device: Device
    entity: Entity
    policy: EventPolicy
    organization: Organization
    asset: Asset
    times: EventTimes
    automation: Automation

    @classmethod
    def from_em7_values(
        cls,
        values: Mapping[str, Any],
        logger: LoggerAdapter,
    ) -> "SL1Event":
        logger.info("Starting SL1 event model creation")

        try:
            event = cls(
                id=_as_string(values, "%e"),
                message=_as_string(values, "%M"),
                severity=_as_string(values, "%S"),
                severity_numeric=_as_string(values, "%s"),
                counter=_as_string(values, "%c"),
                threshold=_as_string(values, "%T"),
                result_value=_as_string(values, "%V"),
                user_note=_as_string(values, "%_user_note"),
                cleared_by=_as_string(values, "%4"),
                external_ticket_reference=_as_string(
                    values,
                    "%_ext_ticket_ref",
                ),
                source=_as_string(values, "%Z"),
                source_numeric=_as_string(values, "%z"),
                category=_as_string(values, "%G"),
                stateful=_as_string(values, "%f"),
                url=_as_string(values, "%H"),
                system=_as_string(values, "%r"),
                alert_id=_as_string(values, "%F"),
                identifier_pattern=_as_string(values, "%I"),

                device=Device(
                    id=_as_string(values, "%x"),
                    name=_as_string(values, "%X"),
                    ip_address=_as_string(values, "%a"),
                    class_id=_as_string(values, "%_class_id"),
                    class_name=_as_string(values, "%_class_name"),
                    category_id=_as_string(values, "%_category_id"),
                    category_name=_as_string(
                        values,
                        "%_category_name",
                    ),
                    parent_id=_as_string(values, "%_parent_id"),
                    parent_name=_as_string(values, "%_parent_name"),
                    root_id=_as_string(values, "%_root_id"),
                    root_name=_as_string(values, "%_root_name"),
                ),

                entity=Entity(
                    entity_type=_as_string(values, "%1"),
                    entity_id=_as_string(values, "%x"),
                    entity_name=_as_string(values, "%X"),
                    sub_entity_type=_as_string(values, "%2"),
                    sub_entity_id=_as_string(values, "%y"),
                    sub_entity_name=_as_string(values, "%Y"),
                ),

                policy=EventPolicy(
                    id=_as_string(values, "%3"),
                    name=_as_string(values, "%_event_policy_name"),
                    external_id=_as_string(values, "%E"),
                    cause_action_text=_as_string(values, "%R"),
                ),

                organization=Organization(
                    id=_as_string(values, "%o"),
                    name=_as_string(values, "%O"),
                    billing_id=_as_string(values, "%B"),
                    crm_id=_as_string(values, "%C"),
                    impacted_organization=_as_string(values, "%b"),
                ),

                asset=Asset(
                    serial=_as_string(values, "%g"),
                    device_id=_as_string(values, "%h"),
                    location=_as_string(values, "%i"),
                    room=_as_string(values, "%k"),
                    floor=_as_string(values, "%K"),
                    plate=_as_string(values, "%P"),
                    panel=_as_string(values, "%p"),
                    zone=_as_string(values, "%q"),
                    punch=_as_string(values, "%Q"),
                    rack=_as_string(values, "%U"),
                    shelf=_as_string(values, "%u"),
                    tag=_as_string(values, "%v"),
                    model=_as_string(values, "%w"),
                    make=_as_string(values, "%W"),
                ),

                times=EventTimes(
                    first_occurrence=_as_string(values, "%D"),
                    last_occurrence=_as_string(values, "%d"),
                    active_at=_as_string(values, "%6"),
                    deleted_at=_as_string(values, "%5"),
                ),

                automation=Automation(
                    action_name=_as_string(values, "%N"),
                    policy_name=_as_string(values, "%n"),
                    policy_note=_as_string(values, "%m"),
                ),
            )

            logger.info(
                "SL1 event model created successfully",
                extra={
                    "sl1_device_id": event.device.id,
                    "sl1_policy_id": event.policy.id,
                },
            )

            if not event.message:
                logger.warning("SL1 event contains a blank message")

            return event

        except Exception:
            logger.exception("Failed to create SL1 event model")
            raise


def _as_string(
    values: Mapping[str, Any],
    key: str,
) -> str:
    value = values.get(key)

    if value is None:
        return ""

    return str(value)