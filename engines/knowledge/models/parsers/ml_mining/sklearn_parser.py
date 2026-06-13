from __future__ import annotations

import io
import pickle
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.knowledge.models.ksdm_models import (
    AttributeValue,
    FeatureImportance,
    FieldUsageType,
    MiningField,
    MiningModelType,
    MiningSchema,
    ModelFormat,
    ModelGraph,
    ModelNode,
    ModelParameter,
    MlMiningDocument,
    OpType,
    ParameterName,
    Port,
    TrainingConfig,
    TrainingTask,
)
from engines.document.models.msdm_models import Attribute as MsdmAttribute, DataType, ScalarType
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.parsers.base import BaseDocumentParser, ParseOptions

_SKLEARN_TYPE_MAP: dict[str, MiningModelType] = {
    "DecisionTreeClassifier": MiningModelType.DECISION_TREE,
    "DecisionTreeRegressor": MiningModelType.DECISION_TREE,
    "RandomForestClassifier": MiningModelType.DECISION_TREE,
    "RandomForestRegressor": MiningModelType.DECISION_TREE,
    "GradientBoostingClassifier": MiningModelType.DECISION_TREE,
    "GradientBoostingRegressor": MiningModelType.DECISION_TREE,
    "HistGradientBoostingClassifier": MiningModelType.DECISION_TREE,
    "HistGradientBoostingRegressor": MiningModelType.DECISION_TREE,
    "ExtraTreesClassifier": MiningModelType.DECISION_TREE,
    "ExtraTreesRegressor": MiningModelType.DECISION_TREE,
    "LogisticRegression": MiningModelType.REGRESSION,
    "LinearRegression": MiningModelType.REGRESSION,
    "Ridge": MiningModelType.REGRESSION,
    "Lasso": MiningModelType.REGRESSION,
    "ElasticNet": MiningModelType.REGRESSION,
    "LinearSVC": MiningModelType.SVM,
    "LinearSVR": MiningModelType.SVM,
    "SVC": MiningModelType.SVM,
    "SVR": MiningModelType.SVM,
    "NuSVC": MiningModelType.SVM,
    "NuSVR": MiningModelType.SVM,
    "KMeans": MiningModelType.CLUSTERING,
    "MiniBatchKMeans": MiningModelType.CLUSTERING,
    "DBSCAN": MiningModelType.CLUSTERING,
    "AgglomerativeClustering": MiningModelType.CLUSTERING,
    "GaussianMixture": MiningModelType.CLUSTERING,
    "SpectralClustering": MiningModelType.CLUSTERING,
    "Birch": MiningModelType.CLUSTERING,
    "OPTICS": MiningModelType.CLUSTERING,
    "GaussianNB": MiningModelType.NAIVE_BAYES,
    "MultinomialNB": MiningModelType.NAIVE_BAYES,
    "BernoulliNB": MiningModelType.NAIVE_BAYES,
    "ComplementNB": MiningModelType.NAIVE_BAYES,
    "CategoricalNB": MiningModelType.NAIVE_BAYES,
    "MLPClassifier": MiningModelType.NEURAL_NETWORK,
    "MLPRegressor": MiningModelType.NEURAL_NETWORK,
    "GaussianProcessClassifier": MiningModelType.GAUSSIAN_PROCESS,
    "GaussianProcessRegressor": MiningModelType.GAUSSIAN_PROCESS,
}

_TASK_MAP: dict[str, TrainingTask] = {
    "Classifier": TrainingTask.CLASSIFICATION,
    "Regressor": TrainingTask.REGRESSION,
    "Cluster": TrainingTask.CLUSTERING,
}

_PARAM_MAP: dict[str, ParameterName] = {
    "max_depth": ParameterName.MAX_DEPTH,
    "n_estimators": ParameterName.N_ESTIMATORS,
    "learning_rate": ParameterName.LEARNING_RATE,
    "max_iter": ParameterName.MAX_ITER,
    "C": ParameterName.C_SVM,
    "gamma": ParameterName.GAMMA,
    "kernel": ParameterName.KERNEL,
    "tol": ParameterName.TOL,
    "random_state": ParameterName.RANDOM_STATE,
}


