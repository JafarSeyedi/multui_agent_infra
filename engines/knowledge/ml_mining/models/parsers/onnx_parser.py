from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.knowledge.ml_mining.models import (
    AttributeValue,
    MiningModelType,
    ModelFormat,
    ModelGraph,
    ModelNode,
    MlMiningDocument,
    OpType,
    Port,
)
from engines.document.models.msdm_models import DataType, ScalarType
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.parsers.base import BaseDocumentParser, ParseOptions

ONNX_AVAILABLE = importlib.util.find_spec("onnx") is not None

_ONNX_DTYPE_MAP: dict[int, ScalarType] = {
    1: ScalarType.FLOAT,
    2: ScalarType.INT,
    3: ScalarType.INT,
    4: ScalarType.INT,
    5: ScalarType.INT,
    6: ScalarType.INT,
    7: ScalarType.LONG,
    8: ScalarType.STRING,
    9: ScalarType.BOOLEAN,
    10: ScalarType.FLOAT,
    11: ScalarType.DOUBLE,
    12: ScalarType.INT,
    13: ScalarType.LONG,
    14: ScalarType.FLOAT,
    15: ScalarType.DOUBLE,
    16: ScalarType.FLOAT,
}


def _onnx_dtype_to_scalar(dtype: int) -> ScalarType:
    return _ONNX_DTYPE_MAP.get(dtype, ScalarType.ANY)


def _parse_shape(dims: Any) -> list[int | str]:
    shape: list[int | str] = []
    for d in dims:
        if d.dim_value:
            shape.append(d.dim_value)
        elif d.dim_param:
            shape.append(d.dim_param)
        else:
            shape.append(-1)
    return shape


def _parse_value_info(vi: Any) -> tuple[str, DataType | None, list[int | str] | None]:
    name = vi.name
    if vi.type.HasField("tensor_type"):
        tensor_type = vi.type.tensor_type
        onnx_dtype = tensor_type.elem_type
        scalar = _onnx_dtype_to_scalar(onnx_dtype) if onnx_dtype else ScalarType.ANY
        data_type = DataType(base=scalar)
        shape = _parse_shape(tensor_type.shape.dim) if tensor_type.HasField("shape") else None
        return name, data_type, shape
    return name, None, None


def _attr_value(proto: Any) -> AttributeValue:
    t = proto.type
    if t == 1:
        return AttributeValue(float_value=proto.f)
    elif t == 2:
        return AttributeValue(int_value=proto.i)
    elif t == 3:
        return AttributeValue(string_value=proto.s.decode("utf-8", errors="replace"))
    elif t == 4:
        return _parse_tensor_attr(proto.t)
    elif t == 5:
        return AttributeValue(graph_value=_parse_graph(proto.g))
    elif t == 6:
        return AttributeValue(floats=list(proto.floats))
    elif t == 7:
        return AttributeValue(ints=list(proto.ints))
    elif t == 8:
        return AttributeValue(strings=[s.decode("utf-8", errors="replace") for s in proto.strings])
    elif t == 11:
        return AttributeValue(string_value=f"graphs_count={len(proto.graphs)}")
    return AttributeValue()


def _parse_tensor_attr(tp: Any) -> AttributeValue:
    try:
        import numpy as np
        arr = np.frombuffer(tp.raw_data, dtype=_onnx_dtype_to_numpy(tp.data_type))
        if arr.size == 1:
            return AttributeValue(float_value=float(arr[0]), tensor_shape=list(tp.dims))
        return AttributeValue(
            floats=arr.flatten().tolist() if tp.data_type in (1, 10, 11, 16) else [],
            ints=arr.flatten().tolist() if tp.data_type in (2, 3, 4, 5, 6, 7, 12, 13) else [],
            tensor_shape=list(tp.dims),
            tensor_data=tp.raw_data,
        )
    except Exception:
        return AttributeValue(
            tensor_shape=list(tp.dims) if tp.dims else None,
            tensor_data=tp.raw_data,
        )


def _onnx_dtype_to_numpy(dtype: int) -> str:
    _M = {
        1: "float32", 2: "uint8", 3: "int8", 4: "uint16", 5: "int16",
        6: "int32", 7: "int64", 8: "object", 9: "bool", 10: "float16",
        11: "float64", 12: "uint32", 13: "uint64", 14: "complex64",
        15: "complex128", 16: "bfloat16",
    }
    return _M.get(dtype, "float32")


