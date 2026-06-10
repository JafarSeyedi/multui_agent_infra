from __future__ import annotations

import io
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from engines.document.models.ksdm_models import (
    MiningModelType,
    ModelFormat,
    ModelGraph,
    ModelNode,
    MlMiningDocument,
    OpType,
)
from engines.document.parsers.ksdm_parsers.ml_mining import SklearnParser
from engines.knowledge.ml_mining import MlMiningEngine
from engines.knowledge.ml_mining.converters import ConverterRegistry
from engines.knowledge.ml_mining.metrics import MetricsCalculator
from engines.knowledge.ml_mining.validation import (
    validate_document,
    validate_graph,
    validate_mining_schema,
)


# ============================================================
#  Sklearn Parser Tests
# ============================================================

class TestSklearnParser:

    @pytest.mark.asyncio
    async def test_parse_decision_tree(self):
        from sklearn.tree import DecisionTreeClassifier  # type: ignore[import-untyped]
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit([[0, 0], [1, 1], [2, 2], [3, 3]], [0, 0, 1, 1])
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "dt", "dt.pkl")
        assert doc.model_type == MiningModelType.DECISION_TREE
        assert doc.model_format == ModelFormat.SKLEARN
        assert doc.model_graph is not None
        assert len(doc.model_graph.nodes) >= 1
        assert doc.title == "dt.pkl"

    @pytest.mark.asyncio
    async def test_parse_random_forest(self):
        from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-untyped]
        model = RandomForestClassifier(n_estimators=5, max_depth=3, random_state=42)
        model.fit([[0, 0], [1, 1], [2, 2], [3, 3]], [0, 0, 1, 1])
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "rf", "rf.pkl")
        assert doc.model_type == MiningModelType.DECISION_TREE
        assert doc.model_format == ModelFormat.SKLEARN
        assert doc.model_graph is not None

    @pytest.mark.asyncio
    async def test_parse_svm(self):
        from sklearn.svm import SVC  # type: ignore[import-untyped]
        model = SVC(C=1.0, kernel="rbf", gamma="scale", random_state=42)
        model.fit([[0, 0], [1, 1], [2, 2]], [0, 1, 0])
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "svm", "svm.pkl")
        assert doc.model_type == MiningModelType.SVM
        assert doc.model_format == ModelFormat.SKLEARN

    @pytest.mark.asyncio
    async def test_parse_kmeans(self):
        from sklearn.cluster import KMeans  # type: ignore[import-untyped]
        model = KMeans(n_clusters=3, random_state=42, n_init="auto")
        model.fit([[0, 0], [1, 1], [2, 2], [8, 8], [9, 9], [10, 10]])
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "km", "km.pkl")
        assert doc.model_type == MiningModelType.CLUSTERING
        assert doc.model_format == ModelFormat.SKLEARN

    @pytest.mark.asyncio
    async def test_parse_mlp(self):
        from sklearn.neural_network import MLPClassifier  # type: ignore[import-untyped]
        model = MLPClassifier(hidden_layer_sizes=(4,), max_iter=100, random_state=42)
        model.fit([[0, 0], [1, 1], [2, 2], [3, 3]], [0, 0, 1, 1])
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "mlp", "mlp.pkl")
        assert doc.model_type == MiningModelType.NEURAL_NETWORK


# ============================================================
#  PyTorch Parser Tests
# ============================================================

class TestPyTorchParser:

    @pytest.mark.asyncio
    async def test_parse_torchscript(self):
        import torch
        model = torch.nn.Sequential(
            torch.nn.Linear(4, 8),
            torch.nn.ReLU(),
            torch.nn.Linear(8, 3),
        )
        buf = io.BytesIO()
        traced = torch.jit.trace(model, torch.randn(1, 4))
        torch.jit.save(traced, buf)
        data = buf.getvalue()
        from engines.document.parsers.ksdm_parsers.ml_mining import PyTorchParser
        parser = PyTorchParser()
        doc = await parser.parse_bytes(data, "pt", "pt.pt")
        assert doc.model_format == ModelFormat.PYTORCH
        assert doc.model_graph is not None
        assert len(doc.model_graph.nodes) >= 1

    @pytest.mark.asyncio
    async def test_parse_pickle_pytorch(self):
        import torch
        model = torch.nn.Linear(4, 2)
        buf = io.BytesIO()
        torch.save(model.state_dict(), buf)
        data = buf.getvalue()
        from engines.document.parsers.ksdm_parsers.ml_mining import PyTorchParser
        parser = PyTorchParser()
        doc = await parser.parse_bytes(data, "pt2", "pt2.pt")
        assert doc.model_format == ModelFormat.PYTORCH
        assert doc.model_graph is not None


