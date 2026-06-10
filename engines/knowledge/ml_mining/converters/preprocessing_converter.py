from __future__ import annotations

from typing import Any

from engines.document.models.ksdm_models import ModelGraph, ModelNode, OpType
from engines.knowledge.ml_mining.converters import ConverterRegistry, ModelGraphConverter

_PREPROC_OPS = {
    OpType.NORMALIZER, OpType.SCALER, OpType.IMPUTER,
    OpType.ONE_HOT_ENCODER, OpType.LABEL_ENCODER,
    OpType.BINARIZER, OpType.FEATURE_VECTORIZER,
    OpType.DICT_VECTORIZER, OpType.ARRAY_FEATURE_EXTRACTOR,
    OpType.CATEGORY_MAPPER, OpType.STRING_NORMALIZER,
    OpType.TRANSFORMER,
}


def _has_preprocessing(graph: ModelGraph) -> bool:
    for node in graph.nodes:
        if node.op_type in _PREPROC_OPS:
            return True
        if node.sub_graph and _has_preprocessing(node.sub_graph):
            return True
    return False


def _op_to_onnx_ml(op: OpType) -> str:
    mapping = {
        OpType.NORMALIZER: "Normalizer",
        OpType.SCALER: "Scaler",
        OpType.IMPUTER: "Imputer",
        OpType.ONE_HOT_ENCODER: "OneHotEncoder",
        OpType.LABEL_ENCODER: "LabelEncoder",
        OpType.BINARIZER: "Binarizer",
    }
    return mapping.get(op, op.value)


@ConverterRegistry.register
class PreprocessingConverter(ModelGraphConverter):
    def can_convert(self, graph: Any) -> bool:
        if not isinstance(graph, ModelGraph):
            return False
        return _has_preprocessing(graph)

    def convert(self, graph: Any) -> bytes:
        import onnx
        from onnx import helper, TensorProto

        prep_nodes = [n for n in graph.nodes if n.op_type in _PREPROC_OPS]

        if not prep_nodes:
            prep_nodes = []
            for n in graph.nodes:
                if n.sub_graph:
                    prep_nodes.extend(
                        sn for sn in n.sub_graph.nodes if sn.op_type in _PREPROC_OPS
                    )

        if not prep_nodes:
            raise ValueError("No preprocessing nodes found in graph")

        onnx_nodes: list[Any] = []
        prev_output = "X"
        n_features = 1

        for i, node in enumerate(prep_nodes):
            onnx_name = _op_to_onnx_ml(node.op_type)
            output_name = f"transformed_{i}"

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
                elif av.strings:
                    attrs[key] = av.strings

            if onnx_name == "Scaler":
                attrs.setdefault("offset", [0.0] * n_features)
                attrs.setdefault("scale", [1.0] * n_features)

            if onnx_name == "Normalizer":
                attrs.setdefault("norm", "MAX")

            if onnx_name == "Imputer":
                attrs.setdefault("replaced_value_float", 0.0)
                attrs.setdefault("imputed_value_floats", [0.0])

            onnx_node = helper.make_node(
                onnx_name, [prev_output], [output_name],
                domain="ai.onnx.ml",
                name=node.id or f"preproc_{i}",
                **attrs,
            )
            onnx_nodes.append(onnx_node)
            prev_output = output_name

        graph_def = helper.make_graph(
            onnx_nodes, "preprocessing_graph",
            [helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, n_features])],
            [helper.make_tensor_value_info(prev_output, TensorProto.FLOAT, [None, n_features])],
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
