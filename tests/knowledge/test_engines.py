# tests/knowledge/test_engines.py
"""
Tests for knowledge runtime engines.
"""
import pytest
import asyncio

from engines.knowledge.bi_aggregation.engine import BiAggregationEngine
from engines.knowledge.ml_mining.engine import MlMiningEngine
from engines.knowledge.semantic_graph.engine import SemanticGraphEngine
from engines.knowledge.graph.engine import UnifiedGraphEngine


def test_bi_aggregation_engine_init():
    engine = BiAggregationEngine()
    assert engine._parsers == {}
    assert engine._writers == {}


def test_ml_mining_engine_init():
    engine = MlMiningEngine()
    assert engine._parsers == {}
    assert engine._writers == {}


def test_semantic_graph_engine_init():
    engine = SemanticGraphEngine()
    assert engine._parsers == {}
    assert engine._writers == {}


def test_unified_graph_engine_init():
    engine = UnifiedGraphEngine()
    assert engine._parsers == {}
    assert engine._writers == {}


def test_unified_graph_engine_no_parser():
    engine = UnifiedGraphEngine()
    with pytest.raises((NotImplementedError, TypeError)):
        asyncio.get_event_loop().run_until_complete(engine.parse("test.ttl"))


def test_rag_engine_init():
    try:
        from engines.knowledge.rag.knowledge_rag_engine import KnowledgeRagEngine
        engine = KnowledgeRagEngine()
        assert engine._parsers == {}
        assert engine._writers == {}
    except ImportError:
        pytest.skip("KnowledgeRagEngine dependencies not available")


def test_memory_engine_init():
    try:
        from engines.knowledge.memory.knowledge_memory_engine import KnowledgeMemoryEngine
        engine = KnowledgeMemoryEngine()
        assert engine._parsers == {}
        assert engine._writers == {}
    except ImportError:
        pytest.skip("KnowledgeMemoryEngine dependencies not available")


def test_knowledge_rag_engine_import():
    try:
        from engines.knowledge.rag.knowledge_rag_engine import KnowledgeRagEngine
        assert KnowledgeRagEngine is not None
    except ImportError:
        pytest.skip("KnowledgeRagEngine dependencies not available")