# ============================================================
#  Converter → ONNX Runtime Inference Tests
# ============================================================

class TestTreeConverterInference:

    @pytest.mark.asyncio
    async def _train_tree_doc(self) -> Any:
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=4, random_state=42)
        X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4],
                       [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]], dtype=np.float64)
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        model.fit(X, y)
        data = pickle.dumps(model)
        parser = SklearnParser()
        return await parser.parse_bytes(data, "tree_test", "tree.pkl")

    @pytest.mark.asyncio
    async def test_tree_converter_onnx_runtime(self):
        doc = await self._train_tree_doc()
        assert doc.model_graph is not None
        converter = ConverterRegistry.find(doc.model_graph)
        assert converter is not None, "No converter found for tree graph"
        onnx_bytes = converter.convert(doc.model_graph)
        import onnxruntime  # type: ignore[import-untyped]
        sess = onnxruntime.InferenceSession(onnx_bytes, providers=["CPUExecutionProvider"])
        X_test = np.array([[0, 0], [9, 9]], dtype=np.float32)
        outputs = sess.run(None, {"X": X_test})
        assert len(outputs) >= 1
        assert outputs[0].shape[0] == 2

    @pytest.mark.asyncio
    async def test_rf_converter_onnx_runtime(self):
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=3, max_depth=3, random_state=42)
        X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4],
                       [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]], dtype=np.float64)
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        model.fit(X, y)
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "rf_test", "rf.pkl")
        assert doc.model_graph is not None
        converter = ConverterRegistry.find(doc.model_graph)
        assert converter is not None
        onnx_bytes = converter.convert(doc.model_graph)
        import onnxruntime  # type: ignore[import-untyped]
        sess = onnxruntime.InferenceSession(onnx_bytes, providers=["CPUExecutionProvider"])
        outputs = sess.run(None, {"X": np.array([[0, 0], [9, 9]], dtype=np.float32)})
        assert outputs[0].shape[0] == 2


# ============================================================
#  Engine predict/evaluate tests
# ============================================================

class TestEngineInference:

    @pytest.mark.asyncio
    async def test_engine_predict(self):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        X = np.array([[0, 0], [1, 1], [2, 2], [3, 3],
                       [4, 4], [5, 5], [6, 6], [7, 7],
                       [8, 8], [9, 9]], dtype=np.float64)
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        model.fit(X, y)
        data = pickle.dumps(model)
        engine = MlMiningEngine()
        await engine.async_parse(data)
        engine._doc.model_graph = engine._doc.model_graph  # ensure graph exists
        preds = await engine.predict(np.array([[0, 0], [9, 9]], dtype=np.float32))
        assert preds.shape[0] == 2

    @pytest.mark.asyncio
    async def test_engine_evaluate(self):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        X = np.array([[0, 0], [1, 1], [2, 2], [3, 3],
                       [4, 4], [5, 5], [6, 6], [7, 7],
                       [8, 8], [9, 9]], dtype=np.float64)
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        model.fit(X, y)
        data = pickle.dumps(model)
        engine = MlMiningEngine()
        await engine.async_parse(data)
        engine._doc.model_graph = engine._doc.model_graph
        results = await engine.evaluate(
            np.array([[0, 0], [9, 9], [1, 1], [8, 8]], dtype=np.float32),
            np.array([0, 1, 0, 1]),
            metrics=["accuracy", "f1"],
        )
        assert "accuracy" in results
        assert "f1" in results
        assert 0.0 <= results["accuracy"] <= 1.0

    @pytest.mark.asyncio
    async def test_engine_get_model_info(self):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit([[0, 0], [1, 1]], [0, 1])
        data = pickle.dumps(model)
        engine = MlMiningEngine()
        await engine.async_parse(data)
        info = engine.get_model_info()
        assert info["status"] != "no_document"
        assert info["model_type"] == MiningModelType.DECISION_TREE.value
        assert info["model_format"] == ModelFormat.SKLEARN.value

    @pytest.mark.asyncio
    async def test_engine_validate(self):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit([[0, 0], [1, 1]], [0, 1])
        data = pickle.dumps(model)
        engine = MlMiningEngine()
        await engine.async_parse(data)
        warnings = engine.validate()
        assert isinstance(warnings, list)


# ============================================================
#  Metrics Tests
# ============================================================

