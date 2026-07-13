# slsdk/bootstrap/application.py

from __future__ import annotations

from typing import Any, Mapping

from slsdk.bootstrap.container import Container
from slsdk.config.settings import Settings
from slsdk.logging.logger import get_logger

logger = get_logger(__name__)


class Application:
    """Main SDK application entry point."""

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or Settings()
        self._container = Container(self._settings)

    def run_event_ticket_workflow(
        self,
        event_id: int,
        *,
        defaults: Mapping[str, Any] | None = None,
        overrides: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Starting SLSDK application: event_id=%s",
            event_id,
        )

        workflow = self._container.build_event_ticket_workflow()

        try:
            result = workflow.execute(
                event_id,
                defaults=defaults,
                overrides=overrides,
            )
        except Exception:
            logger.exception(
                "SLSDK application execution failed: event_id=%s",
                event_id,
            )
            raise

        logger.info(
            "SLSDK application execution completed: event_id=%s",
            event_id,
        )

        return result