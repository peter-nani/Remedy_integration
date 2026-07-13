from __future__ import annotations

from logging import LoggerAdapter
from typing import Any, Callable

from slsdk.core.exceptions import DatabaseError
from slsdk.database.connection import SL1DatabaseConnection


CursorFactory = Callable[..., Any]


class SL1DatabaseFactory:
    def __init__(
        self,
        cursor_factory: CursorFactory,
        logger: LoggerAdapter,
    ) -> None:
        self._cursor_factory = cursor_factory
        self._logger = logger

        self._logger.info(
            "SL1 database factory initialised"
        )

    def create(
        self,
        *,
        legacy: bool = True,
    ) -> SL1DatabaseConnection:
        self._logger.info(
            "Creating SL1 database connection",
            extra={
                "legacy_mode": legacy,
            },
        )

        try:
            cursor = self._cursor_factory(
                legacy=legacy,
            )

            connection = SL1DatabaseConnection(
                cursor=cursor,
                logger=self._logger,
            )

            self._logger.info(
                "SL1 database connection created successfully",
                extra={
                    "legacy_mode": legacy,
                },
            )

            return connection

        except DatabaseError:
            self._logger.exception(
                "SL1 database connection creation failed"
            )
            raise

        except Exception as error:
            self._logger.exception(
                "Unexpected error while creating SL1 database connection"
            )

            raise DatabaseError(
                "Unable to create SL1 database connection",
                details={
                    "error_type": type(error).__name__,
                    "legacy_mode": legacy,
                },
            ) from error