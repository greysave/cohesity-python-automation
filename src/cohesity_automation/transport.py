"""Pluggable HTTP transport so the client can be tested without a network."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from .errors import TransportError


@dataclass(frozen=True)
class Response:
    status: int
    body: Any
    headers: dict[str, str] = field(default_factory=dict)


class Transport(Protocol):
    def request(
        self, method: str, url: str, headers: dict[str, str], timeout: float
    ) -> Response: ...


class UrllibTransport:
    """Standard-library transport."""

    def __init__(self, verify_tls: bool = True) -> None:
        self._ctx = ssl.create_default_context()
        if not verify_tls:
            self._ctx.check_hostname = False
            self._ctx.verify_mode = ssl.CERT_NONE

    def request(self, method: str, url: str, headers: dict[str, str], timeout: float) -> Response:
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as resp:
                return Response(resp.status, _decode(resp.read()), dict(resp.headers))
        except urllib.error.HTTPError as exc:
            return Response(exc.code, _decode(exc.read()), dict(exc.headers))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransportError(str(exc)) from exc


def _decode(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", "replace")
