# slsdk/services/device_service.py

from __future__ import annotations

from typing import Any

from slsdk.logging.logger import get_logger
from slsdk.repositories.device_repository import DeviceRepository

logger = get_logger(__name__)


class DeviceService:
    """Service layer for device-related operations."""

    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    def get_device(self, device_id: int) -> dict[str, Any] | None:
        logger.debug("Fetching device: device_id=%s", device_id)

        device = self._repository.get_by_id(device_id)

        if not device:
            logger.warning("Device not found: device_id=%s", device_id)
            return None

        logger.debug("Device found: device_id=%s", device_id)
        return device

    def get_device_name(self, device_id: int) -> str | None:
        device = self.get_device(device_id)

        if not device:
            return None

        return device.get("device_name") or device.get("name")

    def get_device_ip(self, device_id: int) -> str | None:
        device = self.get_device(device_id)

        if not device:
            return None

        return (
            device.get("ip")
            or device.get("ip_address")
            or device.get("device_ip")
        )

    def get_device_class(self, device_id: int) -> str | None:
        device = self.get_device(device_id)

        if not device:
            return None

        return (
            device.get("device_class")
            or device.get("device_class_description")
            or device.get("class_description")
        )

    def get_device_organization_id(self, device_id: int) -> int | None:
        device = self.get_device(device_id)

        if not device:
            return None

        organization_id = (
            device.get("organization_id")
            or device.get("org_id")
        )

        if organization_id is None:
            return None

        return int(organization_id)

    def device_exists(self, device_id: int) -> bool:
        exists = self._repository.get_by_id(device_id) is not None

        logger.debug(
            "Device existence check: device_id=%s exists=%s",
            device_id,
            exists,
        )

        return exists