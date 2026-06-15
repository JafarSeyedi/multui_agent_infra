from __future__ import annotations

import pytest

from engines.session.artifacts import ArtifactPart, InMemoryArtifactService


class TestInMemoryArtifactService:

    @pytest.fixture
    def service(self):
        return InMemoryArtifactService()

    async def test_save_and_load_artifact(self, service):
        version = await service.save_artifact(
            "app1", "user1", "sess1", "test.txt",
            b"hello world", "text/plain",
        )
        assert version == 0

        part = await service.load_artifact("app1", "user1", "sess1", "test.txt")
        assert part is not None
        assert part.data == b"hello world"
        assert part.mime_type == "text/plain"

    async def test_load_nonexistent_artifact(self, service):
        part = await service.load_artifact("app1", "user1", "sess1", "nope.txt")
        assert part is None

    async def test_versioning_increments(self, service):
        v1 = await service.save_artifact("app1", "user1", "sess1", "file.txt", b"v1", "text/plain")
        v2 = await service.save_artifact("app1", "user1", "sess1", "file.txt", b"v2", "text/plain")
        assert v1 == 0
        assert v2 == 1

    async def test_load_specific_version(self, service):
        await service.save_artifact("app1", "user1", "sess1", "f.txt", b"first", "text/plain")
        await service.save_artifact("app1", "user1", "sess1", "f.txt", b"second", "text/plain")

        v0 = await service.load_artifact("app1", "user1", "sess1", "f.txt", version=0)
        v1 = await service.load_artifact("app1", "user1", "sess1", "f.txt", version=1)
        assert v0 is not None and v0.data == b"first"
        assert v1 is not None and v1.data == b"second"

    async def test_load_latest_version(self, service):
        await service.save_artifact("app1", "user1", "sess1", "f.txt", b"old", "text/plain")
        await service.save_artifact("app1", "user1", "sess1", "f.txt", b"new", "text/plain")

        latest = await service.load_artifact("app1", "user1", "sess1", "f.txt")
        assert latest is not None and latest.data == b"new"

    async def test_load_invalid_version(self, service):
        await service.save_artifact("app1", "user1", "sess1", "f.txt", b"data", "text/plain")
        result = await service.load_artifact("app1", "user1", "sess1", "f.txt", version=99)
        assert result is None

    async def test_list_artifact_keys(self, service):
        await service.save_artifact("app1", "u1", "s1", "a.txt", b"a", "text/plain")
        await service.save_artifact("app1", "u1", "s1", "b.txt", b"b", "text/plain")
        await service.save_artifact("app1", "u1", "s2", "c.txt", b"c", "text/plain")

        keys = await service.list_artifact_keys("app1", "u1", "s1")
        assert sorted(keys) == ["a.txt", "b.txt"]

    async def test_list_artifact_keys_empty(self, service):
        keys = await service.list_artifact_keys("app1", "u1", "s1")
        assert keys == []

    async def test_delete_artifact(self, service):
        await service.save_artifact("app1", "u1", "s1", "f.txt", b"data", "text/plain")
        await service.delete_artifact("app1", "u1", "s1", "f.txt")

        part = await service.load_artifact("app1", "u1", "s1", "f.txt")
        assert part is None

    async def test_delete_nonexistent(self, service):
        await service.delete_artifact("app1", "u1", "s1", "nope.txt")

    async def test_sessions_isolated(self, service):
        await service.save_artifact("app1", "u1", "s1", "f.txt", b"s1_data", "text/plain")
        await service.save_artifact("app1", "u1", "s2", "f.txt", b"s2_data", "text/plain")

        p1 = await service.load_artifact("app1", "u1", "s1", "f.txt")
        p2 = await service.load_artifact("app1", "u1", "s2", "f.txt")
        assert p1 is not None and p1.data == b"s1_data"
        assert p2 is not None and p2.data == b"s2_data"
