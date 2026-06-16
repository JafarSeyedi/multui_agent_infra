# engines/security/models/writers/security_policy_writer.py
from __future__ import annotations

from ..security_models import Permission


def write_permission(perm: Permission) -> dict:
    return {"resource": perm.resource, "action": perm.action, "effect": perm.effect}
