from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from engines.document.models.ksdm_models import ModelGraph, ModelNode, OpType
from engines.knowledge.ml_mining.converters import ConverterRegistry, ModelGraphConverter


def _flatten_tree(graph: ModelGraph, depth: int = 0) -> Iterator[tuple[ModelNode, int]]:
    for node in graph.nodes:
        yield node, depth
        if node.sub_graph is not None:
            yield from _flatten_tree(node.sub_graph, depth + 1)


def _collect_tree_nodes(graph: ModelGraph) -> list[tuple[ModelNode, int]]:
    return list(_flatten_tree(graph))


def _is_treelike(graph: ModelGraph) -> bool:
    has_tree = False
    has_leaf = False
    for node, _depth in _flatten_tree(graph):
        if node.op_type in (OpType.TREE, OpType.TREE_SPLIT):
            has_tree = True
        elif node.op_type == OpType.LEAF:
            has_leaf = True
    return has_tree and has_leaf


def _is_ensemble(graph: ModelGraph) -> bool:
    ensemble_types = {OpType.RANDOM_FOREST, OpType.GRADIENT_BOOSTED_TREES, OpType.ENSEMBLE}
    for node, _depth in _flatten_tree(graph):
        if node.op_type in ensemble_types:
            return True
    return False


def _collect_all_trees(graph: ModelGraph) -> list[list[tuple[ModelNode, int]]]:
    trees: list[list[tuple[ModelNode, int]]] = []
    for node in graph.nodes:
        if node.op_type in (OpType.RANDOM_FOREST, OpType.GRADIENT_BOOSTED_TREES, OpType.ENSEMBLE):
            if node.sub_graph:
                for sub_node in node.sub_graph.nodes:
                    if sub_node.sub_graph:
                        tree_nodes = _collect_tree_nodes(sub_node.sub_graph)
                        if tree_nodes:
                            trees.append(tree_nodes)
                all_nodes = _collect_tree_nodes(node.sub_graph)
                if not trees and all_nodes:
                    trees.append(all_nodes)
        elif node.op_type in (OpType.TREE, OpType.TREE_SPLIT, OpType.LEAF):
            tree = _collect_tree_nodes(graph)
            if tree:
                trees.append(tree)
    return trees


