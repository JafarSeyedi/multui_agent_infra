# engines/consistency/tests/test_consistency_models.py
from engines.consistency.models.consistency_models import Transaction, IdempotencyRecord
from engines.consistency.models.parsers.consistency_parser import parse_idempotency_record
from engines.consistency.models.writers.consistency_writer import write_idempotency_record


def test_transaction():
    t = Transaction(txn_id="txn-1")
    assert t.status == "pending"


def test_idempotency_record():
    r = IdempotencyRecord(key="req-1", processed=True)
    assert r.processed is True


def test_idempotency_roundtrip():
    r = IdempotencyRecord(key="k", processed=True, result={"ok": True})
    data = write_idempotency_record(r)
    parsed = parse_idempotency_record(data)
    assert parsed.key == "k"
    assert parsed.processed is True
    assert parsed.result == {"ok": True}
