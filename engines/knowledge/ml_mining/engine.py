from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal, overload

import numpy as np

from engines.knowledge.ml_mining.models import (
    AttributeValue,
    EvaluationStage,
    FeatureImportance,
    FieldUsageType,
    ImportanceMethod,
    LossFunction,
    MiningField,
    MiningModelType,
    MiningSchema,
    ModelFormat,
    ModelGraph,
    ModelNode,
    ModelMetric,
    ModelParameter,
    ModelResult,
    MlMiningDocument,
    OpType,
    OptimizationAlgorithm,
    OutlierTreatment,
    ParameterName,
    Port,
    RegularizationConfig,
    TrainingConfig,
)
from engines.document.models.msdm_models import Attribute as MsdmAttribute
from engines.document.parsers.base import BaseDocumentParser
from engines.knowledge.ml_mining.models.parsers import (
    OnnxParser,
    PmmlParser,
    SklearnParser,
    PyTorchParser,
)
from engines.document.writers.base import BaseDocumentWriter
from engines.knowledge.ml_mining.models.writers import (
    OnnxWriter,
    PmmlWriter,
    SklearnWriter,
    PyTorchWriter,
)
from engines.knowledge.ml_mining.converters import ConverterRegistry


_PARSER_MAP: dict[str, type[BaseDocumentParser]] = {
    "pmml": PmmlParser,
    "onnx": OnnxParser,
    "sklearn": SklearnParser,
    "pytorch": PyTorchParser,
}

_WRITER_MAP: dict[str, type[BaseDocumentWriter]] = {
    "pmml": PmmlWriter,
    "onnx": OnnxWriter,
    "sklearn": SklearnWriter,
    "pytorch": PyTorchWriter,
}


