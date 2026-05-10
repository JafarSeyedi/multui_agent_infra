import hashlib

from .base import BinaryPayload

class ChunkedBinaryPayload(BinaryPayload):
    chunks: list[BinaryPayload]
    merkle_root: str

    @staticmethod
    def compute_merkle_root(chunks: list[BinaryPayload]) -> str:
        hashes = [bytes.fromhex(c.sha256) for c in chunks]

        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])

            new = []
            for i in range(0, len(hashes), 2):
                h = hashlib.sha256(hashes[i] + hashes[i+1]).digest()
                new.append(h)

            hashes = new

        return hashes[0].hex()
