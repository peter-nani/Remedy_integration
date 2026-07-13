from __future__ import annotations

from typing import Any


class SLSDKError(Exception):
    """
    Base exception for all known SL SDK failures.
    """

    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class ConfigurationError(SLSDKError):
    """
    Raised when application configuration is missing or invalid.
    """


class RuntimeEnvironmentError(SLSDKError):
    """
    Raised when the automation runtime environment is invalid.
    """


class ValidationError(SLSDKError):
    """
    Raised when input or domain data fails validation.
    """


class TransformationError(SLSDKError):
    """
    Raised when data transformation fails.
    """


class RepositoryError(SLSDKError):
    """
    Raised when repository data access fails.
    """

    retryable = True


class DatabaseError(RepositoryError):
    """
    Raised when database communication or execution fails.
    """


class IntegrationError(SLSDKError):
    """
    Base exception for external system integration failures.
    """

    retryable = True


class APIError(IntegrationError):
    """
    Raised when a REST or HTTP API operation fails.
    """


class SOAPError(IntegrationError):
    """
    Raised when a SOAP operation fails.
    """


class AuthenticationError(IntegrationError):
    """
    Raised when external system authentication fails.
    """

    retryable = False


class IntegrationTimeoutError(IntegrationError):
    """
    Raised when an external integration operation
    exceeds its allowed execution time.
    """


class TicketProviderError(IntegrationError):
    """
    Raised when a ticket provider operation fails.
    """


class WorkflowError(SLSDKError):
    """
    Raised when application workflow execution fails.
    """


class RuleError(SLSDKError):
    """
    Raised when business rule processing fails.
    """


class RetryExhaustedError(SLSDKError):
    """
    Raised when all configured retry attempts are exhausted.
    """

    retryable = False