def _detect_task(model: Any) -> TrainingTask:
    name = type(model).__name__
    for suffix, task in _TASK_MAP.items():
        if suffix in name:
            return task
    return TrainingTask.CLASSIFICATION


def _is_classifier(model: Any) -> bool:
    return hasattr(model, "predict_proba") or "Classifier" in type(model).__name__


def _build_tree_graph(tree_model: Any, node_id_prefix: str = "",
                      feature_names: list[str] | None = None) -> list[ModelNode]:
    tree = tree_model.tree_
    children_left = tree.children_left
    children_right = tree.children_right
    feature = tree.feature
    threshold = tree.threshold
    values = tree.value

    nodes: list[ModelNode] = []
    node_stack: list[int] = [0]

    while node_stack:
        nid = node_stack.pop()
        nid_str = f"{node_id_prefix}n{nid}"
        is_leaf = children_left[nid] == -1 and children_right[nid] == -1

        attrs: dict[str, AttributeValue] = {}

        if is_leaf:
            leaf_value = values[nid]
            if leaf_value.shape[1] == 1:
                attrs["score"] = AttributeValue(float_value=float(leaf_value[0, 0]))
            else:
                score_values = [str(i) for i in range(leaf_value.shape[1])]
                score_counts = [float(leaf_value[0, i]) for i in range(leaf_value.shape[1])]
                attrs["score_dist_values"] = AttributeValue(strings=score_values)
                attrs["score_dist_counts"] = AttributeValue(floats=score_counts)
            op_type = OpType.LEAF
        else:
            feat_idx = feature[nid]
            feat_name = feature_names[feat_idx] if feature_names and feat_idx < len(feature_names) else f"f{feat_idx}"
            attrs["predicate"] = AttributeValue(
                string_value=f"{feat_name} <= {threshold[nid]:.6f}"
            )
            attrs["feature_index"] = AttributeValue(int_value=int(feat_idx))
            attrs["threshold"] = AttributeValue(float_value=float(threshold[nid]))
            op_type = OpType.TREE_SPLIT

        node = ModelNode(id=nid_str, op_type=op_type, attributes=attrs)
        nodes.append(node)

        if children_left[nid] != -1:
            node_stack.append(children_left[nid])
        if children_right[nid] != -1:
            node_stack.append(children_right[nid])

    return nodes


def _extract_feature_importances(model: Any) -> list[FeatureImportance]:
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        names = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else None
        result: list[FeatureImportance] = []
        for i, imp in enumerate(importances):
            fname = str(names[i]) if names else f"f{i}"
            result.append(FeatureImportance(feature_name=fname, importance=float(imp)))
        return result
    if hasattr(model, "coef_"):
        coefs = model.coef_
        names = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else None
        result = []
        flat = coefs.flatten()
        for i, c in enumerate(flat):
            fname = str(names[i]) if names else f"f{i}"
            result.append(FeatureImportance(feature_name=fname, importance=float(abs(c))))
        return result
    return []


def _extract_params(model: Any) -> list[ModelParameter]:
    params: list[ModelParameter] = []
    if hasattr(model, "get_params"):
        for key, value in model.get_params().items():
            pname = _PARAM_MAP.get(key)
            if pname and value is not None and isinstance(value, (int, float, str, bool)):
                params.append(ModelParameter(name=pname, value=value))
    return params


