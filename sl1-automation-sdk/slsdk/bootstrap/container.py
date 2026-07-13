# slsdk/bootstrap/container.py

from __future__ import annotations

from slsdk.clients.remedy_client import RemedyClient
from slsdk.config.settings import Settings
from slsdk.credentials.provider import CredentialProvider
from slsdk.database.factory import DatabaseFactory
from slsdk.repositories.certificate_repository import CertificateRepository
from slsdk.repositories.component_repository import ComponentRepository
from slsdk.repositories.device_repository import DeviceRepository
from slsdk.repositories.event_repository import EventRepository
from slsdk.repositories.interface_repository import InterfaceRepository
from slsdk.services.certificate_service import CertificateService
from slsdk.services.component_service import ComponentService
from slsdk.services.device_service import DeviceService
from slsdk.services.enrichment_service import EnrichmentService
from slsdk.services.event_service import EventService
from slsdk.services.interface_service import InterfaceService
from slsdk.services.payload_service import PayloadService
from slsdk.services.ticket_service import TicketService
from slsdk.workflows.event_ticket_workflow import EventTicketWorkflow


class Container:
    """Application dependency container."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_event_ticket_workflow(self) -> EventTicketWorkflow:
        connection = DatabaseFactory.create(self._settings)

        event_repository = EventRepository(connection)
        device_repository = DeviceRepository(connection)
        interface_repository = InterfaceRepository(connection)
        component_repository = ComponentRepository(connection)
        certificate_repository = CertificateRepository(connection)

        event_service = EventService(event_repository)
        device_service = DeviceService(device_repository)
        interface_service = InterfaceService(interface_repository)
        component_service = ComponentService(component_repository)
        certificate_service = CertificateService(certificate_repository)

        enrichment_service = EnrichmentService(
            device_service=device_service,
            interface_service=interface_service,
            component_service=component_service,
            certificate_service=certificate_service,
        )

        payload_service = PayloadService()

        credential_provider = CredentialProvider(self._settings)
        remedy_credentials = credential_provider.get_remedy_credentials()

        remedy_client = RemedyClient(
            base_url=self._settings.remedy_base_url,
            credentials=remedy_credentials,
            timeout=self._settings.remedy_timeout,
            verify_ssl=self._settings.remedy_verify_ssl,
        )

        ticket_service = TicketService(remedy_client)

        return EventTicketWorkflow(
            event_service=event_service,
            enrichment_service=enrichment_service,
            payload_service=payload_service,
            ticket_service=ticket_service,
        )