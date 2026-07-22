"""Alembic environment — skeleton. No models bound yet.

The schema (from 04_technical_architecture.md's 59 entities) lands in a later
pass; when it does, set target_metadata to the SQLAlchemy Base.metadata here.
The chain MUST stay linear (ledger requirement).
"""
from alembic import context

target_metadata = None  # set when the ORM models exist


def run_migrations_offline() -> None:
    context.configure(url=context.config.get_main_option("sqlalchemy.url"),
                      target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Real online config is wired when models exist; scaffold is a no-op guard.
    run_migrations_offline()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
