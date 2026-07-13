from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Credential:
    """
    Authentication and endpoint information required
    by an external integration.
    """

    endpoint: str
    username: str
    password: str

    def __repr__(self) -> str:
        return (
            "Credential("
            f"endpoint={self.endpoint!r}, "
            f"username={self.username!r}, "
            "password='***'"
            ")"
        )