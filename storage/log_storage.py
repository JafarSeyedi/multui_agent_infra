from datetime import datetime
from typing import Dict, List
from .sql_storage import SQLStorage


class LogStorage:
    """Log persistence layer built on top of SQLStorage."""

    def __init__(self, sql_storage: SQLStorage):
        self.sql = sql_storage

    def log_agent_execution(self, agent_name: str, record: Dict):
        key = f"exec:{agent_name}:{record.get('timestamp', datetime.utcnow())}"
        self.sql.save(key, record)

    def list_agent_logs(self, agent_name: str) -> List[str]:
        return self.sql.list_keys(prefix=f"exec:{agent_name}")

    def log_event(self, event_type: str, payload: Dict):
        key = f"event:{event_type}:{datetime.utcnow().isoformat()}"
        self.sql.save(key, payload)

    def list_events(self, event_type: str = None) -> List[str]:
        prefix = f"event:{event_type}" if event_type else "event:"
        return self.sql.list_keys(prefix=prefix)

