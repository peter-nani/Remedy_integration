from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """
    Represents a single automation execution.

    The context provides common identifiers that can be shared across
    logging, statistics, workflows, API clients, and error handling.

    It contains execution metadata only and must not contain
    application-specific business logic.
    """

    execution_id: str
    event_id: str
    automation_name: str
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(
        cls,
        event_id: str,
        automation_name: str,
    ) -> "ExecutionContext":
        """
        Create a new execution context.

        A unique execution identifier is generated for every automation run.
        """

        return cls(
            execution_id=str(uuid4()),
            event_id=str(event_id),
            automation_name=automation_name,
        )