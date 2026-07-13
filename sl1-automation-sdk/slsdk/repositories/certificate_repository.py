from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter

from slsdk.database.connection import DatabaseConnection
from slsdk.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class CertificateRecord:
    certificate_id: int
    device_id: int
    common_name: str
    issuer: str
    expiration_date: str


class CertificateRepository(BaseRepository[CertificateRecord]):
    def __init__(
        self,
        database: DatabaseConnection,
        logger: LoggerAdapter,
    ) -> None:
        super().__init__(
            database=database,
            logger=logger,
        )

    def get_certificate(
        self,
        certificate_id: int,
    ) -> CertificateRecord | None:
        self._logger.debug(
            "Retrieving certificate",
            extra={
                "certificate_id": certificate_id,
            },
        )

        query = """
            SELECT
                certificate_id,
                did,
                common_name,
                issuer,
                expiration_date
            FROM master.certificates
            WHERE certificate_id = %s
        """

        try:
            self._database.execute(
                query,
                (certificate_id,),
            )

            rows = self._database.fetchall()

            if not rows:
                self._logger.warning(
                    "Certificate not found",
                    extra={
                        "certificate_id": certificate_id,
                    },
                )

                return None

            row = rows[0]

            certificate = CertificateRecord(
                certificate_id=int(row[0]),
                device_id=int(row[1]),
                common_name=str(row[2]),
                issuer=str(row[3]),
                expiration_date=str(row[4]),
            )

            self._logger.debug(
                "Certificate retrieved successfully",
                extra={
                    "certificate_id": certificate.certificate_id,
                    "device_id": certificate.device_id,
                },
            )

            return certificate

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve certificate",
                error,
                details={
                    "certificate_id": certificate_id,
                },
            ) from error