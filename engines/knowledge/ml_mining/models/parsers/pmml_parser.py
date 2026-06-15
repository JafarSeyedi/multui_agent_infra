from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.knowledge.ml_mining.models import (
    AttributeValue,
    EvaluationStage,
    FieldUsageType,
    MiningField,
    MiningModelType,
    MiningSchema,
    ModelFormat,
    ModelGraph,
    ModelMetric,
    ModelNode,
    ModelResult,
    MlMiningDocument,
    OpType,
    OutlierTreatment,
    Port,
    TrainingConfig,
    TrainingTask,
)
from engines.document.models.msdm_models import Attribute as MsdmAttribute, DataType, ScalarType
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.parsers.base import BaseDocumentParser, ParseOptions


_PMML_NS = "http://www.dmg.org/PMML-4_2"
_PMML_TAG = f"{{{_PMML_NS}}}"


def _local(elem: ET.Element, tag: str) -> ET.Element | None:
    tagged = elem.find(f".//{tag}")
    if tagged is not None:
        return tagged
    return elem.find(f".//{_PMML_TAG}{tag}")


def _findall(elem: ET.Element, tag: str) -> list[ET.Element]:
    results = elem.findall(f".//{tag}")
    if not results:
        results = elem.findall(f".//{_PMML_TAG}{tag}")
    return results


def _find(elem: ET.Element, tag: str) -> ET.Element | None:
    res = elem.find(f".//{tag}")
    if res is not None:
        return res
    return elem.find(f".//{_PMML_TAG}{tag}")


def _iter(elem: ET.Element, tag: str) -> list[ET.Element]:
    results = list(elem.iter(tag))
    if not results:
        results = list(elem.iter(f"{_PMML_TAG}{tag}"))
    return results


def _children(elem: ET.Element, tag: str) -> list[ET.Element]:
    results = list(elem.findall(tag))
    if not results:
        results = list(elem.findall(f"{_PMML_TAG}{tag}"))
    return results


def _attr_str(elem: ET.Element, name: str, default: str = "") -> str:
    val = elem.get(name)
    if val is not None:
        return val
    val = elem.get(f"{{{_PMML_NS}}}{name}")
    if val is not None:
        return val
    return default


def _attr_opt(elem: ET.Element, name: str) -> str | None:
    val = elem.get(name)
    if val is not None:
        return val
    return elem.get(f"{{{_PMML_NS}}}{name}")


def _attr_float(elem: ET.Element, name: str) -> float | None:
    val = _attr_opt(elem, name)
    return float(val) if val is not None else None


def _attr_int(elem: ET.Element, name: str) -> int | None:
    val = _attr_opt(elem, name)
    return int(val) if val is not None else None


def _parse_predicate(elem: ET.Element) -> str:
    for child in _children(elem, "SimplePredicate"):
        return f"{_attr_str(child, 'field')} {_attr_str(child, 'operator')} {_attr_str(child, 'value')}"
    for child in _children(elem, "CompoundPredicate"):
        return f"compound:{_attr_str(child, 'booleanOperator')}"
    for _child in _children(elem, "True"):
        return "true"
    for _child in _children(elem, "False"):
        return "false"
    return ""


