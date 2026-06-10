from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO

from engines.document.writers.base import BaseDocument, BaseDocumentWriter
from engines.document.models.ksdm_models import (
    AttributeValue,
    MiningModelType,
    MlMiningDocument,
    ModelNode,
    OpType,
    TrainingTask,
)


def _set(elem: ET.Element, attr: str, value: str | None) -> None:
    if value is not None:
        elem.set(attr, value)


def _write_header(root: ET.Element, doc: MlMiningDocument) -> None:
    header = ET.SubElement(root, "Header")
    _set(header, "copyright", doc.vendor_extensions.get("copyright"))
    _set(header, "description", doc.vendor_extensions.get("description"))
    _set(header, "modelVersion", doc.vendor_extensions.get("model_version"))
    app_info = doc.vendor_extensions.get("application")
    if isinstance(app_info, dict):
        app_elem = ET.SubElement(header, "Application")
        _set(app_elem, "name", app_info.get("name"))
        _set(app_elem, "version", app_info.get("version"))


def _write_data_dictionary(root: ET.Element, doc: MlMiningDocument) -> None:
    dd = ET.SubElement(root, "DataDictionary")
    dd.set("numberOfFields", str(len(doc.features) + (1 if doc.target else 0)))
    for feat in doc.features:
        df = ET.SubElement(dd, "DataField")
        df.set("name", feat.name)
        df.set("dataType", feat.data_type.base.value)
        df.set("optype", "continuous")
    if doc.target:
        df = ET.SubElement(dd, "DataField")
        df.set("name", doc.target.name)
        df.set("dataType", doc.target.data_type.base.value)
        df.set("optype", "categorical")


def _write_mining_schema(parent: ET.Element, doc: MlMiningDocument) -> None:
    ms = ET.SubElement(parent, "MiningSchema")
    if doc.mining_schema and doc.mining_schema.fields:
        for mf in doc.mining_schema.fields:
            mf_elem = ET.SubElement(ms, "MiningField")
            mf_elem.set("name", mf.name)
            mf_elem.set("usageType", mf.usage_type.value)
            if mf.importance is not None:
                mf_elem.set("importance", str(mf.importance))
            _set(mf_elem, "missingValueReplacement", str(mf.missing_value_replacement) if mf.missing_value_replacement is not None else None)
            if mf.outliers is not None:
                mf_elem.set("outliers", mf.outliers.value)
            if mf.low_value is not None:
                mf_elem.set("lowValue", str(mf.low_value))
            if mf.high_value is not None:
                mf_elem.set("highValue", str(mf.high_value))
    else:
        for feat in doc.features:
            mf_elem = ET.SubElement(ms, "MiningField")
            mf_elem.set("name", feat.name)
            mf_elem.set("usageType", "active")
        if doc.target:
            mf_elem = ET.SubElement(ms, "MiningField")
            mf_elem.set("name", doc.target.name)
            mf_elem.set("usageType", "predicted")


def _write_outputs(parent: ET.Element, doc: MlMiningDocument) -> None:
    if not doc.results:
        return
    outputs = ET.SubElement(parent, "Outputs")
    for r in doc.results:
        of = ET.SubElement(outputs, "OutputField")
        of.set("name", r.name)
        if r.value is not None:
            of.set("value", str(r.value))
        _set(of, "description", r.description)


def _write_targets(parent: ET.Element, doc: MlMiningDocument) -> None:
    raw_targets = doc.vendor_extensions.get("targets", [])
    if not raw_targets:
        return
    targets_elem = ET.SubElement(parent, "Targets")
    for t in raw_targets:
        if isinstance(t, dict):
            te = ET.SubElement(targets_elem, "Target")
            _set(te, "field", t.get("field"))
            _set(te, "optype", t.get("optype"))
            _set(te, "castInteger", t.get("cast_integer"))
            if t.get("min") is not None:
                te.set("min", str(t["min"]))
            if t.get("max") is not None:
                te.set("max", str(t["max"]))
            if t.get("rescale_constant") is not None:
                te.set("rescaleConstant", str(t["rescale_constant"]))
            if t.get("rescale_factor") is not None:
                te.set("rescaleFactor", str(t["rescale_factor"]))


