# slsdk/services/enrichment_service.py

from __future__ import annotations

from typing import Any

from slsdk.logging.logger import get_logger
from slsdk.models.event import Event
from slsdk.services.certificate_service import CertificateService
from slsdk.services.component_service import ComponentService
from slsdk.services.device_service import DeviceService
from slsdk.services.interface_service import InterfaceService

logger = get_logger(__name__)


class EnrichmentService:
    """Enriches event data with related SL1 resource information."""

    def __init__(
        self,
        device_service: DeviceService,
        interface_service: InterfaceService,
        component_service: ComponentService,
        certificate_service: CertificateService,
    ) -> None:
        self._device_service = device_service
        self._interface_service = interface_service
        self._component_service = component_service
        self._certificate_service = certificate_service

    def enrich(self, event: Event) -> dict[str, Any]:
        logger.info(
            "Starting event enrichment: event_id=%s device_id=%s",
            event.event_id,
            event.device_id,
        )

        payload = self._event_payload(event)

        if event.device_id is not None:
            payload["device"] = self._device_service.get_device(
                event.device_id
            )

        interface_id = getattr(event, "interface_id", None)

        if interface_id is not None:
            payload["interface"] = self._interface_service.get_interface(
                interface_id
            )

        component_id = getattr(event, "component_id", None)

        if component_id is not None:
            payload["component"] = self._component_service.get_component(
                component_id
            )

        certificate_id = getattr(event, "certificate_id", None)

        if certificate_id is not None:
            payload["certificate"] = (
                self._certificate_service.get_certificate(
                    certificate_id
                )
            )

        logger.info(
            "Event enrichment completed: event_id=%s",
            event.event_id,
        )

        return payload

    @staticmethod
    def _event_payload(event: Event) -> dict[str, Any]:
        if hasattr(event, "model_dump"):
            return event.model_dump()

        if hasattr(event, "dict"):
            return event.dict()

        return vars(event).copy()