from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from engines.document.models.base import BaseDocument


class AggregationSource(BaseModel):
    name: str
    source_type: str = "table"
    connection: str | None = None
    description: str | None = None


class DimensionAttribute(BaseModel):
    name: str
    source_column: str | None = None
    data_type: str | None = None


class DimensionLevel(BaseModel):
    name: str
    source_column: str | None = None
    attributes: list[DimensionAttribute] = Field(default_factory=list)


class DimensionHierarchy(BaseModel):
    name: str = "Default"
    levels: list[DimensionLevel] = Field(default_factory=list)
    has_all: bool = True


class Dimension(BaseModel):
    name: str
    source_table: str | None = None
    dimension_type: str = "standard"
    hierarchies: list[DimensionHierarchy] = Field(default_factory=list)
    attributes: list[DimensionAttribute] = Field(default_factory=list)


class Measure(BaseModel):
    name: str
    source_column: str | None = None
    aggregator: str = "sum"
    format_string: str | None = None
    visible: bool = True


class AggregationRelationship(BaseModel):
    name: str
    source_table: str
    target_table: str
    source_column: str
    target_column: str
    cardinality: str = "many_to_one"


class AggregationDefinition(BaseModel):
    name: str
    source: str
    group_by: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    filter_expression: str | None = None
    materialized: bool = False


class UnifiedBiAggregationDocument(BaseDocument):
    name: str = ""
    description: str | None = None
    sources: list[AggregationSource] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(default_factory=list)
    measures: list[Measure] = Field(default_factory=list)
    relationships: list[AggregationRelationship] = Field(default_factory=list)
    aggregations: list[AggregationDefinition] = Field(default_factory=list)
    vendor_extensions: dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(populate_by_name=True)
