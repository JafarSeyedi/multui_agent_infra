# engines/consistency/tests/test_consistency_backends.py
import pytest
from engines.consistency.backends.in_memory.in_memory_consistency import (
    InMemoryTransactionManager,
    InMemoryIdempotencyChecker,
)


@pytest.mark.asyncio
async def test_transaction_begin_commit():
    mgr = InMemoryTransactionManager()
    txn_id = await mgr.begin()
    assert txn_id in mgr._txns
    assert mgr._txns[txn_id].status == "pending"
    await mgr.commit(txn_id)
    assert mgr._txns[txn_id].status == "committed"


@pytest.mark.asyncio
async def test_transaction_rollback():
    mgr = InMemoryTransactionManager()
    txn_id = await mgr.begin()
    await mgr.rollback(txn_id)
    assert mgr._txns[txn_id].status == "rolled_back"


@pytest.mark.asyncio
async def test_transaction_commit_unknown():
    mgr = InMemoryTransactionManager()
    await mgr.commit("nonexistent")
    assert True


@pytest.mark.asyncio
async def test_idempotency_not_processed():
    checker = InMemoryIdempotencyChecker()
    assert await checker.is_processed("req-1") is False


@pytest.mark.asyncio
async def test_idempotency_mark_and_check():
    checker = InMemoryIdempotencyChecker()
    await checker.mark_processed("req-1", {"status": "done"})
    assert await checker.is_processed("req-1") is True


@pytest.mark.asyncio
async def test_idempotency_multiple_keys():
    checker = InMemoryIdempotencyChecker()
    await checker.mark_processed("req-1")
    assert await checker.is_processed("req-1") is True
    assert await checker.is_processed("req-2") is False
