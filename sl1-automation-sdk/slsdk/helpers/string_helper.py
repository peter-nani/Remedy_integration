from __future__ import annotations

import html
import re
from logging import LoggerAdapter

from slsdk.core.exceptions import TransformationError


class StringHelper:
    def __init__(
        self,
        logger: LoggerAdapter,
    ) -> None:
        self._logger = logger

        self._logger.info(
            "String helper initialised"
        )

    def normalize(
        self,
        value: object,
    ) -> str:
        self._logger.debug(
            "Normalising string value"
        )

        try:
            if value is None:
                return ""

            return str(value).strip()

        except Exception as error:
            self._logger.exception(
                "Failed to normalise string value"
            )

            raise TransformationError(
                "Unable to normalise string value",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def truncate(
        self,
        value: object,
        max_length: int,
    ) -> str:
        self._logger.debug(
            "Truncating string value",
            extra={
                "max_length": max_length,
            },
        )

        if max_length < 0:
            raise TransformationError(
                "Maximum string length cannot be negative",
                details={
                    "max_length": max_length,
                },
            )

        normalized_value = self.normalize(value)

        if len(normalized_value) <= max_length:
            return normalized_value

        truncated_value = normalized_value[:max_length]

        self._logger.debug(
            "String value truncated successfully",
            extra={
                "original_length": len(normalized_value),
                "truncated_length": len(truncated_value),
            },
        )

        return truncated_value

    def remove_html(
        self,
        value: object,
    ) -> str:
        self._logger.debug(
            "Removing HTML from string value"
        )

        try:
            normalized_value = self.normalize(value)

            without_tags = re.sub(
                r"<[^>]+>",
                "",
                normalized_value,
            )

            cleaned_value = html.unescape(
                without_tags
            )

            self._logger.debug(
                "HTML removed successfully"
            )

            return cleaned_value.strip()

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to remove HTML from string value"
            )

            raise TransformationError(
                "Unable to remove HTML from string value",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def normalize_whitespace(
        self,
        value: object,
    ) -> str:
        self._logger.debug(
            "Normalising string whitespace"
        )

        try:
            normalized_value = self.normalize(value)

            cleaned_value = re.sub(
                r"\s+",
                " ",
                normalized_value,
            )

            return cleaned_value.strip()

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to normalise string whitespace"
            )

            raise TransformationError(
                "Unable to normalise string whitespace",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def remove_non_ascii(
        self,
        value: object,
    ) -> str:
        self._logger.debug(
            "Removing non-ASCII characters"
        )

        try:
            normalized_value = self.normalize(value)

            cleaned_value = normalized_value.encode(
                "ascii",
                errors="ignore",
            ).decode("ascii")

            return cleaned_value.strip()

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to remove non-ASCII characters"
            )

            raise TransformationError(
                "Unable to remove non-ASCII characters",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def safe_int(
        self,
        value: object,
        *,
        default: int | None = None,
    ) -> int | None:
        self._logger.debug(
            "Converting value to integer"
        )

        if value is None:
            return default

        normalized_value = self.normalize(value)

        if not normalized_value:
            return default

        try:
            return int(normalized_value)

        except (TypeError, ValueError):
            self._logger.warning(
                "Unable to convert value to integer"
            )

            return default

    def contains(
        self,
        value: object,
        search_value: str,
        *,
        case_sensitive: bool = False,
    ) -> bool:
        normalized_value = self.normalize(value)

        if case_sensitive:
            return search_value in normalized_value

        return (
            search_value.lower()
            in normalized_value.lower()
        )