def _parse_graph(g: Any, model_meta: dict[str, Any] | None = None) -> ModelGraph:
    meta = dict(model_meta or {})

    value_info_map: dict[str, tuple[DataType | None, list[int | str] | None]] = {}
    for vi in g.value_info:
        name, dt, shape = _parse_value_info(vi)
        if name:
            value_info_map[name] = (dt, shape)
    for inp in g.input:
        name, dt, shape = _parse_value_info(inp)
        if name and name not in value_info_map:
            value_info_map[name] = (dt, shape)

    init_names: set[str] = set()
    for init in g.initializer:
        init_names.add(init.name)

    nodes: list[ModelNode] = []

    for n in g.node:
        try:
            op_type = OpType(n.op_type)
        except ValueError:
            op_type = OpType.CUSTOM

        node_inputs: list[Port] = []
        for i_name in n.input:
            dt, shape = value_info_map.get(i_name, (None, None))
            node_inputs.append(Port(name=i_name, data_type=dt, shape=shape))

        node_outputs: list[Port] = []
        for o_name in n.output:
            dt, shape = value_info_map.get(o_name, (None, None))
            node_outputs.append(Port(name=o_name, data_type=dt, shape=shape))

        attrs: dict[str, AttributeValue] = {}
        for a in n.attribute:
            av = _attr_value(a)
            attrs[a.name] = av
            if a.type == 5 and av.graph_value is not None:
                nodes.extend(av.graph_value.nodes)

        node_attrs = dict(attrs)
        if n.domain:
            node_attrs["domain"] = AttributeValue(string_value=n.domain)

        nodes.append(ModelNode(
            id=n.name or f"{n.op_type}_{len(nodes)}",
            op_type=op_type,
            name=n.name or "",
            attributes=node_attrs,
            inputs=node_inputs,
            outputs=node_outputs,
        ))

    init_nodes: list[ModelNode] = []
    for init in g.initializer:
        dt, shape = value_info_map.get(init.name, (None, None))
        arr_dtype = _onnx_dtype_to_scalar(init.data_type)
        if dt is None:
            dt = DataType(base=arr_dtype)
        init_attrs: dict[str, AttributeValue] = {}
        init_dims = list(init.dims)
        try:
            import numpy as np
            arr = np.frombuffer(init.raw_data, dtype=_onnx_dtype_to_numpy(init.data_type))
            if arr.size == 1 and not init_dims:
                init_attrs["value"] = AttributeValue(
                    float_value=float(arr[0]),
                    tensor_data=init.raw_data,
                    tensor_shape=init_dims,
                )
            else:
                init_attrs["value"] = AttributeValue(
                    floats=arr.flatten().tolist() if init.data_type in (1, 10, 11, 16) else [],
                    ints=arr.flatten().tolist() if init.data_type in (2, 3, 4, 5, 6, 7, 12, 13) else [],
                    tensor_shape=init_dims,
                    tensor_data=init.raw_data,
                )
        except Exception:
            init_attrs["value"] = AttributeValue(
                tensor_shape=init_dims,
                tensor_data=init.raw_data,
            )

        init_nodes.append(ModelNode(
            id=init.name,
            op_type=OpType.CONSTANT,
            name=init.name,
            outputs=[Port(name=init.name, data_type=dt, shape=init_dims if init_dims else None)],
            attributes=init_attrs,
        ))
    init_names_list = {init.name for init in g.initializer}
    used_names = {n.name for n in nodes}
    filtered_inits = [n for n in init_nodes if n.name and n.name not in used_names]
    all_nodes = filtered_inits + nodes

    input_ports: list[Port] = []
    for inp in g.input:
        if inp.name not in init_names_list:
            name, dt, shape = _parse_value_info(inp)
            input_ports.append(Port(name=name, data_type=dt, shape=shape))

    output_ports: list[Port] = []
    for out in g.output:
        name, dt, shape = _parse_value_info(out)
        output_ports.append(Port(name=name, data_type=dt, shape=shape))

    vi_list: list[dict[str, Any]] = []
    for vi in g.value_info:
        name, dt, shape = _parse_value_info(vi)
        vi_list.append({
            "name": name,
            "elem_type": vi.type.tensor_type.elem_type if vi.type.HasField("tensor_type") else 0,
            "shape": shape,
        })

    metadata: dict[str, Any] = dict(meta)
    metadata["value_info"] = vi_list
    metadata["initializer_names"] = list(init_names_list)

    return ModelGraph(
        name=g.name,
        nodes=all_nodes,
        inputs=input_ports,
        outputs=output_ports,
        metadata=metadata,
    )


class OnnxParser(BaseDocumentParser):
    name = "onnx"
    supported_extensions = (".onnx", ".pb")

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
        if isinstance(source, str) and source.endswith((".onnx", ".pb")):
            return True
        try:
            data = Path(source).read_bytes()[:4] if Path(source).exists() else b""
            return len(data) > 0 and data[0] == 0x08
        except Exception:
            return False

    def _parse_data(self, data: bytes, name: str, doc_id: str) -> MlMiningDocument:
        if not ONNX_AVAILABLE:
            raise ImportError(
                "The 'onnx' package is required to parse ONNX models. "
                "Install it with: pip install onnx"
            )

        import onnx
        model_proto = onnx.load_model_from_string(data)

        opset_list: list[dict[str, Any]] = []
        for entry in model_proto.opset_import:
            opset_list.append({"domain": entry.domain, "version": entry.version})

        model_meta: dict[str, Any] = {
            "ir_version": model_proto.ir_version,
            "producer_name": model_proto.producer_name,
            "producer_version": model_proto.producer_version,
            "opset_imports": opset_list,
        }

        graph = _parse_graph(model_proto.graph, model_meta=model_meta)

        return MlMiningDocument(
            title=name,
            document_id=doc_id,
            model_type=MiningModelType.ONNX_MODEL,
            model_format=ModelFormat.ONNX,
            model_data=data,
            model_graph=graph,
            media_type=MEDIA_TYPES["onnx_protobuf"],
        )
