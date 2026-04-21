from __future__ import annotations

from .postgres_adapter import PostgresStorageAdapter


class SQLServerStorageAdapter(PostgresStorageAdapter):
    """Async SQL Server backend using the same SQLAlchemy flow as other SQL engines."""
