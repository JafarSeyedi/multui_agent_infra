from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import TimeSeriesStorage


class InfluxDBStorageAdapter(TimeSeriesStorage):
    """InfluxDB time-series backend using the official client when installed."""

    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        super().__init__()

        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket

        self._client: Optional[Any] = None
        self._write_api: Optional[Any] = None
        self._query_api: Optional[Any] = None

    async def connect(self) -> None:
        try:
            from influxdb_client import InfluxDBClient
        except ImportError as exc:
            raise RuntimeError(
                "influxdb-client is required for InfluxDBStorageAdapter."
            ) from exc

        self._client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
        )

        self._write_api = self._client.write_api()
        self._query_api = self._client.query_api()

        self._connected = True

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()

        self._client = None
        self._write_api = None
        self._query_api = None
        self._connected = False

    async def health(self) -> bool:
        return self._client is not None

    async def write(
        self,
        measurement: str,
        timestamp: datetime,
        fields: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
    ) -> None:

        if self._client is None:
            await self.connect()

        assert self._write_api is not None

        from influxdb_client import Point, WritePrecision

        point = Point(measurement).time(timestamp, WritePrecision.NS)

        for key, value in (tags or {}).items():
            point = point.tag(key, value)

        for key, value in fields.items():
            point = point.field(key, value)

        self._write_api.write(
            bucket=self.bucket,
            org=self.org,
            record=point,
        )

    async def query(
        self,
        measurement: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:

        if self._query_api is None:
            await self.connect()

        assert self._query_api is not None

        flux = (
            f'from(bucket: "{self.bucket}") '
            f'|> range(start: {start.isoformat()}, stop: {end.isoformat()}) '
            f'|> filter(fn: (r) => r._measurement == "{measurement}")'
        )

        tables = self._query_api.query(flux, org=self.org)

        rows: List[Dict[str, Any]] = []

        for table in tables:
            for record in table.records:
                rows.append(record.values)

        return rows
