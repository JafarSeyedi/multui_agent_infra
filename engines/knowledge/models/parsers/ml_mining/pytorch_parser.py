from __future__ import annotations

import io
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.knowledge.models.ksdm_models import (
    AttributeValue,
    MiningModelType,
    ModelFormat,
    ModelGraph,
    ModelNode,
    MlMiningDocument,
    OpType,
    Port,
    TrainingConfig,
    TrainingTask,
)
from engines.document.models.msdm_models import DataType, ScalarType


def _to_int_list(val: int | tuple[int, ...] | str) -> list[int]:
    if isinstance(val, tuple):
        return list(val)
    if isinstance(val, str):
        return [0]
    return [val]
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.parsers.base import BaseDocumentParser, ParseOptions

_TORCH_AVAILABLE: bool = False
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    pass

_TASK_FROM_LOSS: dict[str, TrainingTask] = {
    "cross_entropy": TrainingTask.CLASSIFICATION,
    "bce": TrainingTask.CLASSIFICATION,
    "mse": TrainingTask.REGRESSION,
    "l1": TrainingTask.REGRESSION,
    "nll": TrainingTask.CLASSIFICATION,
}


def _module_to_op(module: Any, module_name: str = "") -> tuple[OpType, dict[str, AttributeValue]]:
    import torch.nn as nn

    attrs: dict[str, AttributeValue] = {}

    if isinstance(module, nn.Linear):
        attrs["in_features"] = AttributeValue(int_value=module.in_features)
        attrs["out_features"] = AttributeValue(int_value=module.out_features)
        if module.bias is not None:
            attrs["has_bias"] = AttributeValue(string_value="true")
        return (OpType.GEMM, attrs)
    elif isinstance(module, nn.Conv2d):
        attrs["in_channels"] = AttributeValue(int_value=module.in_channels)
        attrs["out_channels"] = AttributeValue(int_value=module.out_channels)
        attrs["kernel_shape"] = AttributeValue(ints=_to_int_list(module.kernel_size))
        attrs["strides"] = AttributeValue(ints=_to_int_list(module.stride))
        attrs["pads"] = AttributeValue(ints=_to_int_list(module.padding))
        return (OpType.CONV, attrs)
    elif isinstance(module, nn.MaxPool2d):
        attrs["kernel_shape"] = AttributeValue(ints=_to_int_list(module.kernel_size))
        attrs["strides"] = AttributeValue(ints=_to_int_list(module.stride))
        return (OpType.MAX_POOL, attrs)
    elif isinstance(module, nn.AvgPool2d):
        attrs["kernel_shape"] = AttributeValue(ints=_to_int_list(module.kernel_size))
        attrs["strides"] = AttributeValue(ints=_to_int_list(module.stride))
        return (OpType.AVERAGE_POOL, attrs)
    elif isinstance(module, nn.BatchNorm2d) or isinstance(module, nn.BatchNorm1d):
        attrs["num_features"] = AttributeValue(int_value=module.num_features)
        return (OpType.BATCH_NORMALIZATION, attrs)
    elif isinstance(module, nn.Dropout) or isinstance(module, nn.Dropout2d):
        attrs["ratio"] = AttributeValue(float_value=module.p)
        return (OpType.DROPOUT, attrs)
    elif isinstance(module, nn.LSTM):
        attrs["hidden_size"] = AttributeValue(int_value=module.hidden_size)
        attrs["num_layers"] = AttributeValue(int_value=module.num_layers)
        attrs["bidirectional"] = AttributeValue(string_value=str(module.bidirectional))
        return (OpType.LSTM, attrs)
    elif isinstance(module, nn.ReLU):
        return (OpType.RELU, attrs)
    elif isinstance(module, nn.GELU):
        return (OpType.GELU, attrs)
    elif isinstance(module, nn.Sigmoid):
        return (OpType.SIGMOID, attrs)
    elif isinstance(module, nn.Tanh):
        return (OpType.TANH, attrs)
    elif isinstance(module, nn.Softmax):
        dim = getattr(module, "dim", None)
        if dim is not None:
            attrs["axis"] = AttributeValue(int_value=dim)
        return (OpType.SOFTMAX, attrs)
    elif isinstance(module, nn.Flatten):
        return (OpType.FLATTEN, attrs)
    elif isinstance(module, nn.Embedding):
        attrs["vocab_size"] = AttributeValue(int_value=module.num_embeddings)
        attrs["embedding_dim"] = AttributeValue(int_value=module.embedding_dim)
        return (OpType.EMBEDDING, attrs)
    else:
        return (OpType.NEURAL_NETWORK, attrs)


