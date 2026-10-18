import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cohesity_automation.config import Settings
from cohesity_automation.errors import TransportError
from cohesity_automation.transport import Response

FIX = Path(__file__).parent / "fixtures"


def fixture(name: str) -> Any:
    return json.loads((FIX / name).read_text())


SETTINGS = Settings(base_url="https://api.example.test", api_key="dummy-key", max_retries=3)


class FakeTransport:
    """Replays a scripted list of Response or Exception objects."""

    def __init__(self, script: Sequence[Response | Exception]) -> None:
        self.script = list(script)
        self.urls: list[str] = []

    def request(self, method: str, url: str, headers: dict[str, str], timeout: float) -> Response:
        self.urls.append(url)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


__all__ = ["SETTINGS", "FakeTransport", "Response", "TransportError", "fixture"]