def _parse_node(elem: ET.Element) -> ModelNode:
    node_id = _attr_str(elem, "id")
    score = _attr_opt(elem, "score")
    record_count = _attr_int(elem, "recordCount")
    predicate_str = _parse_predicate(elem)

    child_nodes = _children(elem, "Node")
    is_leaf = len(child_nodes) == 0

    if is_leaf:
        op_type = OpType.LEAF
    elif predicate_str and predicate_str != "true":
        op_type = OpType.TREE_SPLIT
    else:
        op_type = OpType.TREE

    attrs: dict[str, AttributeValue] = {}
    if score is not None:
        attrs["score"] = AttributeValue(string_value=score)
    if record_count is not None:
        attrs["record_count"] = AttributeValue(int_value=record_count)
    if predicate_str:
        attrs["predicate"] = AttributeValue(string_value=predicate_str)

    sd_elements = _children(elem, "ScoreDistribution")
    if sd_elements:
        sd_values: list[str] = []
        sd_counts: list[float] = []
        sd_confidences: list[float] = []
        for sd in sd_elements:
            sd_values.append(_attr_str(sd, "value"))
            rc = _attr_float(sd, "recordCount")
            sd_counts.append(rc if rc is not None else 0.0)
            conf = _attr_float(sd, "confidence")
            if conf is not None:
                sd_confidences.append(conf)
        attrs["score_dist_values"] = AttributeValue(strings=sd_values)
        attrs["score_dist_counts"] = AttributeValue(floats=sd_counts)
        if sd_confidences:
            attrs["score_dist_confidences"] = AttributeValue(floats=sd_confidences)

    sub_graph = None
    if not is_leaf and child_nodes:
        sub_graph = ModelGraph(
            name=f"children_{node_id}",
            nodes=[_parse_node(cn) for cn in child_nodes],
        )

    return ModelNode(
        id=node_id or f"node_{id(elem)}",
        op_type=op_type,
        name=_attr_str(elem, "name") or score or "",
        attributes=attrs,
        sub_graph=sub_graph,
    )


def _parse_mining_schema(elem: ET.Element) -> MiningSchema | None:
    ms_elem = _find(elem, "MiningSchema")
    if ms_elem is None:
        return None
    fields: list[MiningField] = []
    for mf in _iter(ms_elem, "MiningField"):
        raw_usage = _attr_str(mf, "usageType", "active")
        try:
            usage_type = FieldUsageType(raw_usage)
        except ValueError:
            usage_type = FieldUsageType.ACTIVE
        imp = _attr_float(mf, "importance")
        raw_ot = _attr_opt(mf, "outliers")
        outlier_treatment: OutlierTreatment | None = None
        if raw_ot:
            try:
                outlier_treatment = OutlierTreatment(raw_ot)
            except ValueError:
                pass
        fields.append(MiningField(
            name=_attr_str(mf, "name"),
            usage_type=usage_type,
            importance=imp,
            missing_value_replacement=_attr_opt(mf, "missingValueReplacement"),
            outliers=outlier_treatment,
            low_value=_attr_float(mf, "lowValue"),
            high_value=_attr_float(mf, "highValue"),
        ))
    return MiningSchema(fields=fields) if fields else None


def _parse_data_dictionary(root: ET.Element) -> dict[str, DataType]:
    dd = _find(root, "DataDictionary")
    if dd is None:
        return {}
    _DATA_TYPE_MAP = {
        "string": ScalarType.STRING,
        "integer": ScalarType.INT,
        "float": ScalarType.FLOAT,
        "double": ScalarType.DOUBLE,
        "boolean": ScalarType.BOOLEAN,
    }
    result: dict[str, DataType] = {}
    for df in _iter(dd, "DataField"):
        raw_dt = _attr_str(df, "dataType", "string").lower()
        base = _DATA_TYPE_MAP.get(raw_dt, ScalarType.STRING)
        result[_attr_str(df, "name")] = DataType(base=base)
    return result


def _parse_targets(elem: ET.Element) -> list[dict[str, Any]]:
    targets_elem = _find(elem, "Targets")
    if targets_elem is None:
        return []
    result: list[dict[str, Any]] = []
    for t in _iter(targets_elem, "Target"):
        result.append({
            "field": _attr_str(t, "field"),
            "optype": _attr_opt(t, "optype"),
            "cast_integer": _attr_opt(t, "castInteger"),
            "min": _attr_float(t, "min"),
            "max": _attr_float(t, "max"),
            "rescale_constant": _attr_float(t, "rescaleConstant"),
            "rescale_factor": _attr_float(t, "rescaleFactor"),
        })
    return result


def _parse_outputs(elem: ET.Element) -> list[ModelResult]:
    outputs_elem = _find(elem, "Outputs")
    if outputs_elem is None:
        return []
    result: list[ModelResult] = []
    for of in _iter(outputs_elem, "OutputField"):
        result.append(ModelResult(
            name=_attr_str(of, "name"),
            value=_attr_opt(of, "value"),
            description=_attr_opt(of, "description"),
        ))
    return result


