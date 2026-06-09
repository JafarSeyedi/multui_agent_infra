from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import yaml

from engines.document.models.base import BaseDocument
from engines.document.models.ksdm_models import ProcessMiningDefinitionDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions
from engines.document.writers.ksdm_writers.process_mining.jprm_writer import _clustering_config_to_dict, _require


class YprmWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self._write(_require(document))

    async def write(self, document: BaseDocument) -> bytes:
        return await self._write(_require(document))

    async def _write(self, document: ProcessMiningDefinitionDocument) -> bytes:
        raw: dict[str, Any] = {
            "title": document.title,
            "metadata": document.metadata,
        }
        processes = {}
        for pid, pdef in document.processes.items():
            dps = {}
            for dpid, dp in pdef.decision_points.items():
                dp_dict: dict[str, Any] = {"description": dp.description}
                dp_dict["mining_algorithm"] = dp.mining_algorithm.value
                if dp.clustering_config:
                    dp_dict["clustering_config"] = _clustering_config_to_dict(dp.clustering_config)
                if dp.min_support is not None:
                    dp_dict["min_support"] = dp.min_support
                if dp.min_confidence is not None:
                    dp_dict["min_confidence"] = dp.min_confidence
                if dp.max_rules is not None:
                    dp_dict["max_rules"] = dp.max_rules
                dps[dpid] = dp_dict
            ceds = {}
            for cid, ce in pdef.catch_event_definitions.items():
                ce_dict: dict[str, Any] = {"description": ce.description}
                if ce.clustering_config:
                    ce_dict["clustering_config"] = _clustering_config_to_dict(ce.clustering_config)
                if ce.min_events_per_cluster is not None:
                    ce_dict["min_events_per_cluster"] = ce.min_events_per_cluster
                ce_dict["output_pmml_model"] = ce.output_pmml_model
                ceds[cid] = ce_dict
            p_dict: dict[str, Any] = {"description": pdef.description}
            if pdef.mining_name:
                p_dict["mining_name"] = pdef.mining_name
            p_dict["decision_points"] = dps
            p_dict["catch_event_definitions"] = ceds
            processes[pid] = p_dict
        raw["processes"] = processes
        if document.default_clustering_config:
            raw["default_clustering_config"] = _clustering_config_to_dict(document.default_clustering_config)
        return yaml.dump(raw, default_flow_style=False, sort_keys=False).encode("utf-8")

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-yaml"]

    def get_supported_extensions(self) -> list[str]:
        return [".yprm"]