class MlMiningEngine:
    def __init__(self, doc: MlMiningDocument | None = None):
        self._doc = doc
        self._onnx_session: Any = None
        self._onnx_model_bytes: bytes | None = None

    # --- Load / Parse -------------------------------------------------------

    async def async_load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> MlMiningDocument:
        if parser_name and parser_name in _PARSER_MAP:
            parser = _PARSER_MAP[parser_name]()
        else:
            parser = self._detect_parser(source)

        if isinstance(source, str):
            from pathlib import Path
            path = Path(source)
            result = await parser.parse_path(str(path), "load")
        else:
            result = await parser.parse_bytes(source, "load", "load")
        assert isinstance(result, MlMiningDocument)
        self._doc = result
        self._onnx_session = None
        self._onnx_model_bytes = None
        return self._doc

    def load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> MlMiningDocument:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_load(source, parser_name, **options))
        raise RuntimeError(
            "Cannot call load() synchronously inside an async context. "
            "Use await engine.async_load() instead."
        )

    async def async_parse(
        self,
        text_or_bytes: str | bytes,
        model_format: ModelFormat | None = None,
        **options: Any,
    ) -> MlMiningDocument:
        data = (
            text_or_bytes.encode("utf-8")
            if isinstance(text_or_bytes, str)
            else text_or_bytes
        )

        if model_format is not None:
            parser_cls = _PARSER_MAP.get(model_format.value)
            if parser_cls is None:
                raise ValueError(
                    f"Unsupported model format: {model_format}. "
                    f"Choose from: {', '.join(_PARSER_MAP.keys())}"
                )
            parser: BaseDocumentParser | None = parser_cls()
        else:
            text = data.decode("utf-8", errors="replace")
            if "<PMML" in text:
                parser = PmmlParser()
            elif data[:3] in (b"\x08\x00\x08", b"\x08\x01\x08"):
                parser = OnnxParser()
            elif data[:2] in (b"\x80\x02", b"\x80\x03", b"\x80\x04", b"\x80\x05"):
                parser = SklearnParser()
            else:
                parser = None
                if data[:1] == b"\x08":
                    try:
                        import onnx
                        onnx.load_model_from_string(data)
                        parser = OnnxParser()
                    except Exception:
                        pass
                if parser is None:
                    try:
                        import pickle
                        pickle.loads(data[:512])
                        parser = SklearnParser()
                    except Exception:
                        pass
                if parser is None:
                    try:
                        import torch
                        import io as _io
                        buf = _io.BytesIO(data)
                        try:
                            torch.jit.load(buf)
                            parser = PyTorchParser()
                        except Exception:
                            buf.seek(0)
                            torch.load(buf, weights_only=True)
                            parser = PyTorchParser()
                    except Exception:
                        pass
                if parser is None:
                    raise ValueError(
                        "Cannot auto-detect model format from content. "
                        "Specify model_format parameter."
                    )

        assert parser is not None
        result = await parser.parse_bytes(data, "parse", "parse")
        assert isinstance(result, MlMiningDocument)
        self._doc = result
        self._onnx_session = None
        self._onnx_model_bytes = None
        return self._doc

    # --- Graph API ----------------------------------------------------------

    def get_graph(self) -> ModelGraph | None:
        if self._doc is None:
            return None
        return self._doc.model_graph

    def get_node(self, node_id: str) -> ModelNode | None:
        if self._doc is None or self._doc.model_graph is None:
            return None
        return self._find_node_recursive(self._doc.model_graph, node_id)

    def find_nodes(
        self,
        op_type: str | OpType | None = None,
        name: str | None = None,
    ) -> list[ModelNode]:
        if self._doc is None or self._doc.model_graph is None:
            return []
        return self._find_nodes_recursive(self._doc.model_graph, op_type, name)

    @overload
    def traverse(self, yield_depth: Literal[False] = False) -> Iterator[ModelNode]: ...

    @overload
    def traverse(self, yield_depth: Literal[True]) -> Iterator[tuple[ModelNode, int]]: ...

    def traverse(
        self,
        yield_depth: bool = False,
    ) -> Iterator[ModelNode] | Iterator[tuple[ModelNode, int]]:
        if self._doc is None or self._doc.model_graph is None:
            return iter([])
        if yield_depth:
            return self._traverse_nodes_with_depth(self._doc.model_graph)
        return self._traverse_nodes(self._doc.model_graph)

    # --- MiningSchema API ---------------------------------------------------

    def get_mining_schema(self) -> MiningSchema | None:
        if self._doc is None:
            return None
        return self._doc.mining_schema

    def get_fields(self, usage_type: FieldUsageType | str | None = None) -> list[MiningField]:
        if self._doc is None or self._doc.mining_schema is None:
            return []
        if usage_type is not None:
            target = FieldUsageType(usage_type) if isinstance(usage_type, str) else usage_type
            return [f for f in self._doc.mining_schema.fields if f.usage_type == target]
        return list(self._doc.mining_schema.fields)

    def get_active_fields(self) -> list[MiningField]:
        return self.get_fields(usage_type="active")

    def get_predicted_field(self) -> MiningField | None:
        fields = self.get_fields(usage_type=FieldUsageType.PREDICTED)
        return fields[0] if fields else None

    # --- Model Metadata -----------------------------------------------------

    def get_model_type(self) -> MiningModelType | None:
        if self._doc is None:
            return None
        return self._doc.model_type

    def get_features(self) -> list[MsdmAttribute]:
        if self._doc is None:
            return []
        return self._doc.features

    def get_target(self) -> MsdmAttribute | None:
        if self._doc is None:
            return None
        return self._doc.target

    def get_metrics(self) -> list[ModelMetric]:
        if self._doc is None:
            return []
        return self._doc.metrics

    def get_training_config(self) -> TrainingConfig | None:
        if self._doc is None:
            return None
        return self._doc.training_config

    def get_model_format(self) -> ModelFormat | None:
        if self._doc is None:
            return None
        return self._doc.model_format

    def get_parameters(self) -> list[ModelParameter]:
        if self._doc is None:
            return []
        return self._doc.parameters

    def get_feature_importances(self) -> list[FeatureImportance]:
        if self._doc is None:
            return []
        return self._doc.feature_importances

    # --- Inference API ------------------------------------------------------

    def get_model_info(self) -> dict[str, Any]:
        if self._doc is None:
            return {"status": "no_document"}
        info: dict[str, Any] = {
            "status": "loaded",
            "title": self._doc.title,
            "model_type": self._doc.model_type.value if self._doc.model_type else None,
            "model_format": self._doc.model_format.value if self._doc.model_format else None,
            "n_features": len(self._doc.features) if self._doc.features else 0,
            "has_target": self._doc.target is not None,
            "has_graph": self._doc.model_graph is not None,
            "has_mining_schema": self._doc.mining_schema is not None,
            "n_parameters": len(self._doc.parameters) if self._doc.parameters else 0,
            "n_metrics": len(self._doc.metrics) if self._doc.metrics else 0,
            "n_feature_importances": len(self._doc.feature_importances) if self._doc.feature_importances else 0,
        }
        if self._doc.training_config:
            info["training_task"] = self._doc.training_config.task.value if self._doc.training_config.task else None
        if self._doc.model_graph:
            info["graph_nodes"] = len(self._doc.model_graph.nodes)
        return info

    async def predict(self, X: np.ndarray, auto_convert: bool = True) -> np.ndarray:
        if self._doc is None:
            raise ValueError("No document loaded. Call async_load() or async_parse() first.")

        if self._onnx_session is None:
            if not auto_convert:
                raise RuntimeError(
                    "No ONNX session loaded. Call _load_onnx_session() first "
                    "or set auto_convert=True."
                )
            model_bytes = await self._convert_to_onnx()
            self._load_onnx_session(model_bytes)

        input_name = self._onnx_session.get_inputs()[0].name
        output_name = self._onnx_session.get_outputs()[0].name

        if not isinstance(X, np.ndarray):
            X = np.array(X, dtype=np.float32)
        if X.dtype != np.float32:
            X = X.astype(np.float32)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        result = self._onnx_session.run([output_name], {input_name: X})[0]
        return result

    async def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        metrics: list[str] | None = None,
    ) -> dict[str, float]:
        predictions = await self.predict(X)

        if not isinstance(y, np.ndarray):
            y = np.array(y)
        if not isinstance(predictions, np.ndarray):
            predictions = np.array(predictions)

        if predictions.ndim > 1 and predictions.shape[1] > 1:
            pred_labels = predictions.argmax(axis=1)
        else:
            pred_labels = predictions.flatten()

        y_flat = y.flatten()

        from engines.knowledge.ml_mining.metrics import MetricsCalculator
        return MetricsCalculator.calc(y_flat, pred_labels, metrics)

    async def _convert_to_onnx(self) -> bytes:
        if self._doc is None or self._doc.model_graph is None:
            raise ValueError("No model graph available for conversion")

        converter = ConverterRegistry.find(self._doc.model_graph)
        if converter is not None:
            return converter.convert(self._doc.model_graph)

        import onnx
        from onnx import helper, TensorProto as TP

        fallback_node = helper.make_node(
            "Identity", ["X"], ["Y"], name="fallback"
        )
        n_features = max(len(self._doc.features), 1) if self._doc.features else 1
        graph_def = helper.make_graph(
            [fallback_node], "fallback_graph",
            [helper.make_tensor_value_info("X", TP.FLOAT, [None, n_features])],
            [helper.make_tensor_value_info("Y", TP.FLOAT, [None, n_features])],
        )
        model_def = helper.make_model(
            graph_def,
            opset_imports=[helper.make_opsetid("", 20)],
        )
        return model_def.SerializeToString()

    def _load_onnx_session(self, model_bytes: bytes) -> None:
        self._onnx_model_bytes = model_bytes
        import onnxruntime  # type: ignore[import-untyped]
        self._onnx_session = onnxruntime.InferenceSession(
            model_bytes,
            providers=["CPUExecutionProvider"],
        )

    # --- Validation ---------------------------------------------------------

    def validate(self) -> list[str]:
        warnings: list[str] = []
        if self._doc is None:
            return ["No document loaded"]
        graph = self._doc.model_graph
        if graph is None:
            return warnings
        node_ids: set[str] = set()
        for node, _depth in self._traverse_nodes_with_depth(graph):
            if node.id:
                if node.id in node_ids:
                    warnings.append(f"Duplicate node id: {node.id}")
                node_ids.add(node.id)
            if node.op_type == OpType.CUSTOM:
                warnings.append(f"Node '{node.id or '<unnamed>'}' has CUSTOM op_type")

        converter = ConverterRegistry.find(graph)
        if converter is None and graph.nodes:
            warnings.append(
                "No converter found for this model graph. Inference unavailable."
            )
        return warnings

    # --- Write / Convert ----------------------------------------------------

    async def async_convert(self, target_format: str, **options: Any) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded. Call async_load() or async_parse() first.")
        if target_format == "onnx_runtime":
            return await self._convert_to_onnx()
        writer_cls = _WRITER_MAP.get(target_format)
        if writer_cls is None:
            raise ValueError(
                f"Unknown target format: {target_format}. "
                f"Choose from: {', '.join(_WRITER_MAP.keys())}"
            )
        writer = writer_cls()
        return await writer.write(self._doc)

    def convert(self, target_format: str, **options: Any) -> bytes:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_convert(target_format, **options))
        raise RuntimeError(
            "Cannot call convert() synchronously inside an async context. "
            "Use await engine.async_convert() instead."
        )

    async def async_write(
        self,
        destination: str,
        format: str | None = None,
        **options: Any,
    ) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded.")
        if format and format in _WRITER_MAP:
            writer = _WRITER_MAP[format]()
        else:
            from pathlib import Path
            ext = Path(destination).suffix.lower()
            matched: list[BaseDocumentWriter] = []
            for cls in _WRITER_MAP.values():
                w = cls()
                if any(ext.endswith(e) for e in w.get_supported_extensions()):
                    matched.append(w)
            writer = matched[0] if matched else PmmlWriter()
        result = await writer.write(self._doc)
        Path(destination).write_bytes(result)
        return result

    def write(
        self,
        destination: str,
        format: str | None = None,
        **options: Any,
    ) -> bytes:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_write(destination, format, **options))
        raise RuntimeError(
            "Cannot call write() synchronously inside an async context. "
            "Use await engine.async_write() instead."
        )

    # --- Internal Helpers ---------------------------------------------------

    def _detect_parser(self, source: str | bytes) -> BaseDocumentParser:
        if isinstance(source, str):
            from pathlib import Path
            path = Path(source)
            for p_cls in _PARSER_MAP.values():
                p = p_cls()
                if p.can_parse(str(path)):
                    return p
        raise ValueError(
            "Cannot auto-detect parser for source. Specify parser_name: "
            f"{', '.join(_PARSER_MAP.keys())}"
        )

    @staticmethod
    def _find_node_recursive(graph: ModelGraph, node_id: str) -> ModelNode | None:
        for node in graph.nodes:
            if node.id == node_id:
                return node
            if node.sub_graph is not None:
                found = MlMiningEngine._find_node_recursive(node.sub_graph, node_id)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _find_nodes_recursive(
        graph: ModelGraph,
        op_type: str | OpType | None,
        name: str | None,
    ) -> list[ModelNode]:
        result: list[ModelNode] = []
        target_op = OpType(op_type) if isinstance(op_type, str) else op_type
        for node in graph.nodes:
            if (target_op is None or node.op_type == target_op) and (
                name is None or node.name == name
            ):
                result.append(node)
            if node.sub_graph is not None:
                result.extend(
                    MlMiningEngine._find_nodes_recursive(node.sub_graph, target_op, name)
                )
        return result

    @staticmethod
    def _traverse_nodes(graph: ModelGraph) -> Iterator[ModelNode]:
        for node in graph.nodes:
            yield node
            if node.sub_graph is not None:
                yield from MlMiningEngine._traverse_nodes(node.sub_graph)

    @staticmethod
    def _traverse_nodes_with_depth(
        graph: ModelGraph,
        depth: int = 0,
    ) -> Iterator[tuple[ModelNode, int]]:
        for node in graph.nodes:
            yield node, depth
            if node.sub_graph is not None:
                yield from MlMiningEngine._traverse_nodes_with_depth(
                    node.sub_graph, depth=depth + 1
                )


__all__ = [
    "MlMiningEngine",
]
