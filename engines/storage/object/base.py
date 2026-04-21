# PDF
# DOCX
# XLSX
# DWG
# images
# audio
# video

# engines/storage/object/base.py

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from engines.storage.base_storage import BaseStorage


class ObjectStorage(BaseStorage, ABC):
    """
    Binary object storage abstraction.
    """

    @abstractmethod
    async def put(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    async def get(self, key: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def generate_url(self, key: str) -> Optional[str]:
        """Optional signed URL"""
        pass

