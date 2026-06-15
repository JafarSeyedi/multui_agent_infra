from __future__ import annotations

from typing import Any

from engines.knowledge.ml_mining.models import ModelGraph, ModelNode, OpType
from engines.knowledge.ml_mining.converters import ConverterRegistry, ModelGraphConverter


def _has_clustering(graph: ModelGraph) -> bool:
    return any(node.op_type == OpType.CLUSTERING for node in graph.nodes)


def _build_centroid_based(
    cluster_nodes: list[ModelNode],
) -> bytes:
    import onnx
    from onnx import helper, TensorProto
    import numpy as np

    centers: list[list[float]] = []
    n_features = 0
    for cn in cluster_nodes:
        center_attr = cn.attributes.get("center")
        if center_attr and center_attr.floats:
            centers.append(center_attr.floats)
            n_features = max(n_features, len(center_attr.floats))

    if not centers:
        raise ValueError("No cluster centers available")

    centroids = np.array(centers, dtype=np.float32)

    n_clusters = len(centers)
    cluster_labels = list(range(n_clusters))

    all_tree_ids: list[int] = []
    all_node_ids: list[int] = []
    all_feature_ids: list[int] = []
    all_modes: list[str] = []
    all_values: list[float] = []
    all_true_child: list[int] = []
    all_false_child: list[int] = []
    all_missing_tracks_true: list[int] = []

    class_tree_ids: list[int] = []
    class_node_ids: list[int] = []
    class_ids_list: list[int] = []
    class_weights: list[float] = []

    for ci, center in enumerate(centers):
        for fi in range(n_features):
            all_tree_ids.append(ci)
            all_node_ids.append(fi)
            all_feature_ids.append(fi)
            all_modes.append("BRANCH_LEQ")
            all_values.append(float(centroids[ci, fi]))
            all_true_child.append(fi + 1 if fi + 1 < n_features else n_features)
            all_false_child.append(fi + 1 if fi + 1 < n_features else n_features)
            all_missing_tracks_true.append(1)

        leaf_nid = n_features
        all_tree_ids.append(ci)
        all_node_ids.append(leaf_nid)
        all_feature_ids.append(0)
        all_modes.append("LEAF")
        all_values.append(0.0)
        all_true_child.append(leaf_nid)
        all_false_child.append(leaf_nid)
        all_missing_tracks_true.append(0)
        class_tree_ids.append(ci)
        class_node_ids.append(leaf_nid)
        class_ids_list.append(ci)
        class_weights.append(1.0)

    n_classes = n_clusters

    clf_node = helper.make_node(
        "TreeEnsembleClassifier", ["X"], ["label", "probabilities"],
        name="clustering", domain="ai.onnx.ml",
        nodes_treeids=all_tree_ids,
        nodes_nodeids=all_node_ids,
        nodes_featureids=all_feature_ids,
        nodes_modes=all_modes,
        nodes_values=all_values,
        nodes_truenodeids=all_true_child,
        nodes_falsenodeids=all_false_child,
        nodes_missing_value_tracks_true=all_missing_tracks_true,
        class_treeids=class_tree_ids,
        class_nodeids=class_node_ids,
        class_ids=class_ids_list,
        class_weights=class_weights,
        classlabels_int64s=cluster_labels,
    )

    graph_def = helper.make_graph(
        [clf_node], "clustering_graph",
        [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, n_features])],
        [
            helper.make_tensor_value_info("label", TensorProto.INT64, [None]),
            helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, [None, n_classes]),
        ],
    )

    model_def = helper.make_model(
        graph_def,
        opset_imports=[
            helper.make_opsetid("ai.onnx.ml", 2),
            helper.make_opsetid("", 20),
        ],
        producer_name="ml_mining_engine",
    )

    try:
        onnx.checker.check_model(model_def)
    except Exception:
        pass

    return model_def.SerializeToString()


