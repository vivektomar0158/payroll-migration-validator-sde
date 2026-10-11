# Payroll Data Migration Validator — backend service (SDE edition)

**9/9 tests passing (validators, sync API, async job + auth paths); processes a 385-row legacy / 372-row target reconciliation as a background job returning 202 immediately, with auth enforced via `X-API-Key` and results persisted to Postgres instead of held in memory.**

Copied from the Data Analyst version (same validators: duplicates, missing fields, totals reconciliation) and wrapped as a standalone backend microservice.

Reconciles a legacy payroll export against a target export and reports duplicates, missing required fields, and mismatched totals.

## What's new in this edition

- **API-key auth** (`app/auth.py`) — set `MIGRATION_VALIDATOR_API_KEY` and every endpoint requires an `X-API-Key` header; unset, it's a no-op so the service still runs out of the box for local dev.
- **Async job model** (`app/db.py`, `POST /jobs` → 202 + job id → `GET /jobs/{id}`) alongside the original synchronous `/validate`.
- **Postgres persistence** for jobs via SQLAlchemy (`DATABASE_URL`, defaults to local SQLite; docker-compose wires up real Postgres).
- **Structured JSON logging** (`app/logging_config.py`).
- **Dockerfile + docker-compose.yml** (api + Postgres) and a GitHub Actions CI workflow (`.github/workflows/ci.yml`).

## Run

```
docker compose up --build
# or locally:
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Use

```
curl -F "legacy=@data/payroll_legacy.csv" -F "target=@data/payroll_target.csv" http://127.0.0.1:8000/validate
# -> {"report_id": "...", "duplicate_count": N, "missing_field_count": N, "mismatch_count": N, ...}

curl http://127.0.0.1:8000/report/<report_id>.html -o report.html
curl http://127.0.0.1:8000/report/<report_id>.csv  -o report.csv
curl http://127.0.0.1:8000/report/<report_id>.xlsx -o report.xlsx

# async path
curl -F "legacy=@data/payroll_legacy.csv" -F "target=@data/payroll_target.csv" http://127.0.0.1:8000/jobs
# -> {"job_id": "...", "status": "QUEUED"}
curl http://127.0.0.1:8000/jobs/<job_id>
```

Add `-H "X-API-Key: <key>"` to every call once `MIGRATION_VALIDATOR_API_KEY` is set.

## Tests

`pytest tests/ -q` — unit tests per validator rule (`app/validators/`), an API integration test (`tests/test_api.py`), and job/auth tests (`tests/test_jobs.py`).

## Seed data

`data/payroll_legacy.csv` / `data/payroll_target.csv` are copied from the Analytics Dashboard project's generator, with deliberately seeded issues: duplicate legacy rows, blank `bank_account` fields after migration, and `net_pay` drift between legacy and target.
