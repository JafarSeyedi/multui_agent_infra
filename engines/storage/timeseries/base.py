# engines/storage/timeseries/base.py

# metrics
# observability
# events timeline

# engines/storage/timeseries/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime
from engines.storage.base_storage import BaseStorage


class TimeSeriesStorage(BaseStorage, ABC):
    """
    Time-series storage abstraction.
    """

    @abstractmethod
    async def write(
        self,
        measurement: str,
        timestamp: datetime,
        fields: Dict[str, Any],
        tags: Dict[str, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def query(
        self,
        measurement: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        pass
