# engines/security/tests/test_security_backends.py
import pytest
from engines.security.authenticators.api_key_auth import ApiKeyAuthenticator
from engines.security.authorizers.rbac_authorizer import RBACAuthorizer


@pytest.mark.asyncio
async def test_api_key_auth_valid():
    auth = ApiKeyAuthenticator({"sk-abc": "alice", "sk-xyz": "bob"})
    subject = await auth.authenticate({"api_key": "sk-abc"})
    assert subject == "alice"


@pytest.mark.asyncio
async def test_api_key_auth_invalid():
    auth = ApiKeyAuthenticator({})
    subject = await auth.authenticate({"api_key": "sk-invalid"})
    assert subject is None


@pytest.mark.asyncio
async def test_rbac_authorize_allowed():
    authorizer = RBACAuthorizer({"doc:1": ["read"], "doc:2": ["read", "write"]})
    assert await authorizer.authorize("alice", "doc:1", "read") is True
    assert await authorizer.authorize("alice", "doc:1", "write") is False


@pytest.mark.asyncio
async def test_rbac_authorize_missing_resource():
    authorizer = RBACAuthorizer({})
    assert await authorizer.authorize("alice", "doc:99", "read") is False
