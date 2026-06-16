# engines/security/tests/test_security_models.py
from engines.security.models.security_models import Credential, Principal, Permission
from engines.security.models.parsers.security_policy_parser import parse_permission
from engines.security.models.writers.security_policy_writer import write_permission


def test_credential():
    c = Credential(username="alice")
    assert c.username == "alice"


def test_principal_defaults():
    p = Principal(subject="sub")
    assert p.roles == []


def test_permission_roundtrip():
    perm = Permission(resource="doc:1", action="read", effect="allow")
    data = write_permission(perm)
    parsed = parse_permission(data)
    assert parsed.resource == "doc:1"
    assert parsed.action == "read"
    assert parsed.effect == "allow"
