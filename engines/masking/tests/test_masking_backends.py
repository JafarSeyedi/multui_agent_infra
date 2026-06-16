# engines/masking/tests/test_masking_backends.py
import pytest
from engines.masking.backends.in_memory.in_memory_masking import (
    InMemoryMaskingEngine,
    InMemoryAnonymizer,
)


@pytest.mark.asyncio
async def test_mask_simple_field():
    engine = InMemoryMaskingEngine()
    data = {"ssn": "123-45-6789", "name": "Alice"}
    result = await engine.mask(data, ["ssn"])
    assert result["ssn"] == "***"
    assert result["name"] == "Alice"


@pytest.mark.asyncio
async def test_mask_nested_field():
    engine = InMemoryMaskingEngine()
    data = {"user": {"email": "alice@example.com", "name": "Alice"}}
    result = await engine.mask(data, ["user.email"])
    assert result["user"]["email"] == "***"


@pytest.mark.asyncio
async def test_mask_no_matching_field():
    engine = InMemoryMaskingEngine()
    data = {"name": "Alice"}
    result = await engine.mask(data, ["ssn"])
    assert result == data


@pytest.mark.asyncio
async def test_anonymize_ssn():
    anon = InMemoryAnonymizer()
    result = await anon.anonymize("My SSN is 123-45-6789")
    assert "XXX-XX-XXXX" in result
    assert "123-45-6789" not in result


@pytest.mark.asyncio
async def test_anonymize_email():
    anon = InMemoryAnonymizer()
    result = await anon.anonymize("Contact me at alice@example.com")
    assert "[email]" in result
    assert "alice@example.com" not in result


@pytest.mark.asyncio
async def test_anonymize_no_match():
    anon = InMemoryAnonymizer()
    result = await anon.anonymize("Hello world")
    assert result == "Hello world"
