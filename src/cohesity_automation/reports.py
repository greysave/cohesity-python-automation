"""Report generation: per-tenant usage (chargeback-style) and job inventory."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .models import ProtectionJob, StorageStat

TIB = 1024**4


@dataclass(frozen=True)
class UsageRow:
    tenant: str
    logical_tib: float
    stored_tib: float
    reduction: float
    cost: float


def usage_report(stats: Iterable[StorageStat], rate_per_tib: float) -> list[UsageRow]:
    """Aggregate by tenant and price stored capacity at ``rate_per_tib``."""
    logical: dict[str, int] = defaultdict(int)
    stored: dict[str, int] = defaultdict(int)
    for s in stats:
        logical[s.tenant] += s.logical_bytes
        stored[s.tenant] += s.stored_bytes
    rows = [
        UsageRow(
            tenant=t,
            logical_tib=round(logical[t] / TIB, 4),
            stored_tib=round(stored[t] / TIB, 4),
            reduction=round(logical[t] / stored[t], 2) if stored[t] else 0.0,
            cost=round(stored[t] / TIB * rate_per_tib, 2),
        )
        for t in logical
    ]
    return sorted(rows, key=lambda r: r.tenant)


def jobs_by_environment(jobs: Iterable[ProtectionJob]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for j in jobs:
        counts[j.environment] += 1
    return dict(sorted(counts.items()))


def to_csv(rows: Iterable[UsageRow]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["tenant", "logical_tib", "stored_tib", "reduction", "cost"])
    for r in rows:
        w.writerow([_safe(r.tenant), r.logical_tib, r.stored_tib, r.reduction, r.cost])
    return buf.getvalue()


def _safe(cell: str) -> str:
    """Neutralise spreadsheet formula injection."""
    return "'" + cell if cell[:1] in ("=", "+", "-", "@") else cell


def to_json(rows: Iterable[UsageRow]) -> str:
    return json.dumps([r.__dict__ for r in rows], indent=2)
