import unittest
from collections.abc import Sequence

from cohesity_automation import ApiClient, ApiError, AuthError, RateLimitError, TransportError
from tests.helpers import SETTINGS, FakeTransport, Response, fixture


def make(
    script: Sequence[Response | Exception], sleeps: list[float] | None = None
) -> tuple[ApiClient, FakeTransport, list[float]]:
    t = FakeTransport(script)
    s = sleeps if sleeps is not None else []
    return ApiClient(SETTINGS, t, sleep=s.append, jitter=lambda: 1.0), t, s


class ClientTests(unittest.TestCase):
    def test_pagination_follows_cursor(self) -> None:
        c, t, _ = make(
            [Response(200, fixture("jobs_page1.json")), Response(200, fixture("jobs_page2.json"))]
        )
        jobs = list(c.protection_jobs())
        self.assertEqual([j.name for j in jobs], ["job-alpha", "job-beta", "job-gamma"])
        self.assertIn("cursor=c2", t.urls[1])
        self.assertNotIn("cursor", t.urls[0])

    def test_cursor_loop_detected(self) -> None:
        page = {"items": [], "nextCursor": "x"}
        c, _, _ = make([Response(200, page)] * 3)
        with self.assertRaises(ApiError):
            list(c.paginate("/api/v1/jobs"))

    def test_retry_on_503_then_success(self) -> None:
        c, _, sleeps = make([Response(503, {"message": "busy"}), Response(200, {"ok": 1})])
        self.assertEqual(c.get("/x"), {"ok": 1})
        self.assertEqual(len(sleeps), 1)

    def test_backoff_grows(self) -> None:
        c, _, sleeps = make([Response(500, None)] * 3 + [Response(200, {})])
        c.get("/x")
        self.assertEqual(sleeps, [0.5, 1.0, 2.0])

    def test_retries_exhausted_raises(self) -> None:
        c, _, sleeps = make([Response(502, None)] * 4)
        with self.assertRaises(ApiError):
            c.get("/x")
        self.assertEqual(len(sleeps), 3)

    def test_rate_limit_honours_retry_after(self) -> None:
        c, _, sleeps = make([Response(429, {}, {"Retry-After": "7"}), Response(200, {})])
        c.get("/x")
        self.assertEqual(sleeps, [7.0])

    def test_auth_error_not_retried(self) -> None:
        c, t, _ = make([Response(401, {"message": "no"})])
        with self.assertRaises(AuthError):
            c.get("/x")
        self.assertEqual(len(t.urls), 1)

    def test_rate_limit_error_type(self) -> None:
        c, _, _ = make([Response(429, {})] * 4)
        with self.assertRaises(RateLimitError):
            c.get("/x")

    def test_transport_error_retried(self) -> None:
        c, _, sleeps = make([TransportError("reset"), Response(200, {"a": 1})])
        self.assertEqual(c.get("/x"), {"a": 1})
        self.assertEqual(len(sleeps), 1)

    def test_404_not_retried(self) -> None:
        c, t, _ = make([Response(404, {"message": "nope"})])
        with self.assertRaises(ApiError):
            c.get("/x")
        self.assertEqual(len(t.urls), 1)

    def test_malformed_item_rejected(self) -> None:
        c, _, _ = make([Response(200, {"items": [{"id": "1"}], "nextCursor": None})])
        with self.assertRaises(ApiError):
            list(c.protection_jobs())


if __name__ == "__main__":
    unittest.main()
