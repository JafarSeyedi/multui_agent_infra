from ...models import AgentInput
from ...models import AgentOutput
from .common import ConfidenceScore
from .common import Evidence


# -------------------------------------------------
# Agent 76 — Knowledge Ingestion Agent
# -------------------------------------------------

class KnowledgeIngestionInput(AgentInput):

    source_documents: list[str]

    source_type: str | None


class KnowledgeIngestionOutput(AgentOutput):

    ingested_documents: list[str]

    knowledge_metadata: dict | None


# -------------------------------------------------
# Agent 77 — Document Chunking Agent
# -------------------------------------------------

class DocumentChunkingInput(AgentInput):

    document_text: str

    chunk_size: int | None


class DocumentChunkingOutput(AgentOutput):

    chunks: list[str]


# -------------------------------------------------
# Agent 78 — Embedding Generator
# -------------------------------------------------

class EmbeddingGeneratorInput(AgentInput):

    texts: list[str]


class EmbeddingGeneratorOutput(AgentOutput):

    embeddings_generated: int


# -------------------------------------------------
# Agent 79 — Semantic Indexer
# -------------------------------------------------

class SemanticIndexerInput(AgentInput):

    embeddings_reference: str

    semantic_metadata: dict | None


class SemanticIndexerOutput(AgentOutput):

    index_id: str

    indexed_items: int


# -------------------------------------------------
# Agent 80 — Vector Search Agent
# -------------------------------------------------

class VectorSearchInput(AgentInput):

    query: str

    top_k: int | None


class VectorSearchOutput(AgentOutput):

    retrieved_chunks: list[str]

    scores: list[float] | None


# -------------------------------------------------
# Agent 81 — Hybrid Retrieval Agent
# -------------------------------------------------

class HybridRetrievalInput(AgentInput):

    query: str

    vector_results: list[str]

    keyword_results: list[str]


class HybridRetrievalOutput(AgentOutput):

    merged_results: list[str]


# -------------------------------------------------
# Agent 82 — Context Builder Agent
# -------------------------------------------------

class ContextBuilderInput(AgentInput):

    retrieved_chunks: list[str]

    max_context_length: int | None


class ContextBuilderOutput(AgentOutput):

    constructed_context: str


# -------------------------------------------------
# Agent 83 — Memory Consolidation Agent
# -------------------------------------------------

class MemoryConsolidationInput(AgentInput):

    recent_memories: list[str]


class MemoryConsolidationOutput(AgentOutput):

    consolidated_memory: str


# -------------------------------------------------
# Agent 84 — Episodic Memory Agent
# -------------------------------------------------

class EpisodicMemoryInput(AgentInput):

    student_id: str

    session_events: list[str]


class EpisodicMemoryOutput(AgentOutput):

    stored: bool

    episode_id: str | None


# -------------------------------------------------
# Agent 85 — Student Knowledge Memory Agent
# -------------------------------------------------

class StudentKnowledgeMemoryInput(AgentInput):

    student_id: str

    concept_updates: dict


class StudentKnowledgeMemoryOutput(AgentOutput):

    updated_concepts: list[str]

    confidence: ConfidenceScore | None


# -------------------------------------------------
# Agent 86 — Knowledge Updater Agent
# -------------------------------------------------

class KnowledgeUpdaterInput(AgentInput):

    existing_knowledge: str

    new_information: str


class KnowledgeUpdaterOutput(AgentOutput):

    updated_knowledge: str


# -------------------------------------------------
# Agent 87 — Knowledge Conflict Resolver
# -------------------------------------------------

class KnowledgeConflictResolverInput(AgentInput):

    conflicting_entries: list[str]


class KnowledgeConflictResolverOutput(AgentOutput):

    resolved_entry: str

    evidence: list[Evidence] | None


# -------------------------------------------------
# Agent 88 — Retrieval Ranker
# -------------------------------------------------

class RetrievalRankerInput(AgentInput):

    query: str

    retrieved_items: list[str]


class RetrievalRankerOutput(AgentOutput):

    ranked_items: list[str]


# -------------------------------------------------
# Agent 89 — Context Relevance Evaluator
# -------------------------------------------------

class ContextRelevanceEvaluatorInput(AgentInput):

    query: str

    context_chunks: list[str]


class ContextRelevanceEvaluatorOutput(AgentOutput):

    relevance_scores: list[float]


# -------------------------------------------------
# Agent 90 — Knowledge Summarizer Agent
# -------------------------------------------------

class KnowledgeSummarizerInput(AgentInput):

    knowledge_chunks: list[str]


class KnowledgeSummarizerOutput(AgentOutput):

    summary: str

    confidence: ConfidenceScore | None