class SklearnParser(BaseDocumentParser):
    name = "sklearn"
    supported_extensions = (".pkl", ".joblib", ".pickle")

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                          metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> MlMiningDocument:
        return self._parse_data(data, source_name, document_id)

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
        if isinstance(source, str) and source.endswith((".pkl", ".joblib", ".pickle")):
            return True
        try:
            data = Path(source).read_bytes()[:10] if Path(source).exists() else b""
            return data[:4] in (b"\x80\x04", b"\x80\x05", b"\x80\x03", b"\x80\x02", b"\x80\x01")
        except Exception:
            return False

    def _parse_data(self, data: bytes, name: str, doc_id: str) -> MlMiningDocument:
        model = self._load_model(data)
        model_cls_name = type(model).__name__

        model_type = _SKLEARN_TYPE_MAP.get(model_cls_name, MiningModelType.OTHER)

        feature_names: list[str] | None = None
        if hasattr(model, "feature_names_in_"):
            feature_names = list(model.feature_names_in_)
        elif hasattr(model, "n_features_in_"):
            feature_names = [f"f{i}" for i in range(model.n_features_in_)]

        features: list[MsdmAttribute] = []
        if feature_names:
            for fn in feature_names:
                features.append(MsdmAttribute(name=fn, data_type=DataType(base=ScalarType.DOUBLE)))

        target: MsdmAttribute | None = None
        if _is_classifier(model) and hasattr(model, "classes_"):
            target = MsdmAttribute(name="target", data_type=DataType(base=ScalarType.STRING))

        training_task = _detect_task(model)
        params = _extract_params(model)
        importances = _extract_feature_importances(model)

        model_graph = self._build_graph(model, feature_names)

        mining_schema: MiningSchema | None = None
        if feature_names:
            fields = [MiningField(name=fn, usage_type=FieldUsageType.ACTIVE) for fn in feature_names]
            if target:
                fields.append(MiningField(name="target", usage_type=FieldUsageType.PREDICTED))
            mining_schema = MiningSchema(fields=fields)

        return MlMiningDocument(
            title=name,
            document_id=doc_id,
            model_type=model_type,
            model_format=ModelFormat.SKLEARN,
            features=features,
            target=target,
            parameters=params,
            feature_importances=importances,
            training_config=TrainingConfig(task=training_task),
            model_graph=model_graph,
            mining_schema=mining_schema,
            model_data=data,
            media_type=MEDIA_TYPES.get("pickle_protobuf", MEDIA_TYPES["onnx_protobuf"]),
        )

    def _load_model(self, data: bytes) -> Any:
        try:
            return pickle.loads(data)
        except Exception:
            pass
        try:
            import joblib  # type: ignore[import-untyped]
            return joblib.load(io.BytesIO(data))
        except Exception:
            pass
        raise ValueError("Could not load sklearn model from bytes")

    def _build_graph(self, model: Any,
                     feature_names: list[str] | None = None) -> ModelGraph | None:
        model_cls_name = type(model).__name__
        nodes: list[ModelNode] = []

        if "Pipeline" in model_cls_name and hasattr(model, "steps"):
            nodes = self._build_pipeline_graph(model)
        elif hasattr(model, "estimators_") and "Gradient" not in model_cls_name:
            nodes = self._build_ensemble_graph(model, feature_names)
        elif hasattr(model, "estimators_") and "Gradient" in model_cls_name:
            nodes = self._build_gb_graph(model, feature_names)
        elif hasattr(model, "tree_"):
            nodes = _build_tree_graph(model, feature_names=feature_names)
        elif hasattr(model, "coef_") or hasattr(model, "intercept_"):
            nodes = self._build_linear_graph(model, feature_names)
        elif "SVC" in model_cls_name or "SVR" in model_cls_name:
            nodes = self._build_svm_graph(model, feature_names)
        elif _SKLEARN_TYPE_MAP.get(model_cls_name) == MiningModelType.CLUSTERING:
            nodes = self._build_clustering_graph(model, feature_names)
        elif "NB" in model_cls_name or "Bayes" in model_cls_name:
            nodes = self._build_naive_bayes_graph(model, feature_names)
        elif "MLP" in model_cls_name:
            nodes = self._build_mlp_graph(model, feature_names)
        else:
            nodes = self._build_generic_graph(model, feature_names)

        if not nodes:
            return None

        input_ports: list[Port] = []
        output_ports: list[Port] = []
        if feature_names:
            input_ports = [Port(name=fn) for fn in feature_names]

        return ModelGraph(
            name=model_cls_name,
            nodes=nodes,
            inputs=input_ports,
            outputs=output_ports,
        )

    def _build_pipeline_graph(self, pipeline: Any) -> list[ModelNode]:
        nodes: list[ModelNode] = []
        for step_name, step_model in pipeline.steps:
            step_graph = self._build_graph(step_model)
            if step_graph and step_graph.nodes:
                nodes.append(ModelNode(
                    id=step_name,
                    op_type=OpType.TRANSFORMER,
                    name=step_name,
                    sub_graph=step_graph,
                ))
        return nodes

    def _build_ensemble_graph(self, model: Any,
                               feature_names: list[str] | None = None) -> list[ModelNode]:
        tree_nodes: list[ModelNode] = []
        if hasattr(model, "estimators_"):
            for i, est in enumerate(model.estimators_):
                if est is None:
                    continue
                subtree = _build_tree_graph(est, f"t{i}_", feature_names)
                if subtree:
                    tree_nodes.append(ModelNode(
                        id=f"tree_{i}",
                        op_type=OpType.TREE,
                        name=f"estimator_{i}",
                        sub_graph=ModelGraph(nodes=subtree),
                    ))

        return [ModelNode(
            id="ensemble_root",
            op_type=OpType.RANDOM_FOREST,
            name=type(model).__name__,
            sub_graph=ModelGraph(nodes=tree_nodes) if tree_nodes else None,
        )]

    def _build_gb_graph(self, model: Any,
                         feature_names: list[str] | None = None) -> list[ModelNode]:
        tree_nodes: list[ModelNode] = []
        if hasattr(model, "estimators_"):
            for stage_idx, stage in enumerate(model.estimators_):
                for class_idx, est in enumerate(stage):
                    if est is None:
                        continue
                    subtree = _build_tree_graph(est, f"s{stage_idx}_c{class_idx}_", feature_names)
                    if subtree:
                        tree_nodes.append(ModelNode(
                            id=f"stage_{stage_idx}_class_{class_idx}",
                            op_type=OpType.TREE,
                            name=f"stage_{stage_idx}_class_{class_idx}",
                            sub_graph=ModelGraph(nodes=subtree),
                        ))
        return [ModelNode(
            id="gb_root",
            op_type=OpType.GRADIENT_BOOSTED_TREES,
            name=type(model).__name__,
            sub_graph=ModelGraph(nodes=tree_nodes) if tree_nodes else None,
        )]

    def _build_linear_graph(self, model: Any,
                             feature_names: list[str] | None = None) -> list[ModelNode]:
        attrs: dict[str, AttributeValue] = {}
        if hasattr(model, "coef_"):
            coef = model.coef_
            flat = coef.flatten()
            attrs["coefficients"] = AttributeValue(floats=[float(c) for c in flat])
        if hasattr(model, "intercept_"):
            intercept = model.intercept_
            flat_i = intercept.flatten()
            attrs["intercept"] = AttributeValue(floats=[float(c) for c in flat_i])

        op = OpType.LINEAR_CLASSIFIER if _is_classifier(model) else OpType.LINEAR_REGRESSOR
        return [ModelNode(
            id="linear_model",
            op_type=op,
            name=type(model).__name__,
            attributes=attrs,
        )]

    def _build_svm_graph(self, model: Any,
                          feature_names: list[str] | None = None) -> list[ModelNode]:
        attrs: dict[str, AttributeValue] = {}
        if hasattr(model, "support_vectors_"):
            sv = model.support_vectors_
            attrs["support_vectors"] = AttributeValue(floats=sv.flatten().tolist())
            attrs["n_support_vectors"] = AttributeValue(int_value=sv.shape[0])
        if hasattr(model, "dual_coef_"):
            dc = model.dual_coef_
            attrs["dual_coef"] = AttributeValue(floats=dc.flatten().tolist())
        if hasattr(model, "intercept_"):
            intercept = model.intercept_
            flat_i = intercept.flatten()
            attrs["intercept"] = AttributeValue(floats=[float(c) for c in flat_i])
        if hasattr(model, "gamma"):
            attrs["gamma"] = AttributeValue(string_value=str(model.gamma))
        if hasattr(model, "kernel"):
            attrs["kernel"] = AttributeValue(string_value=model.kernel)

        is_classifier = "SVC" in type(model).__name__
        op = OpType.SVM_CLASSIFIER if is_classifier else OpType.SVM_REGRESSOR
        return [ModelNode(
            id="svm_model",
            op_type=op,
            name=type(model).__name__,
            attributes=attrs,
        )]

    def _build_clustering_graph(self, model: Any,
                                 feature_names: list[str] | None = None) -> list[ModelNode]:
        nodes: list[ModelNode] = []
        centers: Any = None
        if hasattr(model, "cluster_centers_"):
            centers = model.cluster_centers_
        elif hasattr(model, "means_"):
            centers = model.means_
        elif hasattr(model, "subcluster_centers_"):
            centers = model.subcluster_centers_
        if centers is not None:
            for i, center in enumerate(centers):
                nid = f"cluster_{i}"
                attrs: dict[str, AttributeValue] = {
                    "center": AttributeValue(floats=[float(c) for c in center]),
                }
                if hasattr(model, "labels_"):
                    attrs["size"] = AttributeValue(int_value=int((model.labels_ == i).sum()))
                nodes.append(ModelNode(
                    id=nid,
                    op_type=OpType.CLUSTERING,
                    name=nid,
                    attributes=attrs,
                ))
        elif hasattr(model, "labels_"):
            labels = model.labels_
            unique_labels = set(labels)
            for i, lbl in enumerate(unique_labels):
                if lbl < 0:
                    continue
                nid = f"cluster_{i}"
                nodes.append(ModelNode(
                    id=nid,
                    op_type=OpType.CLUSTERING,
                    name=nid,
                    attributes={
                        "label": AttributeValue(int_value=int(lbl)),
                        "size": AttributeValue(int_value=int((labels == lbl).sum())),
                    },
                ))
        return nodes

    def _build_naive_bayes_graph(self, model: Any,
                                  feature_names: list[str] | None = None) -> list[ModelNode]:
        attrs: dict[str, AttributeValue] = {}
        if hasattr(model, "class_prior_"):
            attrs["class_prior"] = AttributeValue(floats=[float(p) for p in model.class_prior_])
        if hasattr(model, "classes_"):
            attrs["classes"] = AttributeValue(strings=[str(c) for c in model.classes_])
        return [ModelNode(
            id="naive_bayes",
            op_type=OpType.NAIVE_BAYES_MODEL,
            name=type(model).__name__,
            attributes=attrs,
        )]

    def _build_mlp_graph(self, model: Any,
                          feature_names: list[str] | None = None) -> list[ModelNode]:
        attrs: dict[str, AttributeValue] = {}
        if hasattr(model, "coefs_"):
            layer_shapes = [list(c.shape) for c in model.coefs_]
            attrs["layer_shapes"] = AttributeValue(strings=[str(s) for s in layer_shapes])
            attrs["n_layers"] = AttributeValue(int_value=len(model.coefs_))
        if hasattr(model, "hidden_layer_sizes"):
            attrs["hidden_layer_sizes"] = AttributeValue(ints=list(model.hidden_layer_sizes))
        if hasattr(model, "activation"):
            attrs["activation"] = AttributeValue(string_value=model.activation)
        return [ModelNode(
            id="mlp_model",
            op_type=OpType.NEURAL_NETWORK,
            name=type(model).__name__,
            attributes=attrs,
        )]

    def _build_generic_graph(self, model: Any,
                              feature_names: list[str] | None = None) -> list[ModelNode]:
        attrs: dict[str, AttributeValue] = {}
        if hasattr(model, "get_params"):
            for key, value in model.get_params().items():
                if value is not None and isinstance(value, (str, int, float, bool)):
                    if isinstance(value, str):
                        attrs[key] = AttributeValue(string_value=value)
                    elif isinstance(value, bool):
                        attrs[key] = AttributeValue(string_value=str(value))
                    elif isinstance(value, int):
                        attrs[key] = AttributeValue(int_value=value)
                    elif isinstance(value, float):
                        attrs[key] = AttributeValue(float_value=value)
        return [ModelNode(
            id="model",
            op_type=OpType.CUSTOM,
            name=type(model).__name__,
            attributes=attrs,
        )]