def _function_name(doc: MlMiningDocument) -> str:
    if doc.training_config and doc.training_config.task:
        return doc.training_config.task.value
    task_map: dict[MiningModelType, str] = {
        MiningModelType.DECISION_TREE: "classification",
        MiningModelType.NAIVE_BAYES: "classification",
        MiningModelType.SVM: "classification",
        MiningModelType.NEURAL_NETWORK: "classification",
        MiningModelType.REGRESSION: "regression",
        MiningModelType.CLUSTERING: "clustering",
    }
    return task_map.get(doc.model_type, "classification")


def _write_predicate(parent: ET.Element, node: ModelNode) -> None:
    pred = (node.attributes.get("predicate") or AttributeValue()).string_value
    if not pred:
        ET.SubElement(parent, "True")
        return
    if "compound:" in pred:
        cp = ET.SubElement(parent, "CompoundPredicate")
        cp.set("booleanOperator", pred.replace("compound:", ""))
        return
    parts = pred.split(" ", 2)
    if len(parts) == 3:
        sp = ET.SubElement(parent, "SimplePredicate")
        sp.set("field", parts[0])
        sp.set("operator", parts[1])
        sp.set("value", parts[2])
    else:
        ET.SubElement(parent, "True")


_NODE_ORDER = [OpType.TREE, OpType.TREE_SPLIT, OpType.LEAF]


def _write_node(parent: ET.Element, node: ModelNode) -> None:
    ne = ET.SubElement(parent, "Node")
    _set(ne, "id", node.id if node.id else None)
    _set(ne, "name", node.name if node.name else None)
    score = (node.attributes.get("score") or AttributeValue()).string_value
    _set(ne, "score", score)
    rc = (node.attributes.get("record_count") or AttributeValue()).int_value
    if rc is not None:
        ne.set("recordCount", str(rc))

    sd_values = (node.attributes.get("score_dist_values") or AttributeValue()).strings
    sd_counts = (node.attributes.get("score_dist_counts") or AttributeValue()).floats
    sd_confidences = (node.attributes.get("score_dist_confidences") or AttributeValue()).floats
    if sd_values:
        for i, val in enumerate(sd_values):
            sd_elem = ET.SubElement(ne, "ScoreDistribution")
            sd_elem.set("value", val)
            if i < len(sd_counts):
                sd_elem.set("recordCount", str(sd_counts[i]))
            if i < len(sd_confidences):
                sd_elem.set("confidence", str(sd_confidences[i]))

    if node.sub_graph:
        _write_predicate(ne, node)
        for child in sorted(node.sub_graph.nodes,
                            key=lambda n: _NODE_ORDER.index(n.op_type) if n.op_type in _NODE_ORDER else 99):
            _write_node(ne, child)
    else:
        _write_predicate(ne, node)


def _write_tree_model(parent: ET.Element, doc: MlMiningDocument) -> None:
    tm = ET.SubElement(parent, "TreeModel")
    tm.set("modelName", doc.title or "tree_model")
    tm.set("functionName", _function_name(doc))
    _set(tm, "splitCharacteristic", "binarySplit")
    _write_mining_schema(tm, doc)
    _write_outputs(tm, doc)
    _write_targets(tm, doc)
    graph = doc.model_graph
    if graph and graph.nodes:
        for n in graph.nodes:
            _write_node(tm, n)