class TestMetrics:

    def test_accuracy(self):
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0])
        result = MetricsCalculator.calc(y_true, y_pred, ["accuracy"])
        assert result["accuracy"] == 0.75

    def test_classification_metrics(self):
        y_true = np.array([1, 1, 0, 0, 1, 0])
        y_pred = np.array([1, 0, 0, 0, 1, 1])
        r = MetricsCalculator.calc(y_true, y_pred, ["accuracy", "precision", "recall", "f1"])
        assert "accuracy" in r
        assert "precision" in r
        assert "recall" in r
        assert "f1" in r

    def test_regression_metrics(self):
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.1, 1.9, 3.2, 3.8])
        r = MetricsCalculator.calc(y_true, y_pred, ["mse", "rmse", "mae", "r2"])
        assert "mse" in r
        assert r["mse"] > 0
        assert "rmse" in r
        assert "mae" in r
        assert "r2" in r

    def test_mape(self):
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([110.0, 190.0, 290.0])
        r = MetricsCalculator.calc(y_true, y_pred, ["mape"])
        assert "mape" in r

    def test_empty_metric_list_defaults(self):
        y_true = np.array([0, 1, 0])
        y_pred = np.array([0, 1, 0])
        r = MetricsCalculator.calc(y_true, y_pred)
        assert len(r) >= 5


# ============================================================
#  Validation Tests
# ============================================================

class TestValidation:

    def test_validate_document_empty(self):
        from engines.document.models.media_types import MEDIA_TYPES
        doc = MlMiningDocument(title="test", document_id="test", media_type=MEDIA_TYPES["txt"])
        warnings = validate_document(doc)
        assert len(warnings) >= 1

    def test_validate_graph_no_nodes(self):
        from engines.document.models.ksdm_models import ModelGraph
        graph = ModelGraph(nodes=[])
        warnings = validate_graph(graph)
        assert "Graph has no nodes" in warnings

    def test_validate_graph_duplicate_ids(self):
        graph = ModelGraph(nodes=[
            ModelNode(id="a", op_type=OpType.RELU),
            ModelNode(id="a", op_type=OpType.SIGMOID),
        ])
        warnings = validate_graph(graph)
        assert any("Duplicate" in w for w in warnings)

    def test_validate_mining_schema(self):
        from engines.document.models.ksdm_models import (
            MiningField,
            MiningSchema,
        )
        schema = MiningSchema(fields=[])
        warnings = validate_mining_schema(schema)
        assert any("no fields" in w.lower() for w in warnings)

    def test_validate_engine(self):
        from engines.document.models.media_types import MEDIA_TYPES
        engine = MlMiningEngine()
        engine._doc = MlMiningDocument(title="test", document_id="test", media_type=MEDIA_TYPES["txt"])
        warnings = engine.validate()
        assert isinstance(warnings, list)


# ============================================================
#  Full Pipeline Integration Test
# ============================================================

class TestFullPipeline:

    @pytest.mark.asyncio
    async def test_train_parse_convert_predict(self):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=4, random_state=42)
        X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4],
                       [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]], dtype=np.float64)
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        model.fit(X, y)

        data = pickle.dumps(model)

        engine = MlMiningEngine()
        doc = await engine.async_parse(data)
        assert doc.model_graph is not None

        onnx_bytes = await engine.async_convert("onnx_runtime")
        assert len(onnx_bytes) > 0

        import onnxruntime  # type: ignore[import-untyped]
        sess = onnxruntime.InferenceSession(onnx_bytes, providers=["CPUExecutionProvider"])
        preds = sess.run(None, {"X": np.array([[0, 0], [9, 9]], dtype=np.float32)})[0]
        assert preds.shape[0] == 2


# ============================================================
#  SVM Converter Test
# ============================================================

class TestSVMConverter:

    @pytest.mark.asyncio
    async def test_svm_parse_and_convert(self):
        from sklearn.svm import SVC
        model = SVC(C=1.0, kernel="rbf", gamma="scale", probability=False, random_state=42)
        X = np.array([[0, 0], [1, 1], [2, 2], [8, 8], [9, 9], [10, 10]], dtype=np.float64)
        y = np.array([0, 0, 0, 1, 1, 1])
        model.fit(X, y)
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "svm_test", "svm.pkl")
        assert doc.model_graph is not None
        converter = ConverterRegistry.find(doc.model_graph)
        assert converter is not None


# ============================================================
#  Clustering Converter Test
# ============================================================

class TestClusteringConverter:

    @pytest.mark.asyncio
    async def test_kmeans_parse_and_convert(self):
        from sklearn.cluster import KMeans
        model = KMeans(n_clusters=2, random_state=42, n_init="auto")
        X = np.array([[0, 0], [0, 1], [1, 0], [8, 8], [9, 9], [10, 10]], dtype=np.float64)
        model.fit(X)
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "km_test", "km.pkl")
        assert doc.model_graph is not None
        converter = ConverterRegistry.find(doc.model_graph)
        assert converter is not None


# ============================================================
#  ConverterRegistry Tests
# ============================================================

