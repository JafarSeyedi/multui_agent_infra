"""Service discovery helpers for communication runtime."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from ...document.models.ssdm_models import DiscoveryBackend, DiscoveryConfig


@dataclass
class DiscoveryResult:
    target: str | None
    targets: list[str]
    source: str
    metadata: dict[str, Any]


class ServiceDiscovery:
    """Resolve service endpoints from static and common discovery backends."""

    def __init__(
        self,
        *,
        static_endpoints: dict[str, list[str]] | None = None,
        fallback_transport_targets: dict[str, str] | None = None,
    ) -> None:
        self.static_endpoints = static_endpoints or {}
        self.fallback_transport_targets = fallback_transport_targets or {}

    def resolve(
        self,
        operation_id: str,
        binding_endpoint: str | None = None,
        *,
        discovery: DiscoveryConfig | None = None,
    ) -> DiscoveryResult:
        if binding_endpoint:
            return DiscoveryResult(binding_endpoint, [binding_endpoint], "binding", {})

        if operation_id in self.static_endpoints and self.static_endpoints[operation_id]:
            endpoints = list(self.static_endpoints[operation_id])
            return DiscoveryResult(random.choice(endpoints), endpoints, "static", {"operation_id": operation_id})

        backend = discovery.backend if discovery else DiscoveryBackend.NONE
        if backend == DiscoveryBackend.NONE:
            if operation_id in self.fallback_transport_targets:
                target = self.fallback_transport_targets[operation_id]
                return DiscoveryResult(target, [target], "config", {"operation_id": operation_id})
            return DiscoveryResult(None, [], "none", {"operation_id": operation_id})

        if backend == DiscoveryBackend.DNS:
            if discovery is None:
                raise RuntimeError("DNS discovery requires DiscoveryConfig")
            return self._resolve_dns(operation_id, discovery)
        if backend == DiscoveryBackend.KUBERNETES:
            if discovery is None:
                raise RuntimeError("Kubernetes discovery requires DiscoveryConfig")
            return self._resolve_kubernetes(operation_id, discovery)

        # Other backends (consul/eureka/etcd/zookeeper) are intentionally lazy-loadable.
        method = getattr(self, f"_resolve_{backend.value}", None)
        if method is not None:
            return method(operation_id, discovery)

        raise RuntimeError(f"Unsupported discovery backend '{backend.value}'")

    def _resolve_dns(self, operation_id: str, discovery: DiscoveryConfig) -> DiscoveryResult:
        name = discovery.dns_name or operation_id
        if not name:
            raise RuntimeError("dns_name is required for DNS discovery")

        try:
            import socket
            info = socket.getaddrinfo(name, discovery.port or 80, proto=socket.IPPROTO_TCP)
            targets = [f"{str(sock[4][0])}:{int(sock[4][1])}" for sock in info if sock[4]]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"DNS lookup failed for {name}") from exc

        if not targets:
            raise RuntimeError(f"No DNS result for {name}")
        return DiscoveryResult(random.choice(targets), targets, "dns", {"name": name})

    def _resolve_kubernetes(self, operation_id: str, discovery: DiscoveryConfig) -> DiscoveryResult:
        namespace = discovery.namespace or "default"
        service_name = discovery.service_name or operation_id

        try:
            from kubernetes import client, config  # type: ignore[import-untyped]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("kubernetes package required for Kubernetes discovery") from exc

        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()

        core = client.CoreV1Api()
        svc_list = core.read_namespaced_service_status(name=service_name, namespace=namespace)
        if not svc_list or not svc_list.spec.ports:
            raise RuntimeError(f"Kubernetes service not found or no ports: {service_name}")

        port = discovery.port or (svc_list.spec.ports[0].port if svc_list.spec.ports else 80)
        target = f"{service_name}.{namespace}:{port}"
        return DiscoveryResult(target, [target], "kubernetes", {"service": service_name, "namespace": namespace})


# ---------------------------------------------------------------------------
# backend helpers for future extension
# ---------------------------------------------------------------------------
def _backend_none(
    operation_id: str,
    discovery: DiscoveryConfig | None = None,
):
    return DiscoveryResult(
        None,
        [],
        "none",
        {"operation_id": operation_id},
    )


def _backend_static(
    operation_id: str,
    discovery: DiscoveryConfig | None = None,
) -> DiscoveryResult:
    if discovery is None or not discovery.static_hosts:
        raise RuntimeError("static discovery requires DiscoveryConfig.static_hosts")
    return DiscoveryResult(discovery.static_hosts[0], list(discovery.static_hosts), "static", {"operation_id": operation_id})


def _backend_consul(
    operation_id: str,
    discovery: DiscoveryConfig | None = None,
):
    raise RuntimeError("Consul discovery not implemented in this lightweight runtime")


def _backend_eureka(
    operation_id: str,
    discovery: DiscoveryConfig | None = None,
):
    raise RuntimeError("Eureka discovery not implemented in this lightweight runtime")


def _backend_etcd(
    operation_id: str,
    discovery: DiscoveryConfig | None = None,
):
    raise RuntimeError("ETCD discovery not implemented in this lightweight runtime")


def _backend_zookeeper(
    operation_id: str,
    discovery: DiscoveryConfig | None = None,
):
    raise RuntimeError("ZooKeeper discovery not implemented in this lightweight runtime")