def _parse_header(root: ET.Element) -> dict[str, Any]:
    header = _find(root, "Header")
    if header is None:
        return {}
    hdr: dict[str, Any] = {
        "copyright": _attr_opt(header, "copyright"),
        "description": _attr_opt(header, "description"),
        "model_version": _attr_opt(header, "modelVersion"),
    }
    app = _find(header, "Application")
    if app is not None:
        hdr["application"] = {
            "name": _attr_str(app, "name"),
            "version": _attr_opt(app, "version"),
        }
    return hdr


def _parse_regression_model(elem: ET.Element) -> ModelGraph:
    nodes: list[ModelNode] = []
    for rt in _children(elem, "RegressionTable"):
        intercept = _attr_float(rt, "intercept") or 0.0
        target_category = _attr_opt(rt, "targetCategory")
        predictors: list[ModelNode] = []
        for np_elem in _children(rt, "NumericPredictor"):
            predictors.append(ModelNode(
                id=_attr_str(np_elem, "name", "np"),
                op_type=OpType.LINEAR_REGRESSION_MODEL,
                name=_attr_str(np_elem, "name", ""),
                attributes={
                    "coefficient": AttributeValue(float_value=_attr_float(np_elem, "coefficient") or 1.0),
                    "exponent": AttributeValue(int_value=_attr_int(np_elem, "exponent") or 1),
                },
            ))
        for cp_elem in _children(rt, "CategoricalPredictor"):
            predictors.append(ModelNode(
                id=f"{_attr_str(cp_elem, 'name')}={_attr_str(cp_elem, 'value')}",
                op_type=OpType.LINEAR_REGRESSION_MODEL,
                name=_attr_str(cp_elem, "name", ""),
                attributes={
                    "value": AttributeValue(string_value=_attr_str(cp_elem, "value")),
                    "coefficient": AttributeValue(float_value=_attr_float(cp_elem, "coefficient") or 1.0),
                },
            ))
        rt_attrs: dict[str, AttributeValue] = {
            "intercept": AttributeValue(float_value=intercept),
        }
        if target_category is not None:
            rt_attrs["target_category"] = AttributeValue(string_value=target_category)
        reg_node = ModelNode(
            id=f"regression_table_{len(nodes)}",
            op_type=OpType.REGRESSION,
            name=target_category or "regression",
            attributes=rt_attrs,
            sub_graph=ModelGraph(nodes=predictors) if predictors else None,
        )
        nodes.append(reg_node)

    return ModelGraph(
        name=_attr_str(elem, "modelName", "regression"),
        nodes=nodes if nodes else [
            ModelNode(id="reg", op_type=OpType.REGRESSION, name="regression",
                      attributes={"intercept": AttributeValue(float_value=0.0)})
        ],
    )


def _parse_clustering_model(elem: ET.Element) -> ModelGraph:
    nodes: list[ModelNode] = []
    for cluster in _children(elem, "Cluster"):
        size = _attr_int(cluster, "size")
        attrs: dict[str, AttributeValue] = {}
        if size is not None:
            attrs["size"] = AttributeValue(int_value=size)
        km_elem = _find(cluster, "KohonenMap")
        coords_elem = km_elem if km_elem is not None else cluster
        coord_values: list[float] = []
        for i in range(1, 5):
            cv = _attr_float(coords_elem, f"coord{i}")
            if cv is not None:
                coord_values.append(cv)
        if coord_values:
            attrs["coords"] = AttributeValue(floats=coord_values)
        nodes.append(ModelNode(
            id=_attr_str(cluster, "id", f"cluster_{len(nodes)}"),
            op_type=OpType.CLUSTERING,
            name=_attr_str(cluster, "name", ""),
            attributes=attrs,
        ))

    return ModelGraph(
        name=_attr_str(elem, "modelName", "clustering"),
        nodes=nodes,
        metadata={
            "comparison_measure": _parse_comparison_measure(elem),
            "clustering_fields": _parse_clustering_fields(elem),
        },
    )


