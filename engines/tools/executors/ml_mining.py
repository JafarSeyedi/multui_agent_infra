from __future__ import annotations

import json

import numpy as np

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.KNOWLEDGE_ML_MINING)
class MlMiningKnowledgeExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._engine = None

    async def _get_engine(self):
        if self._engine is not None:
            return self._engine
        from engines.knowledge.ml_mining import MlMiningEngine
        self._engine = MlMiningEngine()
        return self._engine

    @property
    def name(self) -> str:
        return "knowledge_ml_mining"

    @property
    def description(self) -> str:
        return "ML mining engine — load, parse, query, and run inference on ML models (PMML/ONNX/sklearn/PyTorch)"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "info")
        source_path = self.arg(args, ParameterName.SOURCE, "")
        model_format = self.arg(args, ArgName.MODEL_FORMAT, "")
        parser_name = self.arg(args, ParameterName.PARSER_NAME, "")
        op_type = self.arg(args, ParameterName.OP_TYPE, "")
        field_name = self.arg(args, ParameterName.FIELD_NAME, "")
        target_format = self.arg(args, ParameterName.TARGET_FORMAT, "")
        x_data_str = self.arg(args, ArgName.X_DATA, "[]")
        y_data_str = self.arg(args, ArgName.Y_DATA, "[]")
        metrics_str = self.arg(args, ArgName.METRICS, "[]")

        try:
            engine = await self._get_engine()

            if action == "load":
                if source_path:
                    doc = await engine.async_load(source_path, parser_name=parser_name or None)
                elif model_format:
                    from engines.knowledge.ml_mining.models import ModelFormat
                    doc = await engine.async_parse("", model_format=ModelFormat(model_format))
                else:
                    return ToolResult(success=False, error="source_path or model_format required")
                return ToolResult(success=True, data={"document_id": doc.document_id if hasattr(doc, "document_id") else "", "title": doc.title if hasattr(doc, "title") else ""})

            elif action == "info":
                info = engine.get_model_info()
                return ToolResult(success=True, data=info)

            elif action == "get_fields":
                fields = engine.get_fields(usage_type=field_name or None)
                return ToolResult(success=True, data={"fields": [str(f) for f in fields]})

            elif action == "find_nodes":
                nodes = engine.find_nodes(op_type=op_type or None)
                return ToolResult(success=True, data={"nodes": [str(n) for n in nodes]})

            elif action == "get_graph":
                graph = engine.get_graph()
                if graph:
                    return ToolResult(success=True, data={"n_nodes": len(graph.nodes)})
                return ToolResult(success=True, data={"n_nodes": 0})

            elif action == "predict":
                x_data = np.array(json.loads(x_data_str), dtype=np.float32)
                predictions = await engine.predict(x_data)
                return ToolResult(success=True, data={"predictions": predictions.tolist()})

            elif action == "evaluate":
                x_data = np.array(json.loads(x_data_str), dtype=np.float32)
                y_data = np.array(json.loads(y_data_str), dtype=np.float32)
                metrics = json.loads(metrics_str) if metrics_str else None
                results = await engine.evaluate(x_data, y_data, metrics=metrics)
                return ToolResult(success=True, data=results)

            elif action == "convert":
                if target_format:
                    result = await engine.async_convert(target_format)
                    return ToolResult(success=True, data={"result": result.decode("utf-8", errors="replace")})
                return ToolResult(success=False, error="target_format required")

            elif action == "validate":
                warnings = engine.validate()
                return ToolResult(success=True, data={"warnings": warnings})

            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
