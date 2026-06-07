import importlib.util
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.writers.base import BaseKnowledgeWriter, BaseDocument
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.isdm_models import MlMiningDocument


class OnnxWriter(BaseKnowledgeWriter):
    supported_format = MEDIA_TYPES["onnx_proto"]

    def can_write(self, document) -> bool:
        return isinstance(document, MlMiningDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        onnx_model = getattr(document, 'onnx_model', None)
        if onnx_model is None:
            raise TypeError("onnx_model must be set on the document to write ONNX format")
        if not importlib.util.find_spec('onnx'):
            raise TypeError("ONNX writing requires 'onnx' package. Install with: pip install onnx")
        import onnx
        from onnx import helper
        nodes = []
        for n in onnx_model.graph.nodes:
            nodes.append(helper.make_node(n.op_type, n.input_names, n.output_names, name=n.op_type))
        graph = helper.make_graph(nodes, onnx_model.graph.name, onnx_model.graph.inputs, onnx_model.graph.outputs, onnx_model.graph.initializers)
        opset = [helper.make_opsetid(d, v) for d, v in onnx_model.opset_imports.items()]
        model = helper.make_model(graph, opset_imports=opset)
        if onnx_model.producer_name:
            model.producer_name = onnx_model.producer_name
        onnx.checker.check_model(model)
        model_bytes = model.SerializeToString()
        if destination is not None:
            if isinstance(destination, (str, Path)):
                onnx.save(model, str(destination))
            else:
                cast(BinaryIO, destination).write(model_bytes)
        return model_bytes
