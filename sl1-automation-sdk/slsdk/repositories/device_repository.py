from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter

from slsdk.database.connection import DatabaseConnection
from slsdk.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class DeviceRecord:
    device_id: int
    device_name: str
    ip_address: str


class DeviceRepository(BaseRepository[DeviceRecord]):
    def __init__(
        self,
        database: DatabaseConnection,
        logger: LoggerAdapter,
    ) -> None:
        super().__init__(
            database=database,
            logger=logger,
        )

    def get_device_ip(
        self,
        device_id: int,
    ) -> str | None:
        self._logger.debug(
            "Retrieving device IP address",
            extra={
                "device_id": device_id,
            },
        )

        query = """
            SELECT ip
            FROM master.system_devices
            WHERE did = %s
        """

        try:
            value = self._database.fetch_value(
                query,
                (device_id,),
            )

            if value is None:
                self._logger.warning(
                    "Device IP address not found",
                    extra={
                        "device_id": device_id,
                    },
                )

                return None

            ip_address = str(value).strip()

            self._logger.debug(
                "Device IP address retrieved successfully",
                extra={
                    "device_id": device_id,
                },
            )

            return ip_address

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve device IP address",
                error,
                details={
                    "device_id": device_id,
                },
            ) from error

    def get_device(
        self,
        device_id: int,
    ) -> DeviceRecord | None:
        self._logger.debug(
            "Retrieving device",
            extra={
                "device_id": device_id,
            },
        )

        query = """
            SELECT
                did,
                device,
                ip
            FROM master.system_devices
            WHERE did = %s
        """

        try:
            self._database.execute(
                query,
                (device_id,),
            )

            rows = self._database.fetchall()

            if not rows:
                self._logger.warning(
                    "Device not found",
                    extra={
                        "device_id": device_id,
                    },
                )

                return None

            row = rows[0]

            device = DeviceRecord(
                device_id=int(row[0]),
                device_name=str(row[1]),
                ip_address=str(row[2]),
            )

            self._logger.debug(
                "Device retrieved successfully",
                extra={
                    "device_id": device.device_id,
                },
            )

            return device

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve device",
                error,
                details={
                    "device_id": device_id,
                },
            ) from error