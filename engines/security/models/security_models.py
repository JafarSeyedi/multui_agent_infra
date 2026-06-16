# engines/security/models/security_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Credential:
    username: str = ""
    password_hash: str = ""
    token: str = ""


@dataclass
class Principal:
    subject: str
    roles: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Permission:
    resource: str
    action: str
    effect: str = "deny"
