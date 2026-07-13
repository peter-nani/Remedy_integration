# slsdk/services/interface_service.py

from __future__ import annotations

from typing import Any

from slsdk.logging.logger import get_logger
from slsdk.repositories.interface_repository import InterfaceRepository

logger = get_logger(__name__)


class InterfaceService:
    """Service layer for interface-related operations."""

    def __init__(self, repository: InterfaceRepository) -> None:
        self._repository = repository

    def get_interface(self, interface_id: int) -> dict[str, Any] | None:
        logger.debug(
            "Fetching interface: interface_id=%s",
            interface_id,
        )

        interface = self._repository.get_by_id(interface_id)

        if not interface:
            logger.warning(
                "Interface not found: interface_id=%s",
                interface_id,
            )
            return None

        return interface

    def get_interfaces_by_device(
        self,
        device_id: int,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "Fetching interfaces for device: device_id=%s",
            device_id,
        )

        interfaces = self._repository.get_by_device_id(device_id)

        logger.debug(
            "Interfaces fetched: device_id=%s count=%s",
            device_id,
            len(interfaces),
        )

        return interfaces

    def get_interface_name(self, interface_id: int) -> str | None:
        interface = self.get_interface(interface_id)

        if not interface:
            return None

        return (
            interface.get("interface_name")
            or interface.get("name")
            or interface.get("if_name")
        )

    def get_interface_alias(self, interface_id: int) -> str | None:
        interface = self.get_interface(interface_id)

        if not interface:
            return None

        return (
            interface.get("interface_alias")
            or interface.get("alias")
            or interface.get("if_alias")
        )

    def get_interface_ip(self, interface_id: int) -> str | None:
        interface = self.get_interface(interface_id)

        if not interface:
            return None

        return (
            interface.get("ip")
            or interface.get("ip_address")
            or interface.get("interface_ip")
        )

    def interface_exists(self, interface_id: int) -> bool:
        exists = self._repository.get_by_id(interface_id) is not None

        logger.debug(
            "Interface existence check: interface_id=%s exists=%s",
            interface_id,
            exists,
        )

        return exists