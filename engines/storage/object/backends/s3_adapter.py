from __future__ import annotations

import asyncio

from ..base import ObjectStorage


class S3Adapter(ObjectStorage):
    """Amazon S3 object storage backend using boto3 when installed."""

    def __init__(
        self,
        bucket_name: str,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        super().__init__()
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.endpoint_url = endpoint_url
        self._client = None

    async def connect(self) -> None:
        try:
            import boto3 #type [import-not-found]
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3Adapter.") from exc

        self._client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            endpoint_url=self.endpoint_url,
        )
        self._connected = True

    async def disconnect(self) -> None:
        self._client = None
        self._connected = False

    async def health(self) -> bool:
        return self._client is not None

    async def put(self, key: str, data: bytes, content_type: str | None = None) -> None:
        await self.ensure_connected()
        if self._client is None:
            raise RuntimeError("S3 client is not initialized.")

        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )

    async def get(self, key: str) -> bytes:
        await self.ensure_connected()
        if self._client is None:
            raise RuntimeError("S3 client is not initialized.")

        def _download() -> bytes:
            response = self._client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()

        return await asyncio.to_thread(_download)

    async def delete(self, key: str) -> None:
        await self.ensure_connected()
        if self._client is None:
            raise RuntimeError("S3 client is not initialized.")
        await asyncio.to_thread(self._client.delete_object, Bucket=self.bucket_name, Key=key)

    async def exists(self, key: str) -> bool:
        await self.ensure_connected()
        if self._client is None:
            return False

        def _exists() -> bool:
            try:
                self._client.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_exists)

    async def generate_url(self, key: str) -> str | None:
        if not await self.exists(key):
            return None
        if self._client is None:
            raise RuntimeError("S3 client is not initialized.")
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
        )
