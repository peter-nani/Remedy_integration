# slsdk/logging/logger.py

from __future__ import annotations

import logging
import sys


DEFAULT_LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] "
    "%(name)s - %(message)s"
)


def configure_logging(
    level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
) -> None:
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))

    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)