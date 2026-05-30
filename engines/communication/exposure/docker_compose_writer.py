"""Generate Docker Compose service fragments from SSDM deployment descriptors."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import DeploymentDescriptor


class DockerComposeWriter:
    """Produce a Compose-compatible service spec."""

    def dump_service(self, deployment: DeploymentDescriptor) -> dict[str, Any]:
        service: dict[str, Any] = {
            "image": deployment.container_image,
            "command": deployment.command,
            "entrypoint": deployment.args,
            "environment": deployment.environment,
            "ports": [self._port_mapping(port) for port in deployment.ports],
            "labels": deployment.labels,
        }
        return {key: value for key, value in service.items() if value not in (None, [], {}, "")}

    def dump(self, deployments: list[DeploymentDescriptor]) -> dict[str, Any]:
        return {
            "version": "3.9",
            "services": {
                deployment.service_name: self.dump_service(deployment)
                for deployment in deployments
            },
        }

    @staticmethod
    def _port_mapping(port: Any) -> str:
        host_port = port.host_port or port.service_port or port.container_port
        return f"{host_port}:{port.container_port}"
