# main.py

from __future__ import annotations

import sys

from slsdk.bootstrap.application import Application
from slsdk.logging.logger import get_logger

logger = get_logger(__name__)


def main() -> int:
    if len(sys.argv) < 2:
        logger.error("Missing event ID argument")
        return 1

    try:
        event_id = int(sys.argv[1])
    except ValueError:
        logger.error(
            "Invalid event ID: value=%s",
            sys.argv[1],
        )
        return 1

    logger.info(
        "Starting SLSDK execution: event_id=%s",
        event_id,
    )

    application = Application()

    try:
        result = application.run_event_ticket_workflow(
            event_id=event_id,
        )
    except Exception:
        logger.exception(
            "SLSDK execution failed: event_id=%s",
            event_id,
        )
        return 1

    logger.info(
        "SLSDK execution completed successfully: "
        "event_id=%s result=%s",
        event_id,
        result,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())