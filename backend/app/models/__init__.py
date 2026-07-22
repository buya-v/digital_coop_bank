"""Entity ORM models, derived from 04_technical_architecture.md §2.

Each domain module defines its tables. check_models.py imports all of them so
Base.metadata is complete. Ledger-core tables (ledger.py) are structure-only —
no posting/balance/hold logic (held on the corrected ledger design).
"""
