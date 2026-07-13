from __future__ import annotations

import re
from logging import LoggerAdapter

from slsdk.core.exceptions import TransformationError
from slsdk.helpers.string_helper import StringHelper


class MessageParser:
    def __init__(
        self,
        string_helper: StringHelper,
        logger: LoggerAdapter,
    ) -> None:
        self._string_helper = string_helper
        self._logger = logger

        self._logger.info(
            "Message parser initialised"
        )

    def extract_integer(
        self,
        message: object,
        pattern: str,
        *,
        group: int = 1,
        default: int | None = None,
    ) -> int | None:
        self._logger.debug(
            "Extracting integer from message"
        )

        try:
            value = self.extract_value(
                message=message,
                pattern=pattern,
                group=group,
            )

            if value is None:
                return default

            return self._string_helper.safe_int(
                value,
                default=default,
            )

        except TransformationError:
            raise

        except Exception as error:
            self._logger.exception(
                "Failed to extract integer from message"
            )

            raise TransformationError(
                "Unable to extract integer from message",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def extract_value(
        self,
        message: object,
        pattern: str,
        *,
        group: int = 1,
    ) -> str | None:
        self._logger.debug(
            "Extracting value from message"
        )

        try:
            normalized_message = (
                self._string_helper.normalize(
                    message
                )
            )

            match = re.search(
                pattern,
                normalized_message,
                flags=re.IGNORECASE,
            )

            if match is None:
                self._logger.debug(
                    "Message pattern not found"
                )

                return None

            try:
                value = match.group(group)

            except IndexError as error:
                raise TransformationError(
                    "Regex group does not exist",
                    details={
                        "group": group,
                        "pattern": pattern,
                    },
                ) from error

            return self._string_helper.normalize(
                value
            )

        except TransformationError:
            raise

        except re.error as error:
            self._logger.exception(
                "Invalid message parsing pattern"
            )

            raise TransformationError(
                "Invalid message parsing pattern",
                details={
                    "pattern": pattern,
                    "error_type": type(error).__name__,
                },
            ) from error

        except Exception as error:
            self._logger.exception(
                "Failed to extract value from message"
            )

            raise TransformationError(
                "Unable to extract value from message",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def extract_between(
        self,
        message: object,
        start_marker: str,
        end_marker: str,
    ) -> str | None:
        self._logger.debug(
            "Extracting message content between markers"
        )

        try:
            normalized_message = (
                self._string_helper.normalize(
                    message
                )
            )

            start_index = normalized_message.find(
                start_marker
            )

            if start_index < 0:
                return None

            start_index += len(
                start_marker
            )

            end_index = normalized_message.find(
                end_marker,
                start_index,
            )

            if end_index < 0:
                return None

            return self._string_helper.normalize(
                normalized_message[
                    start_index:end_index
                ]
            )

        except Exception as error:
            self._logger.exception(
                "Failed to extract message content between markers"
            )

            raise TransformationError(
                "Unable to extract message content between markers",
                details={
                    "error_type": type(error).__name__,
                },
            ) from error

    def extract_first_number(
        self,
        message: object,
        *,
        default: int | None = None,
    ) -> int | None:
        self._logger.debug(
            "Extracting first number from message"
        )

        return self.extract_integer(
            message=message,
            pattern=r"(-?\d+)",
            default=default,
        )

    def extract_percentage(
        self,
        message: object,
    ) -> int | None:
        self._logger.debug(
            "Extracting percentage from message"
        )

        return self.extract_integer(
            message=message,
            pattern=r"(-?\d+)\s*%",
        )

    def extract_ip_address(
        self,
        message: object,
    ) -> str | None:
        self._logger.debug(
            "Extracting IP address from message"
        )

        return self.extract_value(
            message=message,
            pattern=(
                r"\b("
                r"(?:\d{1,3}\.){3}"
                r"\d{1,3}"
                r")\b"
            ),
        )

    def contains_pattern(
        self,
        message: object,
        pattern: str,
    ) -> bool:
        self._logger.debug(
            "Checking message pattern"
        )

        try:
            normalized_message = (
                self._string_helper.normalize(
                    message
                )
            )

            return (
                re.search(
                    pattern,
                    normalized_message,
                    flags=re.IGNORECASE,
                )
                is not None
            )

        except re.error as error:
            self._logger.exception(
                "Invalid message search pattern"
            )

            raise TransformationError(
                "Invalid message search pattern",
                details={
                    "pattern": pattern,
                    "error_type": type(error).__name__,
                },
            ) from error