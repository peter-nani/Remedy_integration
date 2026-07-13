from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    username: str | None = None
    password: str | None = None
    token: str | None = None