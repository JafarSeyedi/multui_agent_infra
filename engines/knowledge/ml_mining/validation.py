from __future__ import annotations

from typing import Any

from engines.knowledge.models.ksdm_models import (
    MiningField,
    MiningSchema,
    ModelGraph,
    ModelNode,
    MlMiningDocument,
    OpType,
)
from engines.knowledge.ml_mining.converters import ConverterRegistry


def validate_document(doc: MlMiningDocument) -> list[str]:
    warnings: list[str] = []

    if not doc.title:
        warnings.append("Document has no title")

    if doc.model_type is None:
        warnings.append("Document has no model_type")
    if doc.model_format is None:
        warnings.append("Document has no model_format")

    if not doc.features and not doc.model_graph:
        warnings.append("Document has no features and no model graph")

    if doc.model_graph:
        warnings.extend(validate_graph(doc.model_graph))

    if doc.mining_schema:
        warnings.extend(validate_mining_schema(doc.mining_schema))

    if doc.model_data and len(doc.model_data) == 0:
        warnings.append("model_data is empty")

    return warnings


def validate_graph(graph: ModelGraph) -> list[str]:
    warnings: list[str] = []

    if not graph.nodes:
        warnings.append("Graph has no nodes")
        return warnings

    seen_ids: set[str] = set()
    for node, depth in _walk(graph):
        if node.id:
            if node.id in seen_ids:
                warnings.append(f"Duplicate node id: '{node.id}'")
            seen_ids.add(node.id)

        if node.op_type == OpType.CUSTOM:
            warnings.append(f"CUSTOM op_type on node '{node.id or '<unnamed>'}'")

        if node.inputs and node.outputs:
            if any(not p.name for p in node.inputs):
                warnings.append(f"Node '{node.id}' has unnamed inputs")
            if any(not p.name for p in node.outputs):
                warnings.append(f"Node '{node.id}' has unnamed outputs")

        if node.sub_graph:
            warnings.extend(validate_graph(node.sub_graph))
            for key in ("score", "predicate", "coefficient", "intercept"):
                if key in node.attributes:
                    warnings.append(
                        f"Node '{node.id}' has attribute '{key}' AND a sub_graph"
                    )

    converter = ConverterRegistry.find(graph)
    if converter is None and graph.nodes:
        warnings.append("No converter registered for this graph type — "
                        "inference unavailable")

    return warnings


def validate_mining_schema(schema: MiningSchema) -> list[str]:
    warnings: list[str] = []

    if not schema.fields:
        warnings.append("MiningSchema has no fields")

    field_names: set[str] = set()
    has_predicted = False
    for field in schema.fields:
        if not field.name:
            warnings.append("MiningField has no name")
        else:
            if field.name in field_names:
                warnings.append(f"Duplicate MiningField name: '{field.name}'")
            field_names.add(field.name)

        if field.usage_type is not None and str(field.usage_type) == "predicted":
            has_predicted = True

    if not has_predicted:
        warnings.append("MiningSchema has no predicted field")

    return warnings


def _walk(graph: ModelGraph) -> list[tuple[ModelNode, int]]:
    result: list[tuple[ModelNode, int]] = []

    def _recurse(g: ModelGraph, depth: int) -> None:
        for node in g.nodes:
            result.append((node, depth))
            if node.sub_graph:
                _recurse(node.sub_graph, depth + 1)

    _recurse(graph, 0)
    return result


__all__ = [
    "validate_document",
    "validate_graph",
    "validate_mining_schema",
]