def _write_regression_model(parent: ET.Element, doc: MlMiningDocument) -> None:
    rm = ET.SubElement(parent, "RegressionModel")
    rm.set("modelName", doc.title or "regression_model")
    rm.set("functionName", _function_name(doc))
    _write_mining_schema(rm, doc)
    _write_outputs(rm, doc)
    _write_targets(rm, doc)

    graph = doc.model_graph
    if graph and graph.nodes:
        for node in graph.nodes:
            if node.op_type == OpType.REGRESSION:
                rt = ET.SubElement(rm, "RegressionTable")
                intercept = (node.attributes.get("intercept") or AttributeValue()).float_value or 0.0
                rt.set("intercept", str(intercept))
                tc = (node.attributes.get("target_category") or AttributeValue()).string_value
                _set(rt, "targetCategory", tc)
                if node.sub_graph:
                    for pred_node in node.sub_graph.nodes:
                        coeff = (pred_node.attributes.get("coefficient") or AttributeValue()).float_value or 1.0
                        if pred_node.op_type == OpType.LINEAR_REGRESSION_MODEL:
                            if "value" in pred_node.attributes:
                                cp = ET.SubElement(rt, "CategoricalPredictor")
                                cp.set("name", pred_node.name)
                                cp.set("value", (pred_node.attributes["value"]).string_value or "")
                                cp.set("coefficient", str(coeff))
                            else:
                                np_elem = ET.SubElement(rt, "NumericPredictor")
                                np_elem.set("name", pred_node.name)
                                np_elem.set("coefficient", str(coeff))
                                exp = (pred_node.attributes.get("exponent") or AttributeValue()).int_value or 1
                                np_elem.set("exponent", str(exp))


def _write_clustering_model(parent: ET.Element, doc: MlMiningDocument) -> None:
    cm = ET.SubElement(parent, "ClusteringModel")
    cm.set("modelName", doc.title or "clustering_model")
    cm.set("functionName", _function_name(doc))
    _write_mining_schema(cm, doc)
    _write_outputs(cm, doc)
    _write_targets(cm, doc)

    graph = doc.model_graph
    if graph and graph.nodes:
        cm.set("numberOfClusters", str(len(graph.nodes)))
        for node in graph.nodes:
            if node.op_type == OpType.CLUSTERING:
                cl = ET.SubElement(cm, "Cluster")
                _set(cl, "id", node.id)
                _set(cl, "name", node.name)
                size = (node.attributes.get("size") or AttributeValue()).int_value
                if size is not None:
                    cl.set("size", str(size))
                coords = (node.attributes.get("coords") or AttributeValue()).floats
                if coords:
                    km = ET.SubElement(cl, "KohonenMap")
                    for i, c in enumerate(coords, 1):
                        km.set(f"coord{i}", str(c))


def _write_mining_model(parent: ET.Element, doc: MlMiningDocument) -> None:
    mm = ET.SubElement(parent, "MiningModel")
    mm.set("modelName", doc.title or "mining_model")
    mm.set("functionName", _function_name(doc))
    _set(mm, "modelType", doc.model_type.value)
    _write_mining_schema(mm, doc)
    _write_outputs(mm, doc)
    _write_targets(mm, doc)

    graph = doc.model_graph
    if graph and graph.nodes:
        seg_method = graph.metadata.get("multiple_model_method", "majorityVote")
        seg = ET.SubElement(mm, "Segmentation")
        seg.set("multipleModelMethod", seg_method)
        for i, node in enumerate(graph.nodes):
            segment = ET.SubElement(seg, "Segment")
            segment.set("id", str(i))
            if node.weight is not None:
                segment.set("weight", str(node.weight))
            if node.sub_graph:
                for sn in node.sub_graph.nodes:
                    _write_node(segment, sn)


def _write_model_element(parent: ET.Element, doc: MlMiningDocument) -> None:
    if doc.model_type == MiningModelType.DECISION_TREE:
        _write_tree_model(parent, doc)
    elif doc.model_type in (MiningModelType.REGRESSION, MiningModelType.SVM):
        _write_regression_model(parent, doc)
    elif doc.model_type == MiningModelType.CLUSTERING:
        _write_clustering_model(parent, doc)
    else:
        _write_mining_model(parent, doc)


class PmmlWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document: Any) -> bool:
        return isinstance(document, MlMiningDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | None = None, **options: Any) -> bytes:
        doc = MlMiningDocument.model_validate(document)

        root = ET.Element("PMML")
        root.set("version", "4.2")
        root.set("xmlns", "http://www.dmg.org/PMML-4_2")

        _write_header(root, doc)
        _write_data_dictionary(root, doc)
        _write_model_element(root, doc)

        ET.indent(ET.ElementTree(root), space="  ")
        xml_bytes = ET.tostring(root, encoding="unicode").encode("utf-8")

        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(xml_bytes)
            else:
                destination.write(xml_bytes)
        return xml_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return [".pmml"]
