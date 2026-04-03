from pydantic import BaseModel
from typing import List, Optional, Dict

from .common import ConfidenceScore, Evidence


# -------------------------------------------------
# Agent 76 — Knowledge Ingestion Agent
# -------------------------------------------------

class KnowledgeIngestionInput(BaseModel):

    source_documents: List[str]

    source_type: Optional[str]


class KnowledgeIngestionOutput(BaseModel):

    ingested_documents: List[str]

    metadata: Optional[Dict]


# -------------------------------------------------
# Agent 77 — Document Chunking Agent
# -------------------------------------------------

class DocumentChunkingInput(BaseModel):

    document_text: str

    chunk_size: Optional[int]


class DocumentChunkingOutput(BaseModel):

    chunks: List[str]


# -------------------------------------------------
# Agent 78 — Embedding Generator
# -------------------------------------------------

class EmbeddingGeneratorInput(BaseModel):

    texts: List[str]


class EmbeddingGeneratorOutput(BaseModel):

    embeddings_generated: int


# -------------------------------------------------
# Agent 79 — Semantic Indexer
# -------------------------------------------------

class SemanticIndexerInput(BaseModel):

    embeddings_reference: str

    metadata: Optional[Dict]


class SemanticIndexerOutput(BaseModel):

    index_id: str

    indexed_items: int


# -------------------------------------------------
# Agent 80 — Vector Search Agent
# -------------------------------------------------

class VectorSearchInput(BaseModel):

    query: str

    top_k: Optional[int]


class VectorSearchOutput(BaseModel):

    retrieved_chunks: List[str]

    scores: Optional[List[float]]


# -------------------------------------------------
# Agent 81 — Hybrid Retrieval Agent
# -------------------------------------------------

class HybridRetrievalInput(BaseModel):

    query: str

    vector_results: List[str]

    keyword_results: List[str]


class HybridRetrievalOutput(BaseModel):

    merged_results: List[str]


# -------------------------------------------------
# Agent 82 — Context Builder Agent
# -------------------------------------------------

class ContextBuilderInput(BaseModel):

    retrieved_chunks: List[str]

    max_context_length: Optional[int]


class ContextBuilderOutput(BaseModel):

    constructed_context: str


# -------------------------------------------------
# Agent 83 — Memory Consolidation Agent
# -------------------------------------------------

class MemoryConsolidationInput(BaseModel):

    recent_memories: List[str]


class MemoryConsolidationOutput(BaseModel):

    consolidated_memory: str


# -------------------------------------------------
# Agent 84 — Episodic Memory Agent
# -------------------------------------------------

class EpisodicMemoryInput(BaseModel):

    student_id: str

    session_events: List[str]


class EpisodicMemoryOutput(BaseModel):

    stored: bool

    episode_id: Optional[str]


# -------------------------------------------------
# Agent 85 — Student Knowledge Memory Agent
# -------------------------------------------------

class StudentKnowledgeMemoryInput(BaseModel):

    student_id: str

    concept_updates: Dict


class StudentKnowledgeMemoryOutput(BaseModel):

    updated_concepts: List[str]

    confidence: Optional[ConfidenceScore]


# -------------------------------------------------
# Agent 86 — Knowledge Updater Agent
# -------------------------------------------------

class KnowledgeUpdaterInput(BaseModel):

    existing_knowledge: str

    new_information: str


class KnowledgeUpdaterOutput(BaseModel):

    updated_knowledge: str


# -------------------------------------------------
# Agent 87 — Knowledge Conflict Resolver
# -------------------------------------------------

class KnowledgeConflictResolverInput(BaseModel):

    conflicting_entries: List[str]


class KnowledgeConflictResolverOutput(BaseModel):

    resolved_entry: str

    evidence: Optional[List[Evidence]]


# -------------------------------------------------
# Agent 88 — Retrieval Ranker
# -------------------------------------------------

class RetrievalRankerInput(BaseModel):

    query: str

    retrieved_items: List[str]


class RetrievalRankerOutput(BaseModel):

    ranked_items: List[str]


# -------------------------------------------------
# Agent 89 — Context Relevance Evaluator
# -------------------------------------------------

class ContextRelevanceEvaluatorInput(BaseModel):

    query: str

    context_chunks: List[str]


class ContextRelevanceEvaluatorOutput(BaseModel):

    relevance_scores: List[float]


# -------------------------------------------------
# Agent 90 — Knowledge Summarizer Agent
# -------------------------------------------------

class KnowledgeSummarizerInput(BaseModel):

    knowledge_chunks: List[str]


class KnowledgeSummarizerOutput(BaseModel):

    summary: str

    confidence: Optional[ConfidenceScore]
