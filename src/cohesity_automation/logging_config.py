"""Logging setup with a redaction filter for credential-looking values."""

from __future__ import annotations

import logging
import re

_SECRET = re.compile(r"(?i)(api[-_ ]?key|token|authorization|password)(['\"]?\s*[:=]\s*)\S+")


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _SECRET.sub(r"\1\2***", record.getMessage())
        record.args = None
        return True


def configure_logging(verbose: bool = False) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.addFilter(RedactingFilter())
    root = logging.getLogger("cohesity_automation")
    root.handlers[:] = [handler]
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    root.propagate = False
