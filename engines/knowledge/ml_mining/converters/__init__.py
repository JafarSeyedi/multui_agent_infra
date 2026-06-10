from __future__ import annotations

from typing import Any


class ModelGraphConverter:
    """Abstract base for ModelGraph → executable ONNX protobuf converters."""

    def can_convert(self, graph: Any) -> bool:
        raise NotImplementedError

    def convert(self, graph: Any) -> bytes:
        raise NotImplementedError


class ConverterRegistry:
    _converters: list[type[ModelGraphConverter]] = []

    @classmethod
    def register(cls, converter: type[ModelGraphConverter]) -> type[ModelGraphConverter]:
        cls._converters.append(converter)
        return converter

    @classmethod
    def find(cls, graph: Any) -> ModelGraphConverter | None:
        for conv_cls in cls._converters:
            conv = conv_cls()
            try:
                if conv.can_convert(graph):
                    return conv
            except Exception:
                continue
        return None

    @classmethod
    def all_converters(cls) -> list[type[ModelGraphConverter]]:
        return list(cls._converters)


from .tree_converter import TreeConverter
from .regression_converter import RegressionConverter
from .clustering_converter import ClusteringConverter
from .svm_converter import SVMConverter
from .neural_converter import NeuralConverter
from .preprocessing_converter import PreprocessingConverter

__all__ = [
    "ModelGraphConverter",
    "ConverterRegistry",
    "TreeConverter",
    "RegressionConverter",
    "ClusteringConverter",
    "SVMConverter",
    "NeuralConverter",
    "PreprocessingConverter",
]