class TestConverterRegistry:

    def test_registry_finds_tree_converter(self):
        graph = ModelGraph(
            nodes=[
                ModelNode(id="t1", op_type=OpType.TREE_SPLIT),
                ModelNode(id="l1", op_type=OpType.LEAF),
            ]
        )
        converter = ConverterRegistry.find(graph)
        assert converter is not None

    def test_registry_returns_none_for_unknown(self):
        graph = ModelGraph(
            nodes=[
                ModelNode(id="u1", op_type=OpType.CUSTOM),
            ]
        )
        converter = ConverterRegistry.find(graph)
        assert converter is None


# ============================================================
#  Auto-Detection Tests
# ============================================================


class TestAutoDetect:

    @pytest.mark.asyncio
    async def test_auto_detect_sklearn_pickle(self):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(max_depth=2, random_state=42)
        model.fit([[0], [1], [2], [3]], [0, 0, 1, 1])
        data = pickle.dumps(model)
        engine = MlMiningEngine()
        doc = await engine.async_parse(data)
        assert doc.model_format == ModelFormat.SKLEARN

    @pytest.mark.asyncio
    async def test_auto_detect_onnx(self):
        import onnx
        from onnx import helper, TensorProto as TP
        graph_def = helper.make_graph(
            [helper.make_node("Identity", ["X"], ["Y"])],
            "test",
            [helper.make_tensor_value_info("X", TP.FLOAT, [None, 2])],
            [helper.make_tensor_value_info("Y", TP.FLOAT, [None, 2])],
        )
        model_def = helper.make_model(graph_def, opset_imports=[helper.make_opsetid("", 20)])
        data = model_def.SerializeToString()
        engine = MlMiningEngine()
        doc = await engine.async_parse(data)
        assert doc.model_format == ModelFormat.ONNX


# ============================================================
#  Regression Converter Test
# ============================================================

class TestRegressionConverter:

    @pytest.mark.asyncio
    async def test_linear_regression_parse_and_convert(self):
        from sklearn.linear_model import LinearRegression  # type: ignore[import-untyped]
        model = LinearRegression()
        X = np.array([[1], [2], [3], [4], [5]], dtype=np.float64)
        y = np.array([2, 4, 6, 8, 10], dtype=np.float64)
        model.fit(X, y)
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "lr_test", "lr.pkl")
        assert doc.model_graph is not None
        converter = ConverterRegistry.find(doc.model_graph)
        assert converter is not None
        onnx_bytes = converter.convert(doc.model_graph)
        import onnxruntime  # type: ignore[import-untyped]
        sess = onnxruntime.InferenceSession(onnx_bytes, providers=["CPUExecutionProvider"])
        preds = sess.run(None, {"X": np.array([[6], [7]], dtype=np.float32)})[0]
        assert preds.shape[0] == 2

    @pytest.mark.asyncio
    async def test_logistic_regression_parse_and_convert(self):
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42, max_iter=200)
        X = np.array([[0], [1], [2], [8], [9], [10]], dtype=np.float64)
        y = np.array([0, 0, 0, 1, 1, 1])
        model.fit(X, y)
        data = pickle.dumps(model)
        parser = SklearnParser()
        doc = await parser.parse_bytes(data, "logit_test", "logit.pkl")
        assert doc.model_graph is not None
        converter = ConverterRegistry.find(doc.model_graph)
        assert converter is not None
        onnx_bytes = converter.convert(doc.model_graph)
        import onnxruntime  # type: ignore[import-untyped]
        sess = onnxruntime.InferenceSession(onnx_bytes, providers=["CPUExecutionProvider"])
        preds = sess.run(None, {"X": np.array([[0], [10]], dtype=np.float32)})
        assert len(preds) >= 1


# ============================================================
#  Metrics Edge Cases
# ============================================================

class TestMetricsEdgeCases:

    def test_perfect_prediction(self):
        y = np.array([1, 2, 3, 4, 5])
        r = MetricsCalculator.calc(y, y, ["accuracy", "mse", "r2"])
        assert r["mse"] == 0.0
        assert r["r2"] == 1.0

    def test_all_wrong(self):
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([1, 1, 1, 1])
        r = MetricsCalculator.calc(y_true, y_pred, ["accuracy", "f1"])
        assert r["accuracy"] == 0.0

    def test_single_element(self):
        y_true = np.array([42.0])
        y_pred = np.array([40.0])
        r = MetricsCalculator.calc(y_true, y_pred, ["mse", "mae"])
        assert r["mse"] == 4.0
        assert r["mae"] == 2.0

    def test_mismatched_lengths(self):
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2])
        r = MetricsCalculator.calc(y_true, y_pred, ["mse"])
        assert "mse" in r
