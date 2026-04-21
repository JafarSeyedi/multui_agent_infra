from __future__ import annotations

from .postgres_adapter import PostgresStorageAdapter


class MySQLStorageAdapter(PostgresStorageAdapter):
    """Async MySQL backend using the same SQLAlchemy flow as other SQL engines."""
