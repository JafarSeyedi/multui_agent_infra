# engines/security/models/parsers/security_policy_parser.py
from __future__ import annotations

from ..security_models import Permission


def parse_permission(data: dict) -> Permission:
    return Permission(
        resource=data["resource"],
        action=data["action"],
        effect=data.get("effect", "deny"),
    )
