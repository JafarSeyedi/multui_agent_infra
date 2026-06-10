from __future__ import annotations

from typing import Any

from engines.document.models.ksdm_models import ModelGraph, ModelNode, OpType
from engines.knowledge.ml_mining.converters import ConverterRegistry, ModelGraphConverter


def _has_svm(graph: ModelGraph) -> bool:
    for node in graph.nodes:
        if node.op_type in (OpType.SVM_CLASSIFIER, OpType.SVM_REGRESSOR, OpType.SVM_MODEL):
            return True
        if node.sub_graph:
            for sn in node.sub_graph.nodes:
                if sn.op_type in (OpType.SVM_CLASSIFIER, OpType.SVM_REGRESSOR, OpType.SVM_MODEL):
                    return True
    return False


def _find_svm_node(graph: ModelGraph) -> ModelNode | None:
    for node in graph.nodes:
        if node.op_type in (OpType.SVM_CLASSIFIER, OpType.SVM_REGRESSOR, OpType.SVM_MODEL):
            return node
        if node.sub_graph:
            for sn in node.sub_graph.nodes:
                if sn.op_type in (OpType.SVM_CLASSIFIER, OpType.SVM_REGRESSOR, OpType.SVM_MODEL):
                    return sn
    return None


@ConverterRegistry.register
class SVMConverter(ModelGraphConverter):
    def can_convert(self, graph: Any) -> bool:
        if not isinstance(graph, ModelGraph):
            return False
        return _has_svm(graph)

    def convert(self, graph: Any) -> bytes:
        import onnx
        from onnx import helper, TensorProto
        import numpy as np

        svm_node = _find_svm_node(graph)
        if svm_node is None:
            raise ValueError("No SVM node found in graph")

        is_classifier = svm_node.op_type == OpType.SVM_CLASSIFIER
        support_vectors = svm_node.attributes.get("support_vectors")
        dual_coef = svm_node.attributes.get("dual_coef")
        intercept = svm_node.attributes.get("intercept")
        kernel = svm_node.attributes.get("kernel")
        gamma = svm_node.attributes.get("gamma")

        if is_classifier:
            n_classes = 2
            sv_len = support_vectors.floats if support_vectors else []
            n_sv = svm_node.attributes.get("n_support_vectors")
            n_sv_val = n_sv.int_value if n_sv and n_sv.int_value else 0

            if sv_len and n_sv_val > 0:
                n_features = len(sv_len) // n_sv_val
            else:
                n_features = 1
                n_sv_val = 1

            sv = [float(v) for v in (support_vectors.floats if support_vectors else [0.0])]
            dc = [float(v) for v in (dual_coef.floats if dual_coef else [1.0])]
            itc = [float(v) for v in (intercept.floats if intercept else [0.0])]

            kernel_val = kernel.string_value if kernel and kernel.string_value else "RBF"
            gamma_val = float(gamma.string_value) if gamma and gamma.string_value else 1.0

            kernel_map = {
                "linear": "LINEAR",
                "poly": "POLY",
                "rbf": "RBF",
                "sigmoid": "SIGMOID",
            }
            onnx_kernel = kernel_map.get(kernel_val.lower(), "RBF")

            node = helper.make_node(
                "SVMClassifier", ["X"], ["label", "probabilities"],
                domain="ai.onnx.ml",
                support_vectors=sv,
                coefficients=dc,
                intercepts=itc,
                kernel_type=onnx_kernel,
                gamma=gamma_val,
                classlabels_int64s=[0, 1],
                vector_type="TRAINABLE_SVM",
            )

            graph_def = helper.make_graph(
                [node], "svm_graph",
                [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, n_features])],
                [
                    helper.make_tensor_value_info("label", TensorProto.INT64, [None]),
                    helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, [None, n_classes]),
                ],
            )
        else:
            node = helper.make_node(
                "SVMRegressor", ["X"], ["Y"],
                domain="ai.onnx.ml",
                support_vectors=[float(v) for v in (support_vectors.floats if support_vectors else [0.0])],
                coefficients=[float(v) for v in (dual_coef.floats if dual_coef else [1.0])],
                intercepts=[float(v) for v in (intercept.floats if intercept else [0.0])],
                kernel_type="RBF",
                gamma=1.0,
                vector_type="TRAINABLE_SVM",
            )

            graph_def = helper.make_graph(
                [node], "svm_graph",
                [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 1])],
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
