# slsdk/clients/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class BaseClient(ABC):
    """Base contract for external service clients."""

    @abstractmethod
    def create(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Create a resource in the external service."""
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        resource_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve a resource from the external service."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        resource_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Update a resource in the external service."""
        raise NotImplementedError

    @abstractmethod
    def close(
        self,
        resource_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Close or resolve a resource in the external service."""
        raise NotImplementedError