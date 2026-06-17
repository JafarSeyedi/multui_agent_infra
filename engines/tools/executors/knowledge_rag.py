from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.KNOWLEDGE_RAG)
class KnowledgeRagExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._engine = None

    async def _get_engine(self):
        if self._engine is not None:
            return self._engine
        from engines.knowledge.rag.knowledge_rag_engine import KnowledgeRagEngine
        from engines.storage.factories import create_storage
        from engines.document.storage.document_store import DocumentStore
        vector_db = create_storage("vector", backend="memory")
        await vector_db.connect()
        doc_store = DocumentStore()
        self._engine = KnowledgeRagEngine(document_store=doc_store, vector_db=vector_db)
        return self._engine

    @property
    def name(self) -> str:
        return "knowledge_rag"

    @property
    def description(self) -> str:
        return "Unified RAG engine — retrieve, rerank, plan, and reflect over knowledge"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "retrieve")
        query = self.arg(args, ArgName.QUERY, "")
        retriever_name = self.arg(args, ArgName.RETRIEVER_NAME, "vector")
        top_k = int(self.arg(args, ParameterName.TOP_K, "10"))
        rerank_top_k = int(self.arg(args, ArgName.RERANK_TOP_K, "5"))

        try:
            engine = await self._get_engine()

            if action == "retrieve":
                results = await engine.retrieve(query, retriever_name=retriever_name, top_k=top_k)
                return ToolResult(success=True, data={"results": [str(r) for r in results]})
            elif action == "retrieve_rerank":
                results = await engine.retrieve_with_rerank(query, retriever_name=retriever_name, top_k=top_k, rerank_top_k=rerank_top_k)
                return ToolResult(success=True, data={"results": [str(r) for r in results]})
            elif action == "decompose":
                sub_queries = await engine.decompose_query(query)
                return ToolResult(success=True, data={"sub_queries": sub_queries})
            elif action == "plan":
                plan = await engine.create_retrieval_plan(query)
                return ToolResult(success=True, data={"plan": str(plan)})
            elif action == "answer":
                result = await engine.answer_with_agent(query)
                return ToolResult(success=True, data=result)
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
