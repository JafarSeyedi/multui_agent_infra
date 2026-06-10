from __future__ import annotations

from typing import Any

from engines.document.models.ksdm_models import ModelGraph, ModelNode, OpType
from engines.knowledge.ml_mining.converters import ConverterRegistry, ModelGraphConverter


def _has_linear_model(graph: ModelGraph) -> bool:
    for node in graph.nodes:
        if node.op_type in (OpType.LINEAR_REGRESSOR, OpType.LINEAR_CLASSIFIER,
                             OpType.REGRESSION, OpType.LOGISTIC_REGRESSION_MODEL,
                             OpType.LINEAR_REGRESSION_MODEL):
            return True
        if node.sub_graph:
            for sn in node.sub_graph.nodes:
                if sn.op_type in (OpType.LINEAR_REGRESSOR, OpType.LINEAR_CLASSIFIER,
                                   OpType.REGRESSION, OpType.LOGISTIC_REGRESSION_MODEL,
                                   OpType.LINEAR_REGRESSION_MODEL):
                    return True
    return False


def _find_linear_node(graph: ModelGraph) -> ModelNode | None:
    for node in graph.nodes:
        if node.op_type in (OpType.LINEAR_REGRESSOR, OpType.LINEAR_CLASSIFIER,
                             OpType.REGRESSION, OpType.LOGISTIC_REGRESSION_MODEL,
                             OpType.LINEAR_REGRESSION_MODEL):
            return node
        if node.sub_graph:
            for sn in node.sub_graph.nodes:
                if sn.op_type in (OpType.LINEAR_REGRESSOR, OpType.LINEAR_CLASSIFIER,
                                   OpType.REGRESSION, OpType.LOGISTIC_REGRESSION_MODEL,
                                   OpType.LINEAR_REGRESSION_MODEL):
                    return sn
    return None


@ConverterRegistry.register
class RegressionConverter(ModelGraphConverter):
    def can_convert(self, graph: Any) -> bool:
        if not isinstance(graph, ModelGraph):
            return False
        return _has_linear_model(graph)

    def convert(self, graph: Any) -> bytes:
        import onnx
        from onnx import helper, TensorProto

        linear_node = _find_linear_node(graph)
        if linear_node is None:
            raise ValueError("No linear model node found in graph")

        coeffs = linear_node.attributes.get("coefficients")
        intercept = linear_node.attributes.get("intercept")

        is_classifier = linear_node.op_type in (
            OpType.LINEAR_CLASSIFIER, OpType.LOGISTIC_REGRESSION_MODEL
        )

        if not coeffs or not coeffs.floats:
            raise ValueError("Linear model missing coefficients")

        coef_values = coeffs.floats
        n_features = len(coef_values)

        n_classes = 2

        if is_classifier:
            kwargs: dict[str, Any] = {
                "coefficients": coef_values,
                "intercepts": [intercept.floats[0]] if intercept and intercept.floats else [0.0],
                "post_transform": "LOGISTIC",
            }
            node = helper.make_node(
                "LinearClassifier", ["X"], ["label", "probabilities"],
                domain="ai.onnx.ml", **kwargs,
            )
            outputs = [
                helper.make_tensor_value_info("label", TensorProto.INT64, [None]),
                helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, [None, n_classes]),
            ]
        else:
            node = helper.make_node(
                "LinearRegressor", ["X"], ["Y"],
                domain="ai.onnx.ml",
                coefficients=coef_values,
                intercepts=[intercept.floats[0]] if intercept and intercept.floats else [0.0],
            )
            outputs = [
                helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None]),
            ]

        graph_def = helper.make_graph(
            [node], "regression_graph",
            [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, n_features])],
            outputs,
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
