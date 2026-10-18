"""Environment-driven configuration. Secrets are never logged or repr'd."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from .errors import ConfigError

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def _bool(name: str, raw: str) -> bool:
    low = raw.strip().lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    raise ConfigError(f"{name} must be a boolean, got {raw!r}")


def _num(name: str, raw: str, cast: type[int | float]) -> float:
    try:
        value = cast(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from None
    if value < 0:
        raise ConfigError(f"{name} must be non-negative")
    return float(value)


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str = field(repr=False)
    verify_tls: bool = True
    timeout: float = 30.0
    max_retries: int = 4
    backoff_base: float = 0.5
    page_size: int = 100

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Build settings from ``EXAMPLE_API_*`` variables."""
        env = os.environ if env is None else env
        base = env.get("EXAMPLE_API_URL", "").strip().rstrip("/")
        key = env.get("EXAMPLE_API_KEY", "")
        if not base or not key:
            raise ConfigError("EXAMPLE_API_URL and EXAMPLE_API_KEY are required")
        if not base.startswith(("https://", "http://")):
            raise ConfigError("EXAMPLE_API_URL must start with http:// or https://")
        kw: dict[str, object] = {}
        if "EXAMPLE_API_VERIFY_TLS" in env:
            kw["verify_tls"] = _bool("EXAMPLE_API_VERIFY_TLS", env["EXAMPLE_API_VERIFY_TLS"])
        if "EXAMPLE_API_TIMEOUT" in env:
            kw["timeout"] = _num("EXAMPLE_API_TIMEOUT", env["EXAMPLE_API_TIMEOUT"], float)
        if "EXAMPLE_API_MAX_RETRIES" in env:
            raw = env["EXAMPLE_API_MAX_RETRIES"]
            kw["max_retries"] = int(_num("EXAMPLE_API_MAX_RETRIES", raw, int))
        if "EXAMPLE_API_PAGE_SIZE" in env:
            size = int(_num("EXAMPLE_API_PAGE_SIZE", env["EXAMPLE_API_PAGE_SIZE"], int))
            if size < 1:
                raise ConfigError("EXAMPLE_API_PAGE_SIZE must be >= 1")
            kw["page_size"] = size
        return cls(base_url=base, api_key=key, **kw)  # type: ignore[arg-type]
