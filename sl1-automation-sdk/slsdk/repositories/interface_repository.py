from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter

from slsdk.database.connection import DatabaseConnection
from slsdk.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class InterfaceRecord:
    interface_id: int
    device_id: int
    interface_name: str


@dataclass(frozen=True, slots=True)
class InterfaceTagRecord:
    interface_id: int
    tag_name: str
    tag_value: str


class InterfaceRepository(BaseRepository[InterfaceRecord]):
    def __init__(
        self,
        database: DatabaseConnection,
        logger: LoggerAdapter,
    ) -> None:
        super().__init__(
            database=database,
            logger=logger,
        )

    def get_interface(
        self,
        *,
        device_id: int,
        interface_id: int,
    ) -> InterfaceRecord | None:
        self._logger.debug(
            "Retrieving interface",
            extra={
                "device_id": device_id,
                "interface_id": interface_id,
            },
        )

        query = """
            SELECT
                if_id,
                did,
                ifname
            FROM master.interfaces
            WHERE did = %s
              AND if_id = %s
        """

        try:
            self._database.execute(
                query,
                (
                    device_id,
                    interface_id,
                ),
            )

            rows = self._database.fetchall()

            if not rows:
                self._logger.warning(
                    "Interface not found",
                    extra={
                        "device_id": device_id,
                        "interface_id": interface_id,
                    },
                )

                return None

            row = rows[0]

            interface = InterfaceRecord(
                interface_id=int(row[0]),
                device_id=int(row[1]),
                interface_name=str(row[2]),
            )

            self._logger.debug(
                "Interface retrieved successfully",
                extra={
                    "device_id": interface.device_id,
                    "interface_id": interface.interface_id,
                },
            )

            return interface

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve interface",
                error,
                details={
                    "device_id": device_id,
                    "interface_id": interface_id,
                },
            ) from error

    def get_interface_tags(
        self,
        interface_id: int,
    ) -> tuple[InterfaceTagRecord, ...]:
        self._logger.debug(
            "Retrieving interface tags",
            extra={
                "interface_id": interface_id,
            },
        )

        query = """
            SELECT
                interface_id,
                tag_name,
                tag_value
            FROM master.interface_tags
            WHERE interface_id = %s
        """

        try:
            self._database.execute(
                query,
                (interface_id,),
            )

            rows = self._database.fetchall()

            tags = tuple(
                InterfaceTagRecord(
                    interface_id=int(row[0]),
                    tag_name=str(row[1]),
                    tag_value=str(row[2]),
                )
                for row in rows
            )

            self._logger.debug(
                "Interface tags retrieved successfully",
                extra={
                    "interface_id": interface_id,
                    "tag_count": len(tags),
                },
            )

            return tags

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve interface tags",
                error,
                details={
                    "interface_id": interface_id,
                },
            ) from error

    def get_tag_value(
        self,
        *,
        interface_id: int,
        tag_name: str,
    ) -> str | None:
        self._logger.debug(
            "Retrieving interface tag value",
            extra={
                "interface_id": interface_id,
                "tag_name": tag_name,
            },
        )

        query = """
            SELECT tag_value
            FROM master.interface_tags
            WHERE interface_id = %s
              AND tag_name = %s
        """

        try:
            value = self._database.fetch_value(
                query,
                (
                    interface_id,
                    tag_name,
                ),
            )

            if value is None:
                self._logger.warning(
                    "Interface tag value not found",
                    extra={
                        "interface_id": interface_id,
                        "tag_name": tag_name,
                    },
                )

                return None

            self._logger.debug(
                "Interface tag value retrieved successfully",
                extra={
                    "interface_id": interface_id,
                    "tag_name": tag_name,
                },
            )

            return str(value).strip()

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve interface tag value",
                error,
                details={
                    "interface_id": interface_id,
                    "tag_name": tag_name,
                },
            ) from error