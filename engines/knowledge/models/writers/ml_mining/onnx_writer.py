from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO

from engines.document.writers.base import BaseDocument, BaseDocumentWriter
from engines.knowledge.models.ksdm_models import (
    AttributeValue,
    MlMiningDocument,
    ModelGraph,
    ModelNode,
    OpType,
    Port,
)

ONNX_AVAILABLE = importlib.util.find_spec("onnx") is not None

_ONNX_SCALAR_MAP: dict[str, int] = {
    "float": 1, "int": 6, "long": 7, "double": 11, "boolean": 9,
    "string": 8, "uint8": 2, "int8": 3, "int16": 5, "int32": 6,
    "int64": 7, "uint16": 4, "uint32": 12, "uint64": 13,
    "float16": 10, "bfloat16": 16,
}


def _scalar_to_onnx_dtype(scalar: str | None) -> int:
    return _ONNX_SCALAR_MAP.get(scalar or "", 1)


def _port_to_type_proto(name: str, dt: Any, shape: list[int | str] | None) -> Any:
    import onnx
    from onnx import helper, TensorProto
    onnx_dtype = _scalar_to_onnx_dtype(dt.base.value if dt else None)
    tp = helper.make_tensor_value_info(name, onnx_dtype, shape or [None])
    return tp


def _write_sub_graph(graph: ModelGraph) -> Any:
    import onnx
    from onnx import helper

    sub_nodes = []
    for n in graph.nodes:
        if n.op_type == OpType.CONSTANT:
            continue
        sub_nodes.append(_write_node(n))

    sub_inputs = []
    for inp in graph.inputs:
        sub_inputs.append(_port_to_type_proto(inp.name, inp.data_type, inp.shape))

    sub_outputs = []
    for out in graph.outputs:
        sub_outputs.append(_port_to_type_proto(out.name, out.data_type, out.shape))

    sub_inits = []
    for n in graph.nodes:
        if n.op_type == OpType.CONSTANT:
            init = _write_initializer(n)
            if init is not None:
                sub_inits.append(init)

    return helper.make_graph(sub_nodes, graph.name, sub_inputs, sub_outputs, sub_inits)


def _write_initializer(node: ModelNode) -> Any:
    import onnx
    from onnx import numpy_helper
    import numpy as np

    if not node.outputs:
        return None
    val = node.attributes.get("value")
    if val is None:
        return None
    shape = val.tensor_shape or []
    arr: np.ndarray = np.array([], dtype=np.float32)
    if val.tensor_data:
        arr = np.frombuffer(val.tensor_data, dtype=np.float32)
        if shape:
            try:
                arr = arr.reshape(shape)
            except Exception:
                pass
    elif val.floats:
        arr = np.array(val.floats, dtype=np.float32).reshape(shape) if shape else np.array(val.floats, dtype=np.float32)
    elif val.ints:
        arr = np.array(val.ints, dtype=np.int64).reshape(shape) if shape else np.array(val.ints, dtype=np.int64)
    elif val.float_value is not None:
        arr = np.array(val.float_value, dtype=np.float32)
    elif val.int_value is not None:
        arr = np.array(val.int_value, dtype=np.int64)
    else:
        arr = np.zeros(shape, dtype=np.float32) if shape else np.array([], dtype=np.float32)
    return numpy_helper.from_array(arr, node.outputs[0].name)


def _write_node(node: ModelNode) -> Any:
    import onnx
    from onnx import helper

    domain_attr = node.attributes.get("domain")
    filtered_attrs = {k: v for k, v in node.attributes.items() if k != "domain"}
    attrs = _write_attributes(node.op_type, filtered_attrs)

    onnx_node = helper.make_node(
        node.op_type.value,
        [p.name for p in node.inputs],
        [p.name for p in node.outputs],
        name=node.name or node.op_type.value,
        **attrs,
    )

    if domain_attr is not None and domain_attr.string_value:
        onnx_node.domain = domain_attr.string_value

    return onnx_node


def _write_attributes(op_type: OpType, attrs: dict[str, AttributeValue]) -> dict[str, Any]:
    import onnx
    from onnx import helper

    result: dict[str, Any] = {}
    for key, av in attrs.items():
        if key in ("value", "predicate", "score", "record_count",
                    "score_dist_values", "score_dist_counts",
                    "score_dist_confidences", "coords", "size",
                    "intercept", "target_category", "coefficient",
                    "exponent"):
            continue
        if av.int_value is not None:
            result[key] = av.int_value
        elif av.float_value is not None:
            result[key] = av.float_value
        elif av.string_value is not None:
            result[key] = av.string_value
        elif av.ints:
            result[key] = av.ints
        elif av.floats:
            result[key] = av.floats
        elif av.strings:
            result[key] = av.strings
        elif av.tensor_data:
            import numpy as np
            arr = np.frombuffer(av.tensor_data, dtype=np.float32)
            if av.tensor_shape:
                try:
                    arr = arr.reshape(av.tensor_shape)
                except Exception:
                    pass
            result[key] = arr
        elif av.graph_value is not None:
            result[key] = _write_sub_graph(av.graph_value)
    return result


def _write_graph(doc: MlMiningDocument) -> Any:
    import onnx
    from onnx import helper

    if doc.model_graph is None:
        return None

    graph = doc.model_graph

    model_nodes: list[Any] = []
    graph_inits: list[Any] = []

    for n in graph.nodes:
        if n.op_type == OpType.CONSTANT:
            init = _write_initializer(n)
            if init is not None:
                graph_inits.append(init)
        else:
            model_nodes.append(_write_node(n))

    graph_inputs = []
    for inp in graph.inputs:
        graph_inputs.append(_port_to_type_proto(inp.name, inp.data_type, inp.shape))

    graph_outputs = []
    for out in graph.outputs:
        graph_outputs.append(_port_to_type_proto(out.name, out.data_type, out.shape))

    return helper.make_graph(model_nodes, graph.name, graph_inputs, graph_outputs, graph_inits)


class OnnxWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document: Any) -> bool:
        return isinstance(document, MlMiningDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | None = None, **options: Any) -> bytes:
        doc = MlMiningDocument.model_validate(document)

        if doc.model_graph is not None and ONNX_AVAILABLE:
            import onnx
            from onnx import helper
            import numpy as np  # noqa: F401

            graph_proto = _write_graph(doc)

            if graph_proto is None:
                return doc.model_data or b""

            metadata = doc.model_graph.metadata
            opset_imports = metadata.get("opset_imports", [{"domain": "ai.onnx", "version": 18}])
            opset = [helper.make_opsetid(d["domain"], d["version"]) for d in opset_imports]

            model_proto = helper.make_model(graph_proto, opset_imports=opset)
            producer_name = metadata.get("producer_name", "")
            producer_version = metadata.get("producer_version", "")
            ir_version = metadata.get("ir_version", 0)
            if producer_name:
                model_proto.producer_name = producer_name
            if producer_version:
                model_proto.producer_version = producer_version
            if ir_version:
                model_proto.ir_version = ir_version

            try:
                onnx.checker.check_model(model_proto)
            except Exception:
                pass

            model_bytes = model_proto.SerializeToString()
        elif doc.model_data:
            model_bytes = doc.model_data
        else:
            model_bytes = b""

        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(model_bytes)
            else:
                destination.write(model_bytes)
        return model_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/octet-stream"]

    def get_supported_extensions(self) -> list[str]:
        return [".onnx"]
