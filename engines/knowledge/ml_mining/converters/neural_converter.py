from __future__ import annotations

from typing import Any

from engines.knowledge.ml_mining.models import ModelGraph, ModelNode, OpType
from engines.knowledge.ml_mining.converters import ConverterRegistry, ModelGraphConverter

_NN_OPS = {
    OpType.CONV, OpType.MAX_POOL, OpType.AVERAGE_POOL, OpType.GEMM,
    OpType.RELU, OpType.SIGMOID, OpType.TANH, OpType.SOFTMAX,
    OpType.GELU, OpType.FLATTEN, OpType.BATCH_NORMALIZATION,
    OpType.LAYER_NORMALIZATION, OpType.DROPOUT, OpType.LSTM,
    OpType.GRU, OpType.RNN, OpType.EMBEDDING,
    OpType.MATMUL, OpType.ADD, OpType.MUL, OpType.SUB, OpType.DIV,
    OpType.CONCAT, OpType.RESHAPE, OpType.TRANSPOSE,
    OpType.NEURAL_NETWORK,
}


def _is_nn_graph(graph: ModelGraph) -> bool:
    for node in graph.nodes:
        if node.op_type in _NN_OPS:
            return True
        if node.sub_graph and _is_nn_graph(node.sub_graph):
            return True
    return False


def _op_to_onnx_name(op: OpType) -> str:
    mapping = {
        OpType.CONV: "Conv",
        OpType.MAX_POOL: "MaxPool",
        OpType.AVERAGE_POOL: "AveragePool",
        OpType.GEMM: "Gemm",
        OpType.RELU: "Relu",
        OpType.SIGMOID: "Sigmoid",
        OpType.TANH: "Tanh",
        OpType.SOFTMAX: "Softmax",
        OpType.GELU: "Gelu",
        OpType.FLATTEN: "Flatten",
        OpType.BATCH_NORMALIZATION: "BatchNormalization",
        OpType.LAYER_NORMALIZATION: "LayerNormalization",
        OpType.DROPOUT: "Dropout",
        OpType.LSTM: "LSTM",
        OpType.GRU: "GRU",
        OpType.RNN: "RNN",
        OpType.EMBEDDING: "Embedding",
        OpType.MATMUL: "MatMul",
        OpType.ADD: "Add",
        OpType.MUL: "Mul",
        OpType.SUB: "Sub",
        OpType.DIV: "Div",
        OpType.CONCAT: "Concat",
        OpType.RESHAPE: "Reshape",
        OpType.TRANSPOSE: "Transpose",
    }
    return mapping.get(op, op.value)


def _flatten_nn(graph: ModelGraph, depth: int = 0) -> list[tuple[ModelNode, int]]:
    result: list[tuple[ModelNode, int]] = []
    for node in graph.nodes:
        result.append((node, depth))
        if node.sub_graph:
            result.extend(_flatten_nn(node.sub_graph, depth + 1))
    return result


@ConverterRegistry.register
class NeuralConverter(ModelGraphConverter):
    def can_convert(self, graph: Any) -> bool:
        if not isinstance(graph, ModelGraph):
            return False
        return _is_nn_graph(graph)

    def convert(self, graph: Any) -> bytes:
        import onnx
        from onnx import helper, TensorProto
        import numpy as np

        flat = _flatten_nn(graph)
        n_nodes = len(flat)

        n_features = 1
        if graph.inputs:
            inp_shape = graph.inputs[0].shape
            if inp_shape and len(inp_shape) > 1:
                dim = inp_shape[-1]
                n_features = dim if isinstance(dim, int) else 1

        onnx_nodes: list[Any] = []
        prev_output = "X"
        for i, (node, depth) in enumerate(flat):
            onnx_name = _op_to_onnx_name(node.op_type)
            nid = node.id or f"node_{i}"
            output_name = f"Y_{i}" if i < n_nodes - 1 else "Y"

            attrs: dict[str, Any] = {}
            for key, av in node.attributes.items():
                if key == "parameter_count":
                    continue
                if av.int_value is not None:
                    attrs[key] = av.int_value
                elif av.float_value is not None:
                    attrs[key] = av.float_value
                elif av.string_value is not None:
                    attrs[key] = av.string_value
                elif av.ints:
                    attrs[key] = av.ints
                elif av.floats:
                    attrs[key] = av.floats

            if onnx_name == "Gemm":
                attrs.setdefault("transA", 0)
                attrs.setdefault("transB", 0)
                attrs.setdefault("alpha", 1.0)
                attrs.setdefault("beta", 1.0)

            inputs = [prev_output]
            if node.inputs:
                inputs = [p.name for p in node.inputs]
            elif prev_output:
                inputs = [prev_output]

            onnx_node = helper.make_node(
                onnx_name, inputs, [output_name],
                name=nid,
                **attrs,
            )
            onnx_nodes.append(onnx_node)
            prev_output = output_name

        X_type = TensorProto.FLOAT
        graph_def = helper.make_graph(
            onnx_nodes, "neural_graph",
            [helper.make_tensor_value_info("X", X_type, [None, n_features])],
            [helper.make_tensor_value_info("Y", X_type, [None, n_features])],
        )

        model_def = helper.make_model(
            graph_def,
            opset_imports=[helper.make_opsetid("", 20)],
            producer_name="ml_mining_engine",
        )

        try:
            onnx.checker.check_model(model_def)
        except Exception:
            pass

        return model_def.SerializeToString()
