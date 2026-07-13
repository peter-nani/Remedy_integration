from __future__ import annotations

from dataclasses import dataclass
from logging import LoggerAdapter

from slsdk.database.connection import DatabaseConnection
from slsdk.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class ComponentRecord:
    component_id: int
    device_id: int
    component_name: str
    distinguished_name: str


class ComponentRepository(BaseRepository[ComponentRecord]):
    def __init__(
        self,
        database: DatabaseConnection,
        logger: LoggerAdapter,
    ) -> None:
        super().__init__(
            database=database,
            logger=logger,
        )

    def get_component(
        self,
        component_id: int,
    ) -> ComponentRecord | None:
        self._logger.debug(
            "Retrieving component",
            extra={
                "component_id": component_id,
            },
        )

        query = """
            SELECT
                component_id,
                did,
                component_name,
                distinguished_name
            FROM master.component
            WHERE component_id = %s
        """

        try:
            self._database.execute(
                query,
                (component_id,),
            )

            rows = self._database.fetchall()

            if not rows:
                self._logger.warning(
                    "Component not found",
                    extra={
                        "component_id": component_id,
                    },
                )

                return None

            row = rows[0]

            component = ComponentRecord(
                component_id=int(row[0]),
                device_id=int(row[1]),
                component_name=str(row[2]),
                distinguished_name=str(row[3]),
            )

            self._logger.debug(
                "Component retrieved successfully",
                extra={
                    "component_id": component.component_id,
                    "device_id": component.device_id,
                },
            )

            return component

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve component",
                error,
                details={
                    "component_id": component_id,
                },
            ) from error

    def get_distinguished_name(
        self,
        component_id: int,
    ) -> str | None:
        self._logger.debug(
            "Retrieving component distinguished name",
            extra={
                "component_id": component_id,
            },
        )

        query = """
            SELECT distinguished_name
            FROM master.component
            WHERE component_id = %s
        """

        try:
            value = self._database.fetch_value(
                query,
                (component_id,),
            )

            if value is None:
                self._logger.warning(
                    "Component distinguished name not found",
                    extra={
                        "component_id": component_id,
                    },
                )

                return None

            distinguished_name = str(value).strip()

            self._logger.debug(
                "Component distinguished name retrieved successfully",
                extra={
                    "component_id": component_id,
                },
            )

            return distinguished_name

        except Exception as error:
            raise self._repository_error(
                "Failed to retrieve component distinguished name",
                error,
                details={
                    "component_id": component_id,
                },
            ) from error