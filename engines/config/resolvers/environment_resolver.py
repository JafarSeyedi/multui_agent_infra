# engines/config/resolvers/environment_resolver.py
from __future__ import annotations

import os
from typing import Optional

from ..plugin import ISecretResolver


class EnvironmentSecretResolver(ISecretResolver):
    name = "environment"

    async def resolve(self, secret_ref: str) -> Optional[str]:
        return os.environ.get(secret_ref)
