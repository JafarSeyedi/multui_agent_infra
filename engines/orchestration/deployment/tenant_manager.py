"""Tenant partitioning support for deployment and execution contexts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantInfo:
    tenant_id: str
    name: str
    enabled: bool = True


class TenantManager:
    """In-memory tenant registry and validation."""

    def __init__(self) -> None:
        self._tenants: dict[str, TenantInfo] = {}

    def register(self, tenant_id: str, *, name: str, enabled: bool = True) -> None:
        self._tenants[tenant_id] = TenantInfo(tenant_id=tenant_id, name=name, enabled=enabled)

    def disable(self, tenant_id: str) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant:
            self._tenants[tenant_id] = TenantInfo(tenant_id=tenant.tenant_id, name=tenant.name, enabled=False)

    def is_enabled(self, tenant_id: str | None) -> bool:
        if tenant_id is None:
            return True
        tenant = self._tenants.get(tenant_id)
        return bool(tenant and tenant.enabled)

    def get(self, tenant_id: str) -> TenantInfo | None:
        return self._tenants.get(tenant_id)
