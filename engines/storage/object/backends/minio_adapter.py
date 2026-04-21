from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING

from ..base import ObjectStorage

if TYPE_CHECKING:
    from minio import Minio


class MinioAdapter(ObjectStorage):
    """MinIO object storage backend using the official client when installed."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
    ) -> None:
        super().__init__()

        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure

        self._client: Optional["Minio"] = None

    async def connect(self) -> None:
        try:
            from minio import Minio
        except ImportError as exc:
            raise RuntimeError(
                "minio package is required for MinioAdapter."
            ) from exc

        self._client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

        client = self._client

        def _ensure_bucket() -> None:
            assert client is not None
            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)

        await asyncio.to_thread(_ensure_bucket)

        self._connected = True

    async def disconnect(self) -> None:
        self._client = None
        self._connected = False

    async def health(self) -> bool:
        return self._client is not None

    async def put(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        await self.ensure_connected()
        client = self._client
        assert client is not None

        def _upload() -> None:
            from io import BytesIO

            client.put_object(
                self.bucket_name,
                key,
                BytesIO(data),
                length=len(data),
                content_type=content_type or "application/octet-stream",
            )

        await asyncio.to_thread(_upload)

    async def get(self, key: str) -> bytes:
        await self.ensure_connected()
        client = self._client
        assert client is not None

        def _download() -> bytes:
            response = client.get_object(self.bucket_name, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        return await asyncio.to_thread(_download)

    async def delete(self, key: str) -> None:
        await self.ensure_connected()
        client = self._client
        assert client is not None

        await asyncio.to_thread(
            client.remove_object,
            self.bucket_name,
            key,
        )

    async def exists(self, key: str) -> bool:
        await self.ensure_connected()
        client = self._client
        assert client is not None

        def _exists() -> bool:
            try:
                client.stat_object(self.bucket_name, key)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_exists)

    async def generate_url(self, key: str) -> Optional[str]:
        await self.ensure_connected()
        client = self._client
        assert client is not None

        if not await self.exists(key):
            return None

        return await asyncio.to_thread(
            client.presigned_get_object,
            self.bucket_name,
            key,
        )
