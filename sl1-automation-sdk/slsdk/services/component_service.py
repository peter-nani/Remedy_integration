# slsdk/services/component_service.py

from __future__ import annotations

from typing import Any

from slsdk.logging.logger import get_logger
from slsdk.repositories.component_repository import ComponentRepository

logger = get_logger(__name__)


class ComponentService:
    """Service layer for component-related operations."""

    def __init__(self, repository: ComponentRepository) -> None:
        self._repository = repository

    def get_component(self, component_id: int) -> dict[str, Any] | None:
        logger.debug(
            "Fetching component: component_id=%s",
            component_id,
        )

        component = self._repository.get_by_id(component_id)

        if not component:
            logger.warning(
                "Component not found: component_id=%s",
                component_id,
            )
            return None

        logger.debug(
            "Component found: component_id=%s",
            component_id,
        )

        return component

    def get_components_by_device(
        self,
        device_id: int,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "Fetching components for device: device_id=%s",
            device_id,
        )

        components = self._repository.get_by_device_id(device_id)

        logger.debug(
            "Components fetched: device_id=%s count=%s",
            device_id,
            len(components),
        )

        return components

    def get_component_name(self, component_id: int) -> str | None:
        component = self.get_component(component_id)

        if not component:
            return None

        return (
            component.get("component_name")
            or component.get("name")
            or component.get("comp_name")
        )

    def get_component_type(self, component_id: int) -> str | None:
        component = self.get_component(component_id)

        if not component:
            return None

        return (
            component.get("component_type")
            or component.get("type")
            or component.get("comp_type")
        )

    def get_component_device_id(self, component_id: int) -> int | None:
        component = self.get_component(component_id)

        if not component:
            return None

        device_id = (
            component.get("device_id")
            or component.get("did")
        )

        if device_id is None:
            return None

        return int(device_id)

    def component_exists(self, component_id: int) -> bool:
        exists = self._repository.get_by_id(component_id) is not None

        logger.debug(
            "Component existence check: component_id=%s exists=%s",
            component_id,
            exists,
        )

        return exists