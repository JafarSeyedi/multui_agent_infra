# engines/persistence/tests/test_persistence_models.py
from engines.persistence.models.persistence_models import VectorRecord, BlobRecord
from engines.persistence.models.parsers.vector_persistence_parser import parse_vector_record
from engines.persistence.models.writers.vector_persistence_writer import write_vector_record


def test_vector_record():
    rec = VectorRecord(collection="docs", id="1", vector=[1.0, 0.0])
    assert rec.collection == "docs"


def test_vector_roundtrip():
    rec = VectorRecord(collection="c", id="i", vector=[1.0, 2.0], metadata={"key": "val"})
    data = write_vector_record(rec)
    parsed = parse_vector_record(data)
    assert parsed.vector == [1.0, 2.0]
    assert parsed.metadata["key"] == "val"


def test_blob_record():
    rec = BlobRecord(path="/tmp/test.bin", data=b"hello")
    assert rec.path == "/tmp/test.bin"
