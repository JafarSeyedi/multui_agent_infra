from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.KNOWLEDGE_PROCESS_MINING)
class ProcessMiningKnowledgeExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._engine = None

    async def _get_engine(self):
        if self._engine is not None:
            return self._engine
        from engines.knowledge.process_mining import ProcessMiningEngine
        self._engine = ProcessMiningEngine()
        return self._engine

    @property
    def name(self) -> str:
        return "knowledge_process_mining"

    @property
    def description(self) -> str:
        return "Process mining engine — discover, analyze decision points, and mine event logs"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "get_statistics")
        source_path = self.arg(args, ParameterName.SOURCE, "")
        source_content = self.arg(args, ArgName.INPUT, "")
        source_fmt = self.arg(args, ArgName.MODEL_FORMAT, "jprm")
        activity_key = self.arg(args, ParameterName.ACTIVITY_KEY, "concept:name")
        decision_point_id = self.arg(args, ParameterName.DECISION_POINT_ID, "")

        try:
            engine = await self._get_engine()

            if action == "load":
                if source_path:
                    doc = engine.load(source_path)
                elif source_content:
                    doc = engine.loads(source_content, fmt=source_fmt)
                else:
                    return ToolResult(success=False, error="source_path or source_content required")
                return ToolResult(success=True, data={"document_id": doc.document_id if hasattr(doc, "document_id") else "", "title": doc.title if hasattr(doc, "title") else ""})

            elif action == "get_statistics":
                from engines.knowledge.process_mining.models import ProcessMiningDefinitionDocument
                doc = ProcessMiningDefinitionDocument(
                    title="default",
                    document_id="default",
                )
                stats = engine.get_statistics(doc)
                return ToolResult(success=True, data=stats)

            elif action == "validate":
                from engines.knowledge.process_mining.models import ProcessMiningDefinitionDocument
                doc = ProcessMiningDefinitionDocument(
                    title="default",
                    document_id="default",
                )
                warnings = engine.validate(doc)
                return ToolResult(success=True, data={"warnings": warnings})

            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
