"""Generate Kubernetes manifest dictionaries from SSDM deployment descriptors."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import DeploymentDescriptor, ServiceType


class KubernetesManifestWriter:
    """Render lightweight Kubernetes deployment/service manifests."""

    def dump(self, deployment: DeploymentDescriptor) -> list[dict[str, Any]]:
        return [
            self._deployment_manifest(deployment),
            self._service_manifest(deployment),
        ]

    def _deployment_manifest(self, deployment: DeploymentDescriptor) -> dict[str, Any]:
        container: dict[str, Any] = {
            "name": deployment.service_name,
            "image": deployment.container_image,
            "command": deployment.command,
            "args": deployment.args,
            "env": [{"name": key, "value": value} for key, value in deployment.environment.items()],
            "ports": [{"containerPort": port.container_port, "protocol": port.protocol.value} for port in deployment.ports],
        }
        container = {key: value for key, value in container.items() if value not in (None, [], {})}
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": deployment.service_name, "labels": deployment.labels},
            "spec": {
                "replicas": deployment.replicas,
                "selector": {"matchLabels": {"app": deployment.service_name}},
                "template": {
                    "metadata": {"labels": {"app": deployment.service_name, **deployment.labels}},
                    "spec": {"containers": [container]},
                },
            },
        }

    def _service_manifest(self, deployment: DeploymentDescriptor) -> dict[str, Any]:
        service_type = deployment.service_exposure.type.value if deployment.service_exposure else ServiceType.CLUSTER_IP.value
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": deployment.service_name, "labels": deployment.labels},
            "spec": {
                "type": service_type,
                "selector": {"app": deployment.service_name},
                "ports": [
                    {
                        "port": port.service_port or port.container_port,
                        "targetPort": port.container_port,
                        "protocol": port.protocol.value,
                        **({"name": port.name} if port.name else {}),
                    }
                    for port in deployment.ports
                ],
            },
        }
