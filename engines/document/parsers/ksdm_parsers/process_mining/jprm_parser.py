from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from engines.document.models.ksdm_models import (
    CatchEventMiningDefinition,
    ClusteringConfig,
    DecisionPointDefinition,
    MiningModelType,
    MiningProcessDefinition,
    ProcessMiningDefinitionDocument,
)
from engines.document.models.media_types import MEDIA_TYPES, MediaType
from ...base import BaseDocumentParser, ParseOptions


class JprmParser(BaseDocumentParser):
    name = "jprm_parser"
    supported_extensions = [".jprm"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> ProcessMiningDefinitionDocument:
        raw = json.loads(data.decode("utf-8"))
        processes = {}
        for pid, pdata in raw.get("processes", {}).items():
            dps = {}
            for dpid, dpdata in pdata.get("decision_points", {}).items():
                cc = None
                if "clustering_config" in dpdata and dpdata["clustering_config"]:
                    cc = _parse_clustering_config(dpdata["clustering_config"])
                dps[dpid] = DecisionPointDefinition(
                    id=dpid,
                    description=dpdata.get("description"),
                    flow_element=None,
                    mining_algorithm=MiningModelType(dpdata.get("mining_algorithm", "decision_tree")),
                    clustering_config=cc,
                    min_support=dpdata.get("min_support"),
                    min_confidence=dpdata.get("min_confidence"),
                    max_rules=dpdata.get("max_rules"),
                )
            ceds = {}
            for cid, cdata in pdata.get("catch_event_definitions", {}).items():
                cc = None
                if "clustering_config" in cdata and cdata["clustering_config"]:
                    cc = _parse_clustering_config(cdata["clustering_config"])
                ceds[cid] = CatchEventMiningDefinition(
                    id=cid,
                    description=cdata.get("description"),
                    catch_event=None,
                    clustering_config=cc,
                    min_events_per_cluster=cdata.get("min_events_per_cluster"),
                    output_pmml_model=cdata.get("output_pmml_model", True),
                )
            processes[pid] = MiningProcessDefinition(
                id=pid,
                description=pdata.get("description"),
                process=None,
                event_source=None,
                decision_points=dps,
                catch_event_definitions=ceds,
                mining_name=pdata.get("mining_name"),
            )
        dcc = None
        if "default_clustering_config" in raw and raw["default_clustering_config"]:
            dcc = _parse_clustering_config(raw["default_clustering_config"])
        return ProcessMiningDefinitionDocument(
            title=raw.get("title", ""),
            document_id=document_id,
            processes=processes,
            default_clustering_config=dcc,
            metadata=raw.get("metadata", {}),
            media_type=cast(MediaType, MEDIA_TYPES.get("jprm_json")),
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> ProcessMiningDefinitionDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> ProcessMiningDefinitionDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name, metadata, options)


def _parse_clustering_config(data: dict[str, Any]) -> ClusteringConfig:
    return ClusteringConfig(
        algorithm=MiningModelType(data.get("algorithm", "clustering")),
        n_clusters=data.get("n_clusters"),
        eps=data.get("eps"),
        dbscan_min_samples=data.get("dbscan_min_samples"),
        linkage=data.get("linkage"),
        affinity=data.get("affinity"),
        max_iter=data.get("max_iter"),
        random_state=data.get("random_state"),
        distance_threshold=data.get("distance_threshold"),
    )
