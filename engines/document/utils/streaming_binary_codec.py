# engnes/document/utils/streaming_binary_codec.py

import hashlib  # رفع خطای مربوط به نام hashlib
from typing import Iterable, List # برای دقت بیشتر در تایپ‌هینت‌ها
from ..models.media_types import MediaType
from ..models.base import BinaryEncoding, BinaryPayload 
from .binary_codec import BinaryCodecAdvanced

class StreamingBinaryCodec:

    CHUNK_SIZE = 1024 * 1024   # 1MB chunks

    @staticmethod
    def chunk_file_to_payloads(
        path: str,
        media_type: MediaType,
        encoding: BinaryEncoding = BinaryEncoding.BASE64
    ):
        with open(path, "rb") as f:
            index = 0
            while True:
                block = f.read(StreamingBinaryCodec.CHUNK_SIZE)
                if not block:
                    break
                
                encoded = BinaryCodecAdvanced.encode(block, encoding)

                yield BinaryPayload(
                    media_type=media_type,
                    encoding=encoding,
                    data=encoded,
                    size_bytes=len(block),
                    sha256=hashlib.sha256(block).hexdigest(),
                    chunk_index=index,
                    total_chunks=-1
                )
                index += 1

    @staticmethod
    def payloads_to_file(payloads: list[BinaryPayload], output_path: str):
        ordered = sorted(payloads, key=lambda p: p.chunk_index)

        with open(output_path, "wb") as f:
            for p in ordered:
                chunk = BinaryCodecAdvanced.decode(p)
                f.write(chunk)
