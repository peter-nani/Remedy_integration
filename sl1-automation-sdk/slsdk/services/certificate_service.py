# slsdk/services/certificate_service.py

from __future__ import annotations

from typing import Any

from slsdk.logging.logger import get_logger
from slsdk.repositories.certificate_repository import CertificateRepository

logger = get_logger(__name__)


class CertificateService:
    """Service layer for certificate-related operations."""

    def __init__(self, repository: CertificateRepository) -> None:
        self._repository = repository

    def get_certificate(self, certificate_id: int) -> dict[str, Any] | None:
        logger.debug(
            "Fetching certificate: certificate_id=%s",
            certificate_id,
        )

        certificate = self._repository.get_by_id(certificate_id)

        if not certificate:
            logger.warning(
                "Certificate not found: certificate_id=%s",
                certificate_id,
            )
            return None

        logger.debug(
            "Certificate found: certificate_id=%s",
            certificate_id,
        )

        return certificate

    def get_certificates_by_device(
        self,
        device_id: int,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "Fetching certificates for device: device_id=%s",
            device_id,
        )

        certificates = self._repository.get_by_device_id(device_id)

        logger.debug(
            "Certificates fetched: device_id=%s count=%s",
            device_id,
            len(certificates),
        )

        return certificates

    def get_certificate_name(self, certificate_id: int) -> str | None:
        certificate = self.get_certificate(certificate_id)

        if not certificate:
            return None

        return (
            certificate.get("certificate_name")
            or certificate.get("name")
            or certificate.get("common_name")
        )

    def get_certificate_expiry(self, certificate_id: int) -> Any | None:
        certificate = self.get_certificate(certificate_id)

        if not certificate:
            return None

        return (
            certificate.get("expiry_date")
            or certificate.get("expiration_date")
            or certificate.get("not_after")
        )

    def get_certificate_issuer(self, certificate_id: int) -> str | None:
        certificate = self.get_certificate(certificate_id)

        if not certificate:
            return None

        return (
            certificate.get("issuer")
            or certificate.get("certificate_issuer")
        )

    def certificate_exists(self, certificate_id: int) -> bool:
        exists = self._repository.get_by_id(certificate_id) is not None

        logger.debug(
            "Certificate existence check: certificate_id=%s exists=%s",
            certificate_id,
            exists,
        )

        return exists