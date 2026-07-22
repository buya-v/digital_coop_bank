# Digital Coop Bank — backend

Scaffold for the platform API. **No feature endpoints exist yet** — see
`../docs/adr/0001-technology-stack.md` for the stack decision and scope.

Stack: Python ≥ 3.11 · FastAPI · PostgreSQL 16 · SQLAlchemy 2.0 · Alembic.
Money is **integer minor units, MNT** (`app/money.py`) — the project's core
non-negotiable, encoded in code and unit-tested.

## What's here

```
app/
  main.py     FastAPI app — /health and /ready only
  config.py   env-driven settings (no secrets committed)
  money.py    Money as integer minor units; no float path (the non-negotiable)
tests/
  test_money.py    runs with no DB / no framework (Python 3.9+)
  test_health.py   needs fastapi+httpx (CI installs them)
migrations/   Alembic skeleton — LINEAR chain only (ledger requirement); no models bound yet
```

## Run the tests

```bash
cd backend
pip install -e ".[dev]"
pytest -q
```

The money tests need nothing installed and run on the dev machine's Python 3.9;
the health tests need FastAPI. CI runs the full suite on Python 3.12 with Postgres.

## Not yet built

The OpenAPI contract (from the 138 endpoint rows in
`../idea-lab/final_requirements/04_technical_architecture.md`), the ORM schema
(from its 59 entities), and every feature router. These land in later passes,
per-epic, and only where the entity/legal questions in `../CLAUDE.md` are
resolved. Cards, Round-Ups and Lending are entity-gated and must not be built
until that decision is made.

## Local limits

The dev machine has Python 3.9 and no Docker, so the full DB stack (`docker
compose up`) runs in CI or on a newer local setup, not here. The money module
and any non-DB logic are locally verifiable.