def _parse_comparison_measure(elem: ET.Element) -> dict[str, Any]:
    cm = _find(elem, "ComparisonMeasure")
    if cm is None:
        return {}
    kind = _attr_str(cm, "kind", "distance")
    measure = _find(cm, "euclidian") or _find(cm, "squaredEuclidian") or \
              _find(cm, "chebychev") or _find(cm, "cityBlock") or \
              _find(cm, "minkowski") or _find(cm, "simpleMatching") or \
              _find(cm, "jaccard") or _find(cm, "tanimoto") or \
              _find(cm, "binarySimilarity")
    measure_kind = measure.tag.split("}")[-1] if measure is not None else "euclidian"
    return {"kind": kind, "measure": measure_kind}


def _parse_clustering_fields(elem: ET.Element) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for cf in _iter(elem, "ClusteringField"):
        fields.append({
            "field": _attr_str(cf, "field"),
            "compare_function": _attr_opt(cf, "compareFunction"),
            "is_center_field": _attr_opt(cf, "isCenterField"),
        })
    return fields


def _parse_mining_model_multi(elem: ET.Element, model_graphs: dict[str, ModelGraph]) -> ModelGraph:
    segmentation = _find(elem, "Segmentation")
    if segmentation is None:
        return ModelGraph(name=_attr_str(elem, "modelName", "mining"))
    mm_method = _attr_str(segmentation, "multipleModelMethod", "majorityVote")
    nodes: list[ModelNode] = []
    for seg in _iter(segmentation, "Segment"):
        seg_id = _attr_str(seg, "id", str(len(nodes)))
        inner_model = _find_model_element(seg)
        if inner_model is not None:
            inner_graph = _route_parse(inner_model)
            inner_weight = _attr_float(seg, "weight")
            nodes.append(ModelNode(
                id=f"segment_{seg_id}",
                op_type=OpType.ENSEMBLE,
                name=_attr_str(seg, "name", f"segment_{seg_id}"),
                sub_graph=inner_graph,
                weight=inner_weight,
            ))
    return ModelGraph(
        name=_attr_str(elem, "modelName", "ensemble"),
        nodes=nodes,
        metadata={"multiple_model_method": mm_method},
    )


def _find_model_element(elem: ET.Element) -> ET.Element | None:
    model_tags = [
        "TreeModel", "RegressionModel", "ClusteringModel",
        "SupportVectorMachineModel", "NaiveBayesModel", "AssociationModel",
        "GeneralRegressionModel", "TimeSeriesModel", "RuleSetModel",
        "Scorecard", "BaselineModel", "NeuralNetwork",
    ]
    for tag in model_tags:
        found = _find(elem, tag)
        if found is not None:
            return found
    return None


def _route_parse(elem: ET.Element) -> ModelGraph:
    tag = elem.tag.split("}")[-1]
    if tag == "TreeModel":
        return _parse_tree_model(elem)
    elif tag == "RegressionModel":
        return _parse_regression_model(elem)
    elif tag == "ClusteringModel":
        return _parse_clustering_model(elem)
    elif tag == "MiningModel":
        return _parse_mining_model_multi(elem, {})
    return ModelGraph(name=_attr_str(elem, "modelName", "unknown"))


def _parse_tree_model(elem: ET.Element) -> ModelGraph:
    nodes = _children(elem, "Node")
    if not nodes:
        return ModelGraph(name=_attr_str(elem, "modelName", "tree"))
    root_node = _parse_node(nodes[0])
    return ModelGraph(
        name=_attr_str(elem, "modelName", "tree"),
        nodes=[root_node],
        metadata={"split_characteristic": _attr_str(elem, "splitCharacteristic", "binarySplit")},
    )


