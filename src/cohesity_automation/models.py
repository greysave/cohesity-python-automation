"""Immutable domain models parsed defensively from API payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ApiError


def _req(raw: dict[str, Any], key: str, kind: type) -> Any:
    value = raw.get(key)
    if not isinstance(value, kind) or isinstance(value, bool) and kind is not bool:
        raise ApiError(200, f"field {key!r} missing or not {kind.__name__}")
    return value


@dataclass(frozen=True)
class ProtectionJob:
    id: str
    name: str
    environment: str
    active: bool
    policy: str

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> ProtectionJob:
        return cls(
            id=str(_req(raw, "id", str)),
            name=_req(raw, "name", str),
            environment=raw.get("environment", "unknown"),
            active=bool(raw.get("active", True)),
            policy=raw.get("policy", ""),
        )


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    kind: str

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> Source:
        return cls(str(_req(raw, "id", str)), _req(raw, "name", str), raw.get("kind", "unknown"))


@dataclass(frozen=True)
class StorageStat:
    tenant: str
    logical_bytes: int
    stored_bytes: int

    @property
    def reduction_ratio(self) -> float:
        return self.logical_bytes / self.stored_bytes if self.stored_bytes else 0.0

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> StorageStat:
        return cls(
            tenant=_req(raw, "tenant", str),
            logical_bytes=_req(raw, "logicalBytes", int),
            stored_bytes=_req(raw, "storedBytes", int),
        )
