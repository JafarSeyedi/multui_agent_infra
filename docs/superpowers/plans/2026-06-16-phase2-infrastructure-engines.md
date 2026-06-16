# Phase 2 — Infrastructure Engines Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Build four foundation engines that provide shared backend services — state management, configuration/secrets, security/auth, and data persistence — each following the per-engine model/parser/writer pattern.

**Architecture:** Each engine wraps existing `engines/storage/` providers. No storage backends are embedded. All engines use simple ABC plugin pattern with config-selected backends.

**Tech Stack:** Python 3.11+, pydantic v2, pytest, asyncio, mypy strict

---

## Engine: `engines/state/` — Domain 7 (State & Caching)

### File Structure
```
engines/state/
├── __init__.py
├── plugin.py                    # IStateBackend, ICache, IDistributedLock ABCs
├── models/
│   ├── __init__.py
│   ├── state_models.py          # StateEntry, CacheEntry, LockEntry, WorkflowSnapshot
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── state_config_parser.py
│   └── writers/
│       ├── __init__.py
│       └── state_config_writer.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_state_models.py
│   └── test_state_backends.py
```

### Task S1: Create `plugin.py` and `state_models.py`

- [ ] Create `engines/state/plugin.py`:

```python
# engines/state/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from .models.state_models import StateEntry, CacheEntry


class IStateBackend(ABC):
    name: str = "base"

    @abstractmethod
    async def load(self, instance_id: str) -> Optional[StateEntry]: ...
    @abstractmethod
    async def save(self, entry: StateEntry) -> None: ...
    @abstractmethod
    async def delete(self, instance_id: str) -> None: ...


class ICache(ABC):
    name: str = "base"

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]: ...
    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> None: ...
    @abstractmethod
    async def invalidate(self, key: str) -> None: ...


class IDistributedLock(ABC):
    name: str = "base"

    @abstractmethod
    async def acquire(self, resource: str, ttl: float = 30.0) -> bool: ...
    @abstractmethod
    async def release(self, resource: str) -> None: ...
```

- [ ] Create `engines/state/models/state_models.py`:

```python
# engines/state/models/state_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StateEntry:
    instance_id: str
    data: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CacheEntry:
    key: str
    value: Any = None
    ttl: float = 300.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

- [ ] Add `__init__.py` files, create dirs, create tests
- [ ] Run tests, commit

---

## Engine: `engines/config/` — Domain 8 (Configuration & Secrets)

### Task C1: Create `plugin.py` and models

- [ ] Create plugin with `IConfigSource` and `ISecretResolver` ABCs
- [ ] Create `config_models.py` with `DeploymentConfig`, `ConfigEntry`, `SecretRef`
- [ ] Implement `FileConfigSource` and `EnvironmentSecretResolver`
- [ ] Create parsers/writers, tests

---

## Engine: `engines/security/` — Domain 12 (Security)

### Task S1: Create `plugin.py` and models

- [ ] Create plugin with `IAuthenticator` and `IAuthorizer` ABCs
- [ ] Create `security_models.py` with `AuthenticationResult`, `AuthorizationContext`
- [ ] Implement `JwtAuthenticator` and `AlwaysAllowAuthorizer`
- [ ] Create parsers/writers, tests

---

## Engine: `engines/persistence/` — Domain 16 (Data Persistence & Storage)

### Task P1: Create `plugin.py` and models

- [ ] Create plugin with `IVectorStore` and `IBlobStorage` ABCs
- [ ] Create `persistence_models.py`
- [ ] Implement `InMemoryVectorStore` and `FileBlobStorage` for dev
- [ ] Create parsers/writers, tests
