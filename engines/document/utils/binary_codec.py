# engnes/document/utils/binary_codec.py

import base64
import hashlib
# import zlib
# import gzip
# import brotli  # type: ignore[import-untyped]
from typing import Optional
from engines.document.models.media_types import MediaType
from engines.document.models.base import BinaryPayload, BinaryEncoding

class BinaryCodec:

    DEFAULT_TEXT_ENCODING = "utf-8"

    @staticmethod
    def from_bytes(data: bytes, media_type: MediaType, text_encoding: Optional[str] = None) -> BinaryPayload:

        encoding = text_encoding or BinaryCodec.DEFAULT_TEXT_ENCODING
        
        data_b64 = base64.b64encode(data).decode(encoding)

        return BinaryPayload(
            media_type=media_type,
            encoding=BinaryEncoding.BASE64,
            data=data_b64,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )

    @staticmethod
    def to_bytes(payload: BinaryPayload, text_encoding: Optional[str] = None) -> bytes:

        encoding = text_encoding or BinaryCodec.DEFAULT_TEXT_ENCODING
        return base64.b64decode(payload.data.encode(encoding))

class BinaryCodecAdvanced:

    DEFAULT_TEXT_ENCODING = "utf-8"

    @staticmethod
    def encode(data: bytes, encoding: BinaryEncoding, text_encoding: Optional[str] = None) -> str:
        enc = text_encoding or BinaryCodecAdvanced.DEFAULT_TEXT_ENCODING

        if encoding == BinaryEncoding.BASE64:
            return base64.b64encode(data).decode(enc)

        if encoding == BinaryEncoding.BASE32:
            return base64.b32encode(data).decode(enc)

        if encoding == BinaryEncoding.BASE16:
            return base64.b16encode(data).decode(enc)

        if encoding == BinaryEncoding.RAW:
            return data.hex()

        # if encoding == BinaryEncoding.GZIP_BASE64:
        #     comp = gzip.compress(data)
        #     return base64.b64encode(comp).decode(enc)

        # if encoding == BinaryEncoding.ZLIB_BASE64:
        #     comp = zlib.compress(data)
        #     return base64.b64encode(comp).decode(enc)

        # if encoding == BinaryEncoding.BROTLI_BASE64:
        #     comp = brotli.compress(data)
        #     return base64.b64encode(comp).decode(enc)

        raise ValueError(f"Unsupported encoding: {encoding}")

    @staticmethod
    def decode(payload: BinaryPayload, text_encoding: Optional[str] = None) -> bytes:
        enc = text_encoding or BinaryCodecAdvanced.DEFAULT_TEXT_ENCODING
        data = payload.data

        if payload.encoding == BinaryEncoding.BASE64:
            return base64.b64decode(data.encode(enc))

        if payload.encoding == BinaryEncoding.BASE32:
            return base64.b32decode(data.encode(enc))

        if payload.encoding == BinaryEncoding.BASE16:
            return base64.b16decode(data.encode(enc))

        if payload.encoding == BinaryEncoding.RAW:
            return bytes.fromhex(data)

        # if payload.encoding == BinaryEncoding.GZIP_BASE64:
        #     comp = base64.b64decode(data.encode(enc))
        #     return gzip.decompress(comp)

        # if payload.encoding == BinaryEncoding.ZLIB_BASE64:
        #     comp = base64.b64decode(data.encode(enc))
        #     return zlib.decompress(comp)

        # if payload.encoding == BinaryEncoding.BROTLI_BASE64:
        #     comp = base64.b64decode(data.encode(enc))
        #     return brotli.decompress(comp)

        raise ValueError(f"Unsupported encoding: {payload.encoding}")
