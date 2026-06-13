from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.base import BaseDocument
from engines.knowledge.models.ksdm_models import ProcessMiningDefinitionDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class JprmWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        doc = _require(document)
        yield await self._write(doc)

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
        return json.dumps(raw, indent=2, default=str).encode("utf-8")

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".jprm"]


def _require(doc: BaseDocument) -> ProcessMiningDefinitionDocument:
    assert isinstance(doc, ProcessMiningDefinitionDocument), f"Expected ProcessMiningDefinitionDocument, got {type(doc)}"
    return doc


def _clustering_config_to_dict(cc: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"algorithm": cc.algorithm.value}
    if cc.n_clusters is not None:
        result["n_clusters"] = cc.n_clusters
    if cc.eps is not None:
        result["eps"] = cc.eps
    if cc.dbscan_min_samples is not None:
        result["dbscan_min_samples"] = cc.dbscan_min_samples
    if cc.linkage is not None:
        result["linkage"] = cc.linkage
    if cc.affinity is not None:
        result["affinity"] = cc.affinity
    if cc.max_iter is not None:
        result["max_iter"] = cc.max_iter
    if cc.random_state is not None:
        result["random_state"] = cc.random_state
    if cc.distance_threshold is not None:
        result["distance_threshold"] = cc.distance_threshold
    return result
