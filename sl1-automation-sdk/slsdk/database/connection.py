from __future__ import annotations

from logging import LoggerAdapter
from typing import Any, Protocol, Sequence

from slsdk.core.exceptions import DatabaseError


class DatabaseCursor(Protocol):
    def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        ...

    def fetchall(self) -> list[Any]:
        ...

    def autofetch_value(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        ...


class DatabaseConnection(Protocol):
    def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        ...

    def fetchall(self) -> list[Any]:
        ...

    def fetch_value(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        ...


class SL1DatabaseConnection:
    def __init__(
        self,
        cursor: DatabaseCursor,
        logger: LoggerAdapter,
    ) -> None:
        self._cursor = cursor
        self._logger = logger

        self._logger.info(
            "SL1 database connection adapter initialised"
        )

    def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        self._logger.debug(
            "Executing SL1 database query"
        )

        try:
            result = self._cursor.execute(
                query,
                params,
            )

            self._logger.debug(
                "SL1 database query executed successfully"
            )

            return result

        except Exception as error:
            self._logger.exception(
                "SL1 database query execution failed"
            )

            raise DatabaseError(
                "Unable to execute SL1 database query",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def fetchall(self) -> list[Any]:
        self._logger.debug(
            "Fetching all SL1 database rows"
        )

        try:
            rows = self._cursor.fetchall()

            self._logger.debug(
                "SL1 database rows fetched successfully",
                extra={
                    "row_count": len(rows),
                },
            )

            return rows

        except Exception as error:
            self._logger.exception(
                "Failed to fetch SL1 database rows"
            )

            raise DatabaseError(
                "Unable to fetch SL1 database rows",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def fetch_value(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        self._logger.debug(
            "Fetching single SL1 database value"
        )

        try:
            value = self._cursor.autofetch_value(
                query,
                params,
            )

            self._logger.debug(
                "SL1 database value fetched successfully"
            )

            return value

        except Exception as error:
            self._logger.exception(
                "Failed to fetch SL1 database value"
            )

            raise DatabaseError(
                "Unable to fetch SL1 database value",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error