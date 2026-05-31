"""Multi-tenancy support for orchestration runtime.

Provides tenant-aware data isolation, tenant context propagation,
and tenant-scoped queries per Camunda/Orch8/Kestra patterns.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)

_current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)


@dataclass
class TenantInfo:
    tenant_id: str
    name: str | None = None
    description: str | None = None
    is_active: bool = True
    max_instances: int = 10000
    max_deployments: int = 1000
    metadata: dict[str, Any] = field(default_factory=dict)


class TenantContext:
    @staticmethod
    def get_current_tenant() -> str | None:
        return _current_tenant.get()

    @staticmethod
    def set_current_tenant(tenant_id: str | None) -> None:
        _current_tenant.set(tenant_id)

    @staticmethod
    @contextmanager
    def tenant_scope(tenant_id: str):
        prev = _current_tenant.get()
        _current_tenant.set(tenant_id)
        try:
            yield
        finally:
            _current_tenant.set(prev)

    @staticmethod
    def require_tenant() -> str:
        tenant_id = _current_tenant.get()
        if tenant_id is None:
            raise ValueError("No tenant context set")
        return tenant_id


class TenantAwareMixin:
    def _tenant_filter(self, data: dict[str, Any]) -> dict[str, Any]:
        tenant_id = TenantContext.get_current_tenant()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return data

    def _tenant_scope_predicate(self) -> dict[str, Any]:
        tenant_id = TenantContext.get_current_tenant()
        if tenant_id is not None:
            return {"tenant_id": tenant_id}
        return {}


class TenantManager:
    def __init__(self) -> None:
        self._tenants: dict[str, TenantInfo] = {}

    def register_tenant(self, tenant: TenantInfo) -> None:
        self._tenants[tenant.tenant_id] = tenant
        logger.info("Tenant registered: %s", tenant.tenant_id)

    def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        return self._tenants.get(tenant_id)

    def list_tenants(self, active_only: bool = False) -> list[TenantInfo]:
        tenants = list(self._tenants.values())
        if active_only:
            tenants = [t for t in tenants if t.is_active]
        return tenants

    def deactivate_tenant(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            return False
        tenant.is_active = False
        return True

    def is_tenant_active(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        return tenant is not None and tenant.is_active

    def check_tenant_quota(self, tenant_id: str, current_instances: int) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            return True
        return current_instances < tenant.max_instances
