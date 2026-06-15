from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import Field, ConfigDict

from engines.document.models.base import BaseDocument
from engines.document.models.lsdm_models import EventLogDocument
from engines.document.models.standard import DocumentStandard
from engines.orchestration.bpmn.models.bpmn_models import CatchEvent, FlowElement, Process
from engines.knowledge.ml_mining.models.ml_mining_models import MiningModelType


@dataclass
class ClusteringConfig:
    algorithm: MiningModelType = MiningModelType.CLUSTERING
    n_clusters: int | None = None
    eps: float | None = None
    dbscan_min_samples: int | None = None
    linkage: str | None = None
    affinity: str | None = None
    max_iter: int | None = None
    random_state: int | None = None
    distance_threshold: float | None = None


@dataclass
class DecisionPointDefinition:
    id: str
    description: str | None = None
    flow_element: FlowElement | None = None
    mining_algorithm: MiningModelType = MiningModelType.DECISION_TREE
    clustering_config: ClusteringConfig | None = None
    min_support: float | None = None
    min_confidence: float | None = None
    max_rules: int | None = None


@dataclass
class CatchEventMiningDefinition:
    id: str
    description: str | None = None
    catch_event: CatchEvent | None = None
    clustering_config: ClusteringConfig | None = None
    min_events_per_cluster: int | None = None
    output_pmml_model: bool = True


@dataclass
class MiningProcessDefinition:
    id: str
    description: str | None = None
    process: Process | None = None
    event_source: EventLogDocument | None = None
    decision_points: dict[str, DecisionPointDefinition] = field(default_factory=dict)
    catch_event_definitions: dict[str, CatchEventMiningDefinition] = field(default_factory=dict)
    mining_name: str | None = None


class ProcessMiningDefinitionDocument(BaseDocument):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    kind: DocumentStandard = Field(default=DocumentStandard.KSDM)
    title: str = ""
    document_id: str = ""
    processes: dict[str, MiningProcessDefinition] = Field(default_factory=dict)
    default_clustering_config: ClusteringConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