def _build_module_graph(module: Any, prefix: str = "") -> list[ModelNode]:
    import torch.nn as nn

    nodes: list[ModelNode] = []
    op_type, attrs = _module_to_op(module)
    mod_name = prefix or type(module).__name__
    mod_id = prefix or f"module_{id(module)}"

    child_nodes: list[ModelNode] = []
    if hasattr(module, "named_children"):
        for child_name, child_module in module.named_children():
            child_prefix = f"{prefix}.{child_name}" if prefix else child_name
            child_nodes.extend(_build_module_graph(child_module, child_prefix))

    sub_graph: ModelGraph | None = None
    if child_nodes:
        sub_graph = ModelGraph(name=mod_name, nodes=child_nodes)

    param_count = sum(p.numel() for p in module.parameters()) if hasattr(module, "parameters") else 0
    attrs["parameter_count"] = AttributeValue(int_value=param_count)

    nodes.append(ModelNode(
        id=mod_id,
        op_type=op_type,
        name=mod_name,
        attributes=attrs,
        sub_graph=sub_graph,
    ))
    return nodes


def _infer_task(module: Any) -> TrainingTask:
    for child_name, _ in getattr(module, "named_modules", lambda: [])():
        lower = child_name.lower()
        if "classifier" in lower or "class" in lower:
            return TrainingTask.CLASSIFICATION
    loss_fn_name = getattr(getattr(module, "loss_fn", None), "__class__", None)
    if loss_fn_name:
        name = loss_fn_name.__name__.lower().replace("loss", "").strip()
        task = _TASK_FROM_LOSS.get(name)
        if task:
            return task
    if hasattr(module, "state_dict"):
        sd = module.state_dict()
        last_weight = list(sd.values())[-1] if sd else None
        if last_weight is not None and hasattr(last_weight, "shape") and len(last_weight.shape) == 2:
            if last_weight.shape[0] == 1:
                return TrainingTask.REGRESSION
    return TrainingTask.CLASSIFICATION


class PyTorchParser(BaseDocumentParser):
    name = "pytorch"
    supported_extensions = (".pt", ".pth", ".pytorch")

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
        if isinstance(source, str) and source.endswith((".pt", ".pth", ".pytorch")):
            return True
        try:
            data = Path(source).read_bytes()[:4] if Path(source).exists() else b""
            return data[:2] == b"\x80\x02" or data[:3] == b"PK\x03"
        except Exception:
            return False

    def _parse_data(self, data: bytes, name: str, doc_id: str) -> MlMiningDocument:
        if not _TORCH_AVAILABLE:
            raise ImportError(
                "The 'torch' package is required to parse PyTorch models. "
                "Install it with: pip install torch"
            )

        module = self._load_module(data)
        nodes = _build_module_graph(module)
        model_graph = ModelGraph(
            name=type(module).__name__,
            nodes=nodes,
            metadata={
                "parameter_count": sum(p.numel() for p in module.parameters()),
                "requires_grad_count": sum(1 for p in module.parameters() if p.requires_grad),
            },
        )

        task = _infer_task(module)

        return MlMiningDocument(
            title=name,
            document_id=doc_id,
            model_type=MiningModelType.NEURAL_NETWORK,
            model_format=ModelFormat.PYTORCH,
            model_graph=model_graph,
            model_data=data,
            training_config=TrainingConfig(task=task),
            media_type=MEDIA_TYPES.get("pytorch_model", MEDIA_TYPES["onnx_protobuf"]),
        )

    def _load_module(self, data: bytes) -> Any:
        import torch

        buf = io.BytesIO(data)
        try:
            model = torch.jit.load(buf)
            model.eval()
            return model
        except Exception:
            pass

        try:
            buf.seek(0)
            sd = torch.load(buf, weights_only=True)
            if isinstance(sd, dict):
                import torch.nn as nn
                wrapper = nn.Module()
                wrapper.__dict__.update(sd)
                wrapper.eval()
                return wrapper
            return sd
        except Exception as e:
            raise ValueError(f"Could not load PyTorch model from bytes: {e}")
