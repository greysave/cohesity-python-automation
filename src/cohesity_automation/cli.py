"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from .client import ApiClient
from .config import Settings
from .errors import AutomationError
from .logging_config import configure_logging
from .reports import jobs_by_environment, to_csv, to_json, usage_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cohesity-report", description=__doc__)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    u = sub.add_parser("usage", help="per-tenant storage usage and cost")
    u.add_argument("--rate", type=float, default=20.0, help="cost per stored TiB")
    u.add_argument("--format", choices=["csv", "json"], default="csv")
    sub.add_parser("jobs", help="job counts by environment")
    return p


def main(argv: Sequence[str] | None = None, client: ApiClient | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    try:
        client = client or ApiClient(Settings.from_env())
        if args.command == "usage":
            rows = usage_report(client.storage_stats(), args.rate)
            sys.stdout.write(to_csv(rows) if args.format == "csv" else to_json(rows) + "\n")
        else:
            for env, n in jobs_by_environment(client.protection_jobs()).items():
                sys.stdout.write(f"{env}\t{n}\n")
    except AutomationError as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
