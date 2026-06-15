from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict
from pydantic.dataclasses import dataclass

from engines.document.models.base import BaseDocument
from engines.knowledge.graph.models.graph_models import KnowledgeGraph


class TransformationLogicalSource(BaseModel):
    source_name: str | None = None
    iterator: str | None = None
    reference_formulation: str | None = None
    query: str | None = None
    table_name: str | None = None


class TransformationSubjectMap(BaseModel):
    class_type: str | None = None
    graph_map: str | None = None
    uri_template: str | None = None
    prefix_iri: str | None = None


class TransformationPredicateObjectMap(BaseModel):
    predicate: str | None = None
    object_map: str | None = None
    datatype: str | None = None
    language: str | None = None
    parent_triples_map: str | None = None


class TransformationSubjectMapRef(BaseModel):
    parent_triples_map: str


class TransformationMapping(BaseModel):
    base_iri: str | None = None
    prefixes: dict[str, str] = Field(default_factory=dict)
    logical_sources: list[TransformationLogicalSource] = Field(default_factory=list)
    subject_maps: list[TransformationSubjectMap] = Field(default_factory=list)
    predicate_object_maps: list[TransformationPredicateObjectMap] = Field(default_factory=list)
    references: list[TransformationSubjectMapRef] = Field(default_factory=list)


class SemanticGraphDocument(BaseDocument):
    knowledge_graph: KnowledgeGraph | None = None
    model_config = ConfigDict(populate_by_name=True)


class TransformationModelDocument(BaseDocument):
    mappings: list[TransformationMapping] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)