def _guess_model_type(elem: ET.Element) -> MiningModelType:
    tag = elem.tag.split("}")[-1]
    tag_map: dict[str, MiningModelType] = {
        "TreeModel": MiningModelType.DECISION_TREE,
        "RegressionModel": MiningModelType.REGRESSION,
        "ClusteringModel": MiningModelType.CLUSTERING,
        "SupportVectorMachineModel": MiningModelType.SVM,
        "NaiveBayesModel": MiningModelType.NAIVE_BAYES,
        "NeuralNetwork": MiningModelType.NEURAL_NETWORK,
        "AssociationModel": MiningModelType.ASSOCIATION_RULES,
        "SequenceModel": MiningModelType.SEQUENCE_CLUSTERING,
        "TimeSeriesModel": MiningModelType.TIME_SERIES,
        "Scorecard": MiningModelType.REGRESSION,
    }
    if tag == "MiningModel":
        model_type_str = _attr_str(elem, "modelType", "decisionTree").lower().replace("-", "_").replace(" ", "_")
        try:
            return MiningModelType(model_type_str)
        except ValueError:
            pass
        if _find(elem, "Segmentation") is not None:
            return MiningModelType.DECISION_TREE
    return tag_map.get(tag, MiningModelType.DECISION_TREE)


def _parse_pmml(root: ET.Element, name: str, doc_id: str) -> MlMiningDocument:
    header_meta = _parse_header(root)
    dd_map = _parse_data_dictionary(root)
    model_elem: ET.Element | None = None
    for tag in [
        "TreeModel", "RegressionModel", "ClusteringModel",
        "MiningModel", "SupportVectorMachineModel", "NaiveBayesModel",
        "NeuralNetwork", "AssociationModel", "TimeSeriesModel",
    ]:
        model_elem = _find(root, tag)
        if model_elem is not None:
            break

    model_type = MiningModelType.DECISION_TREE
    model_graph: ModelGraph | None = None
    mining_schema: MiningSchema | None = None
    targets: list[dict[str, Any]] = []
    outputs: list[ModelResult] = []
    feature_names: list[str] = []
    target_name: str | None = None

    if model_elem is not None:
        model_type = _guess_model_type(model_elem)
        model_graph = _route_parse(model_elem)
        mining_schema = _parse_mining_schema(model_elem)
        targets = _parse_targets(model_elem)
        outputs = _parse_outputs(model_elem)

        if mining_schema:
            for mf in mining_schema.fields:
                if mf.usage_type in (FieldUsageType.ACTIVE, FieldUsageType.SUPPLEMENTARY):
                    feature_names.append(mf.name)
                elif mf.usage_type == FieldUsageType.PREDICTED:
                    target_name = mf.name
            _default_dtype = DataType(base=ScalarType.STRING)
            features = [
                MsdmAttribute(name=f, data_type=dd_map.get(f, _default_dtype))
                for f in feature_names
            ]
            target = MsdmAttribute(
                name=target_name,
                data_type=dd_map.get(target_name, _default_dtype),
            ) if target_name else None
        else:
            features = []
            target = None
    else:
        features = []
        target = None

    model_title = _attr_str(model_elem, "modelName", name) if model_elem is not None else name
    return MlMiningDocument(
        title=model_title,
        document_id=doc_id,
        model_type=model_type,
        model_format=ModelFormat.PMML,
        features=features,
        target=target,
        model_data=ET.tostring(root, encoding="unicode").encode("utf-8"),
        mining_schema=mining_schema,
        model_graph=model_graph,
        results=outputs,
        metrics=[],
        vendor_extensions={**header_meta, "targets": targets},
        media_type=MEDIA_TYPES["pmml_xml"],
    )


class PmmlParser(BaseDocumentParser):
    name = "pmml"
    supported_extensions = (".pmml",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                          metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> MlMiningDocument:
        text = data.decode("utf-8", errors="replace")
        return self._parse_text(text, source_name, document_id)

    async def parse_path(self, path: str | Path, document_id: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> MlMiningDocument:
        file_path = Path(path)
        data = file_path.read_bytes()
        return await self.parse_bytes(data, document_id, file_path.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str,
                           source_name: str, metadata: dict[str, Any] | None = None,
                           options: ParseOptions | None = None) -> MlMiningDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith((".pmml", ".pmml.xml")):
            return True
        try:
            data = Path(source).read_bytes()[:500] if Path(source).exists() else b""
            return b"<PMML" in data
        except Exception:
            return False

    def _parse_text(self, text: str, name: str, doc_id: str) -> MlMiningDocument:
        root = ET.fromstring(text)
        return _parse_pmml(root, name, doc_id)
