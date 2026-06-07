# rag/research/memory/reasoning/event_types.py
from enum import Enum


class ReasoningEventType(str, Enum):

    PLANNING = "planning"

    RETRIEVAL_VECTOR = "retrieval_vector"
    RETRIEVAL_KEYWORD = "retrieval_keyword"
    RETRIEVAL_GRAPH = "retrieval_graph"

    GRAPH_REASONING = "graph_reasoning"
    GRAPH_TRAVERSAL = "graph_traversal"

    QUERY_EXPANSION = "query_expansion"

    EVIDENCE_FILTERING = "evidence_filtering"
    EVIDENCE_FUSION = "evidence_fusion"

    SUMMARIZATION = "summarization"
    CITATION = "citation"

    MEMORY_STORE = "memory_store"
    MEMORY_RECALL = "memory_recall"

    ERROR = "error"
    SYSTEM = "system"
