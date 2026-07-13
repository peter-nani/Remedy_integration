from __future__ import annotations

from logging import LoggerAdapter
from typing import Generic, TypeVar

from slsdk.core.exceptions import DatabaseError, RepositoryError
from slsdk.database.connection import DatabaseConnection


T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(
        self,
        database: DatabaseConnection,
        logger: LoggerAdapter,
    ) -> None:
        self._database = database
        self._logger = logger

        self._logger.info(
            "Repository initialised",
            extra={
                "repository": self.__class__.__name__,
            },
        )

    def _repository_error(
        self,
        message: str,
        error: Exception,
        *,
        details: dict[str, object] | None = None,
    ) -> RepositoryError:
        error_details: dict[str, object] = {
            "repository": self.__class__.__name__,
            "error_type": type(error).__name__,
        }

        if details:
            error_details.update(details)

        self._logger.exception(
            message,
            extra={
                "repository": self.__class__.__name__,
            },
        )

        if isinstance(error, DatabaseError):
            error_details.update(error.details)

        return RepositoryError(
            message,
            details=error_details,
        )