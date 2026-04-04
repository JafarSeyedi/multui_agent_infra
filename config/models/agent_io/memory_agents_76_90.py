from pydantic import BaseModel
from typing import List, Optional, Dict

from .common import ConfidenceScore, Evidence


# -------------------------------------------------
# Agent 76 — Knowledge Ingestion Agent
# -------------------------------------------------

class KnowledgeIngestionInput(OrchestrationRequest):

    source_documents: List[str]

    source_type: Optional[str]


class KnowledgeIngestionOutput(OrchestrationResult):

    ingested_documents: List[str]

    metadata: Optional[Dict]


# -------------------------------------------------
# Agent 77 — Document Chunking Agent
# -------------------------------------------------

class DocumentChunkingInput(OrchestrationRequest):

    document_text: str

    chunk_size: Optional[int]


class DocumentChunkingOutput(OrchestrationResult):

    chunks: List[str]


# -------------------------------------------------
# Agent 78 — Embedding Generator
# -------------------------------------------------

class EmbeddingGeneratorInput(OrchestrationRequest):

    texts: List[str]


class EmbeddingGeneratorOutput(OrchestrationResult):

    embeddings_generated: int


# -------------------------------------------------
# Agent 79 — Semantic Indexer
# -------------------------------------------------

class SemanticIndexerInput(OrchestrationRequest):

    embeddings_reference: str

    metadata: Optional[Dict]


class SemanticIndexerOutput(OrchestrationResult):

    index_id: str

    indexed_items: int


# -------------------------------------------------
# Agent 80 — Vector Search Agent
# -------------------------------------------------

class VectorSearchInput(OrchestrationRequest):

    query: str

    top_k: Optional[int]


class VectorSearchOutput(OrchestrationResult):

    retrieved_chunks: List[str]

    scores: Optional[List[float]]


# -------------------------------------------------
# Agent 81 — Hybrid Retrieval Agent
# -------------------------------------------------

class HybridRetrievalInput(OrchestrationRequest):

    query: str

    vector_results: List[str]

    keyword_results: List[str]


class HybridRetrievalOutput(OrchestrationResult):

    merged_results: List[str]


# -------------------------------------------------
# Agent 82 — Context Builder Agent
# -------------------------------------------------

class ContextBuilderInput(OrchestrationRequest):

    retrieved_chunks: List[str]

    max_context_length: Optional[int]


class ContextBuilderOutput(OrchestrationResult):

    constructed_context: str


# -------------------------------------------------
# Agent 83 — Memory Consolidation Agent
# -------------------------------------------------

class MemoryConsolidationInput(OrchestrationRequest):

    recent_memories: List[str]


class MemoryConsolidationOutput(OrchestrationResult):

    consolidated_memory: str


# -------------------------------------------------
# Agent 84 — Episodic Memory Agent
# -------------------------------------------------

class EpisodicMemoryInput(OrchestrationRequest):

    student_id: str

    session_events: List[str]


class EpisodicMemoryOutput(OrchestrationResult):

    stored: bool

    episode_id: Optional[str]


# -------------------------------------------------
# Agent 85 — Student Knowledge Memory Agent
# -------------------------------------------------

class StudentKnowledgeMemoryInput(OrchestrationRequest):

    student_id: str

    concept_updates: Dict


class StudentKnowledgeMemoryOutput(OrchestrationResult):

    updated_concepts: List[str]

    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 86 — Knowledge Updater Agent
# -------------------------------------------------

class KnowledgeUpdaterInput(OrchestrationRequest):

    existing_knowledge: str

    new_information: str


class KnowledgeUpdaterOutput(OrchestrationResult):

    updated_knowledge: str


# -------------------------------------------------
# Agent 87 — Knowledge Conflict Resolver
# -------------------------------------------------

class KnowledgeConflictResolverInput(OrchestrationRequest):

    conflicting_entries: List[str]


class KnowledgeConflictResolverOutput(OrchestrationResult):

    resolved_entry: str

    evidence: Optional[List[Evidence]]


# -------------------------------------------------
# Agent 88 — Retrieval Ranker
# -------------------------------------------------

class RetrievalRankerInput(OrchestrationRequest):

    query: str

    retrieved_items: List[str]


class RetrievalRankerOutput(OrchestrationResult):

    ranked_items: List[str]


# -------------------------------------------------
# Agent 89 — Context Relevance Evaluator
# -------------------------------------------------

class ContextRelevanceEvaluatorInput(OrchestrationRequest):

    query: str

    context_chunks: List[str]


class ContextRelevanceEvaluatorOutput(OrchestrationResult):

    relevance_scores: List[float]


# -------------------------------------------------
# Agent 90 — Knowledge Summarizer Agent
# -------------------------------------------------

class KnowledgeSummarizerInput(OrchestrationRequest):

    knowledge_chunks: List[str]


class KnowledgeSummarizerOutput(OrchestrationResult):

    summary: str

    confidence: Optional[ConfidenceScore]
