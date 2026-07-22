"""Application configuration.

Deliberately minimal for the scaffold. Real settings (DB URL, secrets) come from
the environment — never hard-coded, never committed. Data-residency constraints
(CLAUDE.md blocking question #3) mean the deployment target is operator-chosen,
so nothing here assumes a cloud or region.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Digital Coop Bank API"
    # Semantic version of the running service, not of the requirements baseline.
    version: str = "0.0.1"
    environment: str = os.environ.get("DCB_ENV", "development")
    # DB URL is read at runtime by the (not-yet-present) persistence layer.
    database_url: str = os.environ.get("DATABASE_URL", "")


def get_settings() -> Settings:
    return Settings()