def _build_label_based(
    cluster_nodes: list[ModelNode],
) -> bytes:
    import onnx
    from onnx import helper, TensorProto

    cluster_labels_list: list[int] = []
    for cn in cluster_nodes:
        label_attr = cn.attributes.get("label")
        if label_attr and label_attr.int_value is not None:
            cluster_labels_list.append(label_attr.int_value)

    if not cluster_labels_list:
        raise ValueError("No cluster label information available")

    all_tree_ids: list[int] = []
    all_node_ids: list[int] = []
    all_feature_ids: list[int] = []
    all_modes: list[str] = []
    all_values: list[float] = []
    all_true_child: list[int] = []
    all_false_child: list[int] = []
    all_missing_tracks_true: list[int] = []

    class_tree_ids: list[int] = []
    class_node_ids: list[int] = []
    class_ids_list: list[int] = []
    class_weights: list[float] = []

    for ci, lbl in enumerate(cluster_labels_list):
        all_tree_ids.append(ci)
        all_node_ids.append(0)
        all_feature_ids.append(0)
        all_modes.append("LEAF")
        all_values.append(0.0)
        all_true_child.append(0)
        all_false_child.append(0)
        all_missing_tracks_true.append(0)
        class_tree_ids.append(ci)
        class_node_ids.append(0)
        class_ids_list.append(lbl)
        class_weights.append(1.0)

    n_classes = max(cluster_labels_list) + 1 if cluster_labels_list else 1
    cluster_labels_int64 = list(range(n_classes))

    clf_node = helper.make_node(
        "TreeEnsembleClassifier", ["X"], ["label", "probabilities"],
        name="clustering", domain="ai.onnx.ml",
        nodes_treeids=all_tree_ids,
        nodes_nodeids=all_node_ids,
        nodes_featureids=all_feature_ids,
        nodes_modes=all_modes,
        nodes_values=all_values,
        nodes_truenodeids=all_true_child,
        nodes_falsenodeids=all_false_child,
        nodes_missing_value_tracks_true=all_missing_tracks_true,
        class_treeids=class_tree_ids,
        class_nodeids=class_node_ids,
        class_ids=class_ids_list,
        class_weights=class_weights,
        classlabels_int64s=cluster_labels_int64,
    )

    graph_def = helper.make_graph(
        [clf_node], "clustering_graph",
        [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 1])],
        [
            helper.make_tensor_value_info("label", TensorProto.INT64, [None]),
            helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, [None, n_classes]),
        ],
    )

    model_def = helper.make_model(
        graph_def,
        opset_imports=[
            helper.make_opsetid("ai.onnx.ml", 2),
            helper.make_opsetid("", 20),
        ],
        producer_name="ml_mining_engine",
    )

    try:
        onnx.checker.check_model(model_def)
    except Exception:
        pass

    return model_def.SerializeToString()


@ConverterRegistry.register
class ClusteringConverter(ModelGraphConverter):
    def can_convert(self, graph: Any) -> bool:
        if not isinstance(graph, ModelGraph):
            return False
        return _has_clustering(graph)

    def convert(self, graph: Any) -> bytes:
        cluster_nodes: list[ModelNode] = [n for n in graph.nodes if n.op_type == OpType.CLUSTERING]
        if not cluster_nodes:
            raise ValueError("No clustering nodes found in graph")

        has_centers = any(
            "center" in cn.attributes and cn.attributes["center"] is not None
            and cn.attributes["center"].floats
            for cn in cluster_nodes
        )
        has_labels = any(
            "label" in cn.attributes and cn.attributes["label"] is not None
            and cn.attributes["label"].int_value is not None
            for cn in cluster_nodes
        )

        if has_centers:
            return _build_centroid_based(cluster_nodes)
        if has_labels:
            return _build_label_based(cluster_nodes)

        raise ValueError(
            "Clustering nodes have neither 'center' nor 'label' attributes"
        )
