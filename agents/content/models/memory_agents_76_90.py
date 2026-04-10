from typing import List, Optional, Dict

from agents.base_agents.models import AgentInput, AgentOutput
from .common import ConfidenceScore, Evidence


# -------------------------------------------------
# Agent 76 — Knowledge Ingestion Agent
# -------------------------------------------------

class KnowledgeIngestionInput(AgentInput):

    source_documents: List[str]

    source_type: Optional[str]


class KnowledgeIngestionOutput(AgentOutput):

    ingested_documents: List[str]

    knowledge_metadata: Optional[Dict]


# -------------------------------------------------
# Agent 77 — Document Chunking Agent
# -------------------------------------------------

class DocumentChunkingInput(AgentInput):

    document_text: str

    chunk_size: Optional[int]


class DocumentChunkingOutput(AgentOutput):

    chunks: List[str]


# -------------------------------------------------
# Agent 78 — Embedding Generator
# -------------------------------------------------

class EmbeddingGeneratorInput(AgentInput):

    texts: List[str]


class EmbeddingGeneratorOutput(AgentOutput):

    embeddings_generated: int


# -------------------------------------------------
# Agent 79 — Semantic Indexer
# -------------------------------------------------

class SemanticIndexerInput(AgentInput):

    embeddings_reference: str

    semantic_metadata: Optional[Dict]


class SemanticIndexerOutput(AgentOutput):

    index_id: str

    indexed_items: int


# -------------------------------------------------
# Agent 80 — Vector Search Agent
# -------------------------------------------------

class VectorSearchInput(AgentInput):

    query: str

    top_k: Optional[int]


class VectorSearchOutput(AgentOutput):

    retrieved_chunks: List[str]

    scores: Optional[List[float]]


# -------------------------------------------------
# Agent 81 — Hybrid Retrieval Agent
# -------------------------------------------------

class HybridRetrievalInput(AgentInput):

    query: str

    vector_results: List[str]

    keyword_results: List[str]


class HybridRetrievalOutput(AgentOutput):

    merged_results: List[str]


# -------------------------------------------------
# Agent 82 — Context Builder Agent
# -------------------------------------------------

class ContextBuilderInput(AgentInput):

    retrieved_chunks: List[str]

    max_context_length: Optional[int]


class ContextBuilderOutput(AgentOutput):

    constructed_context: str


# -------------------------------------------------
# Agent 83 — Memory Consolidation Agent
# -------------------------------------------------

class MemoryConsolidationInput(AgentInput):

    recent_memories: List[str]


class MemoryConsolidationOutput(AgentOutput):

    consolidated_memory: str


# -------------------------------------------------
# Agent 84 — Episodic Memory Agent
# -------------------------------------------------

class EpisodicMemoryInput(AgentInput):

    student_id: str

    session_events: List[str]


class EpisodicMemoryOutput(AgentOutput):

    stored: bool

    episode_id: Optional[str]


# -------------------------------------------------
# Agent 85 — Student Knowledge Memory Agent
# -------------------------------------------------

class StudentKnowledgeMemoryInput(AgentInput):

    student_id: str

    concept_updates: Dict


class StudentKnowledgeMemoryOutput(AgentOutput):

    updated_concepts: List[str]

    confidence: Optional[ConfidenceScore]


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

    conflicting_entries: List[str]


class KnowledgeConflictResolverOutput(AgentOutput):

    resolved_entry: str

    evidence: Optional[List[Evidence]]


# -------------------------------------------------
# Agent 88 — Retrieval Ranker
# -------------------------------------------------

class RetrievalRankerInput(AgentInput):

    query: str

    retrieved_items: List[str]


class RetrievalRankerOutput(AgentOutput):

    ranked_items: List[str]


# -------------------------------------------------
# Agent 89 — Context Relevance Evaluator
# -------------------------------------------------

class ContextRelevanceEvaluatorInput(AgentInput):

    query: str

    context_chunks: List[str]


class ContextRelevanceEvaluatorOutput(AgentOutput):

    relevance_scores: List[float]


# -------------------------------------------------
# Agent 90 — Knowledge Summarizer Agent
# -------------------------------------------------

class KnowledgeSummarizerInput(AgentInput):

    knowledge_chunks: List[str]


class KnowledgeSummarizerOutput(AgentOutput):

    summary: str

    confidence: Optional[ConfidenceScore]
