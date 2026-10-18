"""Typed REST client with retry/backoff and cursor pagination."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import urlencode

from .config import Settings
from .errors import ApiError, AuthError, RateLimitError, TransportError
from .models import ProtectionJob, Source, StorageStat
from .transport import Response, Transport, UrllibTransport

log = logging.getLogger(__name__)

_RETRY_STATUS = {500, 502, 503, 504}


class ApiClient:
    """Small client for a hypothetical ``/api/v1`` REST service.

    Pagination contract (synthetic): list endpoints accept ``limit`` and ``cursor``
    and return ``{"items": [...], "nextCursor": str | null}``.
    """

    def __init__(
        self,
        settings: Settings,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        self._s = settings
        self._transport = transport or UrllibTransport(settings.verify_tls)
        self._sleep = sleep
        self._jitter = jitter

    # -- low level -------------------------------------------------------
    def _delay(self, attempt: int, retry_after: float | None) -> float:
        if retry_after is not None:
            return retry_after
        return float(self._s.backoff_base * (2**attempt) * (0.5 + self._jitter() / 2))

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{self._s.base_url}{path}" + (f"?{urlencode(query)}" if query else "")
        headers = {"Authorization": f"Bearer {self._s.api_key}", "Accept": "application/json"}
        for attempt in range(self._s.max_retries + 1):
            retry_after: float | None = None
            try:
                resp = self._transport.request("GET", url, headers, self._s.timeout)
                self._raise_for_status(resp)
                return resp.body
            except RateLimitError as exc:
                err: Exception = exc
                retry_after = exc.retry_after
            except ApiError as exc:
                if exc.status not in _RETRY_STATUS:
                    raise
                err = exc
            except TransportError as exc:
                err = exc
            if attempt >= self._s.max_retries:
                raise err
            delay = self._delay(attempt, retry_after)
            log.warning("retrying %s (attempt %d) in %.2fs: %s", path, attempt + 1, delay, err)
            self._sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def _raise_for_status(resp: Response) -> None:
        if 200 <= resp.status < 300:
            return
        msg = resp.body.get("message", "") if isinstance(resp.body, dict) else str(resp.body or "")
        if resp.status in (401, 403):
            raise AuthError(resp.status, msg)
        if resp.status == 429:
            raw = {k.lower(): v for k, v in resp.headers.items()}.get("retry-after")
            try:
                after = float(raw) if raw is not None else None
            except ValueError:
                after = None
            raise RateLimitError(resp.status, msg, after)
        raise ApiError(resp.status, msg)

    # -- pagination ------------------------------------------------------
    def paginate(self, path: str, params: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        seen: set[str] = set()
        while True:
            page = self.get(path, {**(params or {}), "limit": self._s.page_size, "cursor": cursor})
            if not isinstance(page, dict) or "items" not in page:
                raise ApiError(200, f"unexpected page shape from {path}")
            yield from page["items"]
            cursor = page.get("nextCursor")
            if not cursor:
                return
            if cursor in seen:
                raise ApiError(200, f"cursor loop detected on {path}")
            seen.add(cursor)

    # -- typed resources -------------------------------------------------
    def protection_jobs(self, active_only: bool = False) -> Iterator[ProtectionJob]:
        for raw in self.paginate("/api/v1/jobs", {"active": "true" if active_only else None}):
            yield ProtectionJob.from_api(raw)

    def sources(self) -> Iterator[Source]:
        for raw in self.paginate("/api/v1/sources"):
            yield Source.from_api(raw)

    def storage_stats(self) -> Iterator[StorageStat]:
        for raw in self.paginate("/api/v1/storage-stats"):
            yield StorageStat.from_api(raw)
