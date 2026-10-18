import contextlib
import io
import logging
import unittest

from cohesity_automation import ApiClient
from cohesity_automation.cli import main
from cohesity_automation.logging_config import RedactingFilter
from cohesity_automation.models import StorageStat
from cohesity_automation.reports import to_csv, usage_report
from tests.helpers import SETTINGS, FakeTransport, Response, fixture

TIB = 1024**4


class ReportTests(unittest.TestCase):
    def test_usage_aggregation(self) -> None:
        rows = usage_report([StorageStat("a", 4 * TIB, TIB), StorageStat("a", 0, TIB)], 10.0)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].stored_tib, rows[0].cost, rows[0].reduction), (2.0, 20.0, 2.0))

    def test_csv_injection_neutralised(self) -> None:
        out = to_csv(usage_report([StorageStat("=cmd", TIB, TIB)], 1.0))
        self.assertIn("'=cmd", out)

    def test_zero_stored(self) -> None:
        self.assertEqual(StorageStat("t", 5, 0).reduction_ratio, 0.0)

    def test_redaction(self) -> None:
        rec = logging.LogRecord("n", 20, "p", 1, "api_key=abc123 ok", None, None)
        RedactingFilter().filter(rec)
        self.assertNotIn("abc123", rec.msg)


class CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str], script: list[Response | Exception]) -> tuple[int, str]:
        client = ApiClient(SETTINGS, FakeTransport(script), sleep=lambda s: None)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(argv, client)
        return rc, out.getvalue()

    def test_usage_csv(self) -> None:
        rc, out = self.run_cli(["usage", "--rate", "10"], [Response(200, fixture("stats.json"))])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("tenant,logical_tib"))
        self.assertIn("tenant-a,2.0,0.5,4.0,5.0", out)

    def test_jobs(self) -> None:
        rc, out = self.run_cli(
            ["jobs"],
            [Response(200, fixture("jobs_page1.json")), Response(200, fixture("jobs_page2.json"))],
        )
        self.assertEqual((rc, out), (0, "nas\t1\nvm\t2\n"))

    def test_error_returns_1(self) -> None:
        rc, _ = self.run_cli(["jobs"], [Response(401, {"message": "denied"})])
        self.assertEqual(rc, 1)

    def test_missing_config_returns_1(self) -> None:
        import os

        old = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("EXAMPLE_API_")}
        try:
            self.assertEqual(main(["jobs"]), 1)
        finally:
            os.environ.update(old)