@ConverterRegistry.register
class TreeConverter(ModelGraphConverter):
    def can_convert(self, graph: Any) -> bool:
        if not isinstance(graph, ModelGraph):
            return False
        return _is_treelike(graph) or _is_ensemble(graph)

    def convert(self, graph: Any) -> bytes:
        import onnx
        from onnx import helper, TensorProto

        trees = _collect_all_trees(graph)

        if not trees:
            raise ValueError("No tree structures found in graph")

        has_classification = any(
            node.attributes.get("score_dist_values") is not None
            for tree_nodes in trees
            for node, _depth in tree_nodes
        )

        is_clf = has_classification

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

        n_classes = 0
        all_class_labels: list[int] = []

        nid_offset = 0
        for tree_idx, tree_nodes in enumerate(trees):
            node_map: dict[str, int] = {}
            onnx_nid = 0

            for node, depth in tree_nodes:
                node_map[node.id] = onnx_nid
                onnx_nid += 1

            for node, depth in tree_nodes:
                all_tree_ids.append(tree_idx)
                nid = node_map[node.id]
                all_node_ids.append(nid)

                if node.op_type == OpType.LEAF:
                    all_modes.append("LEAF")
                    all_values.append(0.0)
                    all_true_child.append(nid)
                    all_false_child.append(nid)
                    all_missing_tracks_true.append(0)
                    all_feature_ids.append(0)

                    score_dist = node.attributes.get("score_dist_values")
                    score_counts = node.attributes.get("score_dist_counts")
                    if score_dist and score_counts:
                        values = score_dist.strings
                        counts = score_counts.floats
                        for i, val in enumerate(values):
                            class_tree_ids.append(tree_idx)
                            class_node_ids.append(nid)
                            try:
                                class_ids_list.append(int(val))
                            except ValueError:
                                class_ids_list.append(i)
                            weight = counts[i] if i < len(counts) else 0.0
                            class_weights.append(float(weight))
                            n_classes = max(n_classes, class_ids_list[-1] + 1)
                            if int(val) not in all_class_labels:
                                all_class_labels.append(int(val))
                    else:
                        score_val = node.attributes.get("score")
                        if score_val and score_val.float_value is not None:
                            class_tree_ids.append(tree_idx)
                            class_node_ids.append(nid)
                            class_ids_list.append(0)
                            class_weights.append(float(score_val.float_value))
                            n_classes = max(n_classes, 1)
                else:
                    predicate = node.attributes.get("predicate")
                    threshold_attr = node.attributes.get("threshold")
                    feat_idx_attr = node.attributes.get("feature_index")

                    if threshold_attr and threshold_attr.float_value is not None:
                        thr = threshold_attr.float_value
                    elif predicate and predicate.string_value:
                        parts = predicate.string_value.split(" <= ")
                        thr = float(parts[1]) if len(parts) == 2 else 0.0
                    else:
                        thr = 0.0

                    feat = int(feat_idx_attr.int_value) if feat_idx_attr and feat_idx_attr.int_value is not None else 0

                    all_modes.append("BRANCH_LEQ")
                    all_values.append(float(thr))
                    all_feature_ids.append(feat)

                    left_child = -1
                    right_child = -1
                    if node.sub_graph:
                        for cn in node.sub_graph.nodes:
                            cid = node_map.get(cn.id)
                            if cid is not None and cid > nid:
                                if left_child == -1 or cid < left_child:
                                    right_child = left_child
                                    left_child = cid
                                elif right_child == -1 or cid < right_child:
                                    right_child = cid
                    if left_child == -1:
                        for cn2, _cd2 in tree_nodes:
                            cid2 = node_map.get(cn2.id)
                            if cid2 is not None and cid2 > nid:
                                if left_child == -1 or cid2 < left_child:
                                    right_child = left_child
                                    left_child = cid2
                                elif right_child == -1 or cid2 < right_child:
                                    right_child = cid2

                    all_true_child.append(left_child if left_child != -1 else nid)
                    all_false_child.append(right_child if right_child != -1 else nid)
                    all_missing_tracks_true.append(1)

            nid_offset += onnx_nid

        if is_clf and not class_tree_ids:
            default_class = len(all_class_labels) if all_class_labels else 2
            n_classes = default_class if default_class >= 2 else 2
            for tree_idx in range(len(trees)):
                for i in range(n_classes):
                    class_tree_ids.append(tree_idx)
                    class_node_ids.append(0)
                    class_ids_list.append(i)
                    class_weights.append(1.0 if i == 0 else 0.0)

        n_features = max(len(graph.inputs), 1)
        if not n_features and all_feature_ids:
            n_features = max(all_feature_ids) + 1

        attr: dict[str, Any] = {}
        if is_clf:
            if not all_class_labels:
                all_class_labels = list(range(n_classes))
            attr = {
                "nodes_treeids": all_tree_ids,
                "nodes_nodeids": all_node_ids,
                "nodes_featureids": all_feature_ids,
                "nodes_modes": all_modes,
                "nodes_values": [float(v) for v in all_values],
                "nodes_truenodeids": all_true_child,
                "nodes_falsenodeids": all_false_child,
                "nodes_missing_value_tracks_true": all_missing_tracks_true,
                "class_treeids": class_tree_ids,
                "class_nodeids": class_node_ids,
                "class_ids": class_ids_list,
                "class_weights": class_weights,
                "classlabels_int64s": all_class_labels,
            }

            tree_node = helper.make_node(
                "TreeEnsembleClassifier", ["X"], ["label", "probabilities"],
                name="tree_ensemble", domain="ai.onnx.ml", **attr,
            )

            X_type = TensorProto.FLOAT

            graph_def = helper.make_graph(
                [tree_node], "tree_graph",
                [helper.make_tensor_value_info("X", X_type, [None, n_features])],
                [
                    helper.make_tensor_value_info("label", TensorProto.INT64, [None]),
                    helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, [None, n_classes]),
                ],
            )
        else:
            attr = {
                "nodes_treeids": all_tree_ids,
                "nodes_nodeids": all_node_ids,
                "nodes_featureids": all_feature_ids,
                "nodes_modes": all_modes,
                "nodes_values": [float(v) for v in all_values],
                "nodes_truenodeids": all_true_child,
                "nodes_falsenodeids": all_false_child,
                "nodes_missing_value_tracks_true": all_missing_tracks_true,
                "n_targets": 1,
                "aggregate_function": "SUM",
            }
            tree_node = helper.make_node(
                "TreeEnsembleRegressor", ["X"], ["Y"],
                name="tree_ensemble", domain="ai.onnx.ml", **attr,
            )

            graph_def = helper.make_graph(
                [tree_node], "tree_graph",
                [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, n_features])],
                [helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None])],
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
