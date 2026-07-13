# slsdk/clients/remedy_client.py

from __future__ import annotations

from typing import Any, Mapping

import requests

from slsdk.clients.base import BaseClient
from slsdk.core.exceptions import SLSDKError
from slsdk.credentials.models import Credentials
from slsdk.logging.logger import get_logger

logger = get_logger(__name__)


class RemedyClientError(SLSDKError):
    """Raised when a Remedy API operation fails."""


class RemedyClient(BaseClient):
    """HTTP client for Remedy ticket operations."""

    def __init__(
        self,
        base_url: str,
        credentials: Credentials,
        *,
        timeout: int = 30,
        verify_ssl: bool = True,
        session: requests.Session | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._credentials = credentials
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._session = session or requests.Session()

        self._configure_session()

    def create(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        logger.info("Creating Remedy ticket")

        response = self._request(
            "POST",
            "/tickets",
            json=dict(payload),
        )

        logger.info(
            "Remedy ticket created: resource_id=%s",
            self._extract_resource_id(response),
        )

        return response

    def get(
        self,
        resource_id: str,
    ) -> dict[str, Any] | None:
        logger.debug(
            "Fetching Remedy ticket: resource_id=%s",
            resource_id,
        )

        response = self._request(
            "GET",
            f"/tickets/{resource_id}",
            allow_not_found=True,
        )

        if response is None:
            logger.warning(
                "Remedy ticket not found: resource_id=%s",
                resource_id,
            )

        return response

    def update(
        self,
        resource_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "Updating Remedy ticket: resource_id=%s",
            resource_id,
        )

        response = self._request(
            "PUT",
            f"/tickets/{resource_id}",
            json=dict(payload),
        )

        logger.info(
            "Remedy ticket updated: resource_id=%s",
            resource_id,
        )

        return response

    def close(
        self,
        resource_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Closing Remedy ticket: resource_id=%s",
            resource_id,
        )

        response = self._request(
            "POST",
            f"/tickets/{resource_id}/close",
            json=dict(payload or {}),
        )

        logger.info(
            "Remedy ticket closed: resource_id=%s",
            resource_id,
        )

        return response

    def _configure_session(self) -> None:
        username = getattr(self._credentials, "username", None)
        password = getattr(self._credentials, "password", None)
        token = getattr(self._credentials, "token", None)

        if token:
            self._session.headers.update(
                {"Authorization": f"Bearer {token}"}
            )
        elif username and password:
            self._session.auth = (username, password)

        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        allow_not_found: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        url = f"{self._base_url}/{path.lstrip('/')}"

        logger.debug(
            "Sending Remedy request: method=%s url=%s",
            method,
            url,
        )

        try:
            response = self._session.request(
                method=method,
                url=url,
                timeout=self._timeout,
                verify=self._verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            logger.exception(
                "Remedy request failed: method=%s url=%s",
                method,
                url,
            )
            raise RemedyClientError(
                f"Remedy request failed: {exc}"
            ) from exc

        if allow_not_found and response.status_code == 404:
            return None

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.error(
                "Remedy API error: method=%s url=%s status=%s response=%s",
                method,
                url,
                response.status_code,
                response.text,
            )
            raise RemedyClientError(
                f"Remedy API returned HTTP {response.status_code}"
            ) from exc

        if not response.content:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error(
                "Invalid Remedy JSON response: method=%s url=%s",
                method,
                url,
            )
            raise RemedyClientError(
                "Remedy API returned invalid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise RemedyClientError(
                "Remedy API response must be a JSON object"
            )

        return payload

    @staticmethod
    def _extract_resource_id(
        response: Mapping[str, Any],
    ) -> str | None:
        resource_id = (
            response.get("ticket_id")
            or response.get("incident_id")
            or response.get("id")
        )

        if resource_id is None:
            return None

        return str(resource_id)