# engines/storage/timeseries/base.py
# metrics
# observability
# events timeline
# engines/storage/timeseries/base.py
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import Any

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
        fields: dict[str, Any],
        tags: dict[str, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def query(
        self,
        measurement: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        pass
