# ADR 0001 — Technology stack

**Status:** Proposed (product owner may override before feature code is built on it)
**Date:** 2026-07-22
**Context run:** first architecture pass, after the requirements baseline's Mongolia correction.

## Decision

The platform backend is:

| Layer | Choice | Version target |
|---|---|---|
| Language | Python | ≥ 3.11 (local dev machine is 3.9 — see Consequences) |
| API framework | FastAPI | latest |
| Database | PostgreSQL | 16 |
| ORM / query | SQLAlchemy 2.0 (typed) | — |
| Migrations | Alembic | — |
| Money type | integer minor units in `BIGINT` — never float/DECIMAL-as-float | — |
| Packaging | pyproject (PEP 621) | — |
| Container | Docker + docker-compose | — |
| CI | GitHub Actions | — |
| API contract | **spec-first OpenAPI 3.1**, checked in as the architecture-of-record | — |

## Why

This is a **decision, not a default**, and it is reversible — no feature code exists yet. The reasoning:

1. **The team already works in Python.** The requirements pipeline (`idea-lab/run_pipeline.py`) is Python. Lowest ramp, no new language to staff.
2. **Money correctness is the dominant non-functional requirement.** The ledger addendum mandates integer minor units, append-only double-entry, and `SERIALIZABLE` isolation. PostgreSQL provides serializable isolation and `BIGINT`; SQLAlchemy 2.0 gives typed, explicit column mapping so a money column is never accidentally a float. Alembic gives the **linear migration chain** the ledger design requires (migrations must not branch).
3. **Data residency (`CLAUDE.md` blocking question #3).** The MDDIC Information Security Requirement may force servers physically in Mongolia. Every element here is **self-hostable** — FastAPI, Postgres and Docker run on a Mongolian VM or on-prem with no US-cloud lock-in. A serverless/managed-only stack was rejected for exactly this reason.
4. **OpenAPI alignment.** `04_technical_architecture.md` describes ~192 endpoints as key-names only. Producing a real OpenAPI 3.1 spec from them is the point of this phase; FastAPI is OpenAPI-native, so the eventual implementation and the contract stay coupled.

## Alternative considered

**TypeScript + NestJS + PostgreSQL.** Stronger structural typing than Python and a first-class DI/module system. Rejected as the primary because it adds a language the current team does not use, for a benefit (typing) that SQLAlchemy 2.0 + Pydantic substantially close for the money-correctness surface that matters here. Worth revisiting if a TS frontend team ends up owning the backend too.

## Consequences

- **Spec-first, not code-first.** The OpenAPI spec is authored (derived from `04`) and is the source of truth; the FastAPI app is validated against it. This keeps the contract independent of any one implementation.
- **Local dev machine is Python 3.9 and has no Docker.** The project targets ≥ 3.11 and containerised Postgres. On this machine, non-DB unit tests (e.g. the money module) run directly; the full stack needs a newer Python and Docker, or CI. This is a machine gap, not a stack choice — recorded so no one mistakes a local "can't boot Postgres" for a design problem.
- **Currency is MNT.** The product owner confirmed MNT (ISO 4217 numeric 496, 2 minor units, transacted as whole tugrik). The money module encodes this now; the requirements documents still say USD pending the currency **apply** run — a known, tracked lag, not a contradiction.
- The `coder` / `test_writer` softhouse roles, marked inactive while there was no application, **activate** with this scaffold. `CLAUDE.md`'s "no application code" clause is updated accordingly.

## Not decided here

Frontend stack, mobile stack, the identity/eKYC integration (ХУР vs biometric — a blocking legal question), the payment-rail integration surface, and hosting/region — all downstream of the entity and legal decisions still open in `CLAUDE.md`.
