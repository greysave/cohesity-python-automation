# cohesity-python-automation

> Unofficial portfolio project — not affiliated with Cohesity. See [NOTICE](NOTICE) and [PROVENANCE](PROVENANCE.md).

A small, dependency-free, fully typed Python toolkit showing how I structure automation
against a paginated REST API for data-protection platforms: retries, error taxonomy,
config handling, reporting and a CLI. The API contract is synthetic.

## Architecture

```
cli.py ──► reports.py ──► models.py
  │            ▲
  └──► client.py ──► transport.py (Protocol; urllib impl, fake in tests)
          │
   config.py / errors.py / logging_config.py
```

- **Transport protocol** – the client depends on an interface, so tests inject a scripted fake; no network, no monkeypatching.
- **Retry/backoff** – exponential backoff with jitter on 5xx (500/502/503/504), transport errors and 429; `Retry-After` honoured; 401/403/4xx fail fast. Sleep and jitter are injectable.
- **Pagination** – generator over `items`/`nextCursor` with cursor-loop detection.
- **Models** – frozen dataclasses that validate payload shape and raise `ApiError` rather than leaking `KeyError`.
- **Reports** – per-tenant aggregation and pricing, CSV (formula-injection safe) or JSON.

## Usage

```bash
export EXAMPLE_API_URL=https://api.example.test
export EXAMPLE_API_KEY=...            # never commit
pip install -e .
cohesity-report usage --rate 20 --format csv
cohesity-report jobs
```

Optional: `EXAMPLE_API_VERIFY_TLS`, `EXAMPLE_API_TIMEOUT`, `EXAMPLE_API_MAX_RETRIES`, `EXAMPLE_API_PAGE_SIZE`.

```python
from cohesity_automation import ApiClient, Settings

client = ApiClient(Settings.from_env())
for job in client.protection_jobs(active_only=True):
    print(job.name, job.policy)
```

## Development

```bash
PYTHONPATH=src python -m unittest discover -v
mypy src          # optional, strict config in pyproject.toml
ruff check .      # optional
```

Licensed under Apache-2.0.
