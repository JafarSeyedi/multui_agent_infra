from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engines.knowledge.ml_mining.models import MiningModelType
from engines.knowledge.process_mining.models import (
    ClusteringConfig,
    DecisionPointDefinition,
    CatchEventMiningDefinition,
    MiningProcessDefinition,
    ProcessMiningDefinitionDocument,
)
from engines.document.models.lsdm_models import (
    EventLogDocument,
    LogAttribute,
    LogEvent,
    LogSource,
    XesTrace,
)
from engines.document.models.media_types import MEDIA_TYPES
from engines.orchestration.dmn.models.dmn_models import DecisionLogicType
from engines.document.models.standard import DocumentStandard
from engines.knowledge.process_mining.models.parsers.jprm_parser import JprmParser
from engines.knowledge.process_mining.models.parsers.yprm_parser import YprmParser
from engines.knowledge.process_mining.models.writers.jprm_writer import JprmWriter
from engines.knowledge.process_mining.models.writers.yprm_writer import YprmWriter
from engines.knowledge.process_mining import ProcessMiningEngine


_JPRM_MEDIA = MEDIA_TYPES["jprm_json"]
_YPRM_MEDIA = MEDIA_TYPES["yprm_yaml"]

_SAMPLE_JPRM = """{
    "title": "Test Process",
    "metadata": {},
    "processes": {
        "p1": {
            "description": "Test process",
            "decision_points": {
                "dp1": {
                    "description": "Check approval",
                    "mining_algorithm": "decision_tree"
                }
            },
            "catch_event_definitions": {
                "ce1": {
                    "description": "Monitor timeout",
                    "clustering_config": {
                        "algorithm": "clustering",
                        "n_clusters": 3
                    }
                }
            },
            "mining_name": "test_mining"
        }
    },
    "default_clustering_config": {
        "algorithm": "clustering",
        "n_clusters": 2
    }
}"""


def _make_sample_doc() -> ProcessMiningDefinitionDocument:
    return ProcessMiningDefinitionDocument(
        title="TestProcess",
        document_id="test_001",
        kind=DocumentStandard.KSDM,
        media_type=MEDIA_TYPES["jprm_json"],
        processes={
            "p1": MiningProcessDefinition(
                id="p1",
                description="A test process",
                decision_points={
                    "dp1": DecisionPointDefinition(
                        id="dp1",
                        description="First decision point",
                        mining_algorithm=MiningModelType.DECISION_TREE,
                    ),
                    "dp2": DecisionPointDefinition(
                        id="dp2",
                        description="Second decision point",
                        mining_algorithm=MiningModelType.CLUSTERING,
                        clustering_config=ClusteringConfig(
                            algorithm=MiningModelType.CLUSTERING,
                            n_clusters=3,
                        ),
                    ),
                },
                catch_event_definitions={
                    "ce1": CatchEventMiningDefinition(
                        id="ce1",
                        description="Catch timeout events",
                        clustering_config=ClusteringConfig(
                            algorithm=MiningModelType.CLUSTERING,
                            n_clusters=2,
                        ),
                    ),
                },
                mining_name="mining_p1",
            ),
        },
        default_clustering_config=ClusteringConfig(
            algorithm=MiningModelType.CLUSTERING,
            n_clusters=2,
        ),
        metadata={"source": "test"},
    )


def _make_sample_event_log() -> EventLogDocument:
    return EventLogDocument(
        title="TestLog",
        document_id="log_001",
        kind=DocumentStandard.LSDM,
        source=LogSource.XES,
        events=[
            LogEvent(attributes=[LogAttribute(key="concept:name", value="submit")]),
            LogEvent(attributes=[LogAttribute(key="concept:name", value="approve")]),
            LogEvent(attributes=[LogAttribute(key="concept:name", value="reject")]),
        ],
        traces=[
            XesTrace(
                id="trace_1",
                attributes=[
                    LogAttribute(key="concept:name", value="case_1"),
                ],
                events=[
                    LogAttribute(key="concept:name", value="submit"),
                    LogAttribute(key="concept:name", value="approve"),
                ],
            ),
            XesTrace(
                id="trace_2",
                attributes=[
                    LogAttribute(key="concept:name", value="case_2"),
                ],
                events=[
                    LogAttribute(key="concept:name", value="submit"),
                    LogAttribute(key="concept:name", value="reject"),
                ],
            ),
        ],
        media_type=MEDIA_TYPES["xes_xml"],
    )


class TestProcessMiningModels:

    def test_clustering_config_defaults(self):
        cc = ClusteringConfig()
        assert cc.algorithm == MiningModelType.CLUSTERING

    def test_decision_point_defaults(self):
        dp = DecisionPointDefinition(id="dp1")
        assert dp.mining_algorithm == MiningModelType.DECISION_TREE
        assert dp.clustering_config is None

    def test_catch_event_definition_defaults(self):
        ce = CatchEventMiningDefinition(id="ce1")
        assert ce.clustering_config is None
        assert ce.output_pmml_model is True

    def test_mining_process_definition(self):
        mp = MiningProcessDefinition(id="p1")
        assert mp.decision_points == {}
        assert mp.catch_event_definitions == {}

    def test_document_construction(self):
        doc = _make_sample_doc()
        assert doc.title == "TestProcess"
        assert "p1" in doc.processes
        assert "dp1" in doc.processes["p1"].decision_points
        assert "ce1" in doc.processes["p1"].catch_event_definitions
        assert doc.default_clustering_config is not None


class TestJprmParserWriter:

    @pytest.mark.asyncio
    async def test_parse_jprm(self):
        parser = JprmParser()
        doc = await parser.parse_bytes(
            _SAMPLE_JPRM.encode("utf-8"),
            "test",
            "test.jprm",
        )
        assert isinstance(doc, ProcessMiningDefinitionDocument)
        assert doc.title == "Test Process"
        assert "p1" in doc.processes
        dp1 = doc.processes["p1"].decision_points["dp1"]
        assert dp1.mining_algorithm == MiningModelType.DECISION_TREE
        ce1 = doc.processes["p1"].catch_event_definitions["ce1"]
        assert ce1.clustering_config is not None
        assert ce1.clustering_config.n_clusters == 3
        assert ce1.clustering_config.algorithm == MiningModelType.CLUSTERING

    @pytest.mark.asyncio
    async def test_jprm_roundtrip(self):
        doc = _make_sample_doc()
        writer = JprmWriter()
        data = await writer.write(doc)
        parser = JprmParser()
        doc2 = await parser.parse_bytes(data, "roundtrip", "roundtrip.jprm")
        assert doc2.title == doc.title
        assert set(doc2.processes.keys()) == set(doc.processes.keys())

    @pytest.mark.asyncio
    async def test_write_read_consistency(self):
        doc = _make_sample_doc()
        writer = JprmWriter()
        data = await writer.write(doc)
        parsed = data.decode("utf-8")
        assert "TestProcess" in parsed
        assert "dp1" in parsed
        assert "ce1" in parsed


class TestYprmParserWriter:

    @pytest.mark.asyncio
    async def test_parse_yprm(self):
        raw = yaml.dump(yaml.safe_load(_SAMPLE_JPRM), default_flow_style=False)
        parser = YprmParser()
        doc = await parser.parse_bytes(
            raw.encode("utf-8"),
            "test",
            "test.yprm",
        )
        assert isinstance(doc, ProcessMiningDefinitionDocument)
        assert doc.title == "Test Process"

    @pytest.mark.asyncio
    async def test_yprm_roundtrip(self):
        doc = _make_sample_doc()
        writer = YprmWriter()
        data = await writer.write(doc)
        parser = YprmParser()
        doc2 = await parser.parse_bytes(data, "roundtrip", "roundtrip.yprm")
        assert doc2.title == doc.title


class TestProcessMiningEngine:

    def test_engine_init(self):
        engine = ProcessMiningEngine()
        assert engine is not None

    def test_load_jprm(self, tmp_path: Path):
        fp = tmp_path / "test.jprm"
        fp.write_text(_SAMPLE_JPRM)
        engine = ProcessMiningEngine()
        doc = engine.load(fp, document_id="test")
        assert isinstance(doc, ProcessMiningDefinitionDocument)
        assert doc.title == "Test Process"

    def test_loads_jprm(self):
        engine = ProcessMiningEngine()
        doc = engine.loads(_SAMPLE_JPRM, fmt="jprm", document_id="test")
        assert doc.title == "Test Process"

    def test_loads_yprm(self):
        raw = yaml.dump(yaml.safe_load(_SAMPLE_JPRM), default_flow_style=False)
        engine = ProcessMiningEngine()
        doc = engine.loads(raw, fmt="yprm", document_id="test")
        assert doc.title == "Test Process"

    def test_discover_process_model(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        event_log = _make_sample_event_log()
        result = engine.discover_process_model(doc, event_log)
        assert result is doc

    def test_analyze_decision_points(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        event_log = _make_sample_event_log()
        dmn_doc = engine.analyze_decision_points(doc, event_log)
        assert dmn_doc.title == "Decision Mining: TestProcess"
        assert len(dmn_doc.dmn_definitions) == 1
        dmn_def = dmn_doc.dmn_definitions[0]
        assert dmn_def.id == "decision_mining"
        assert len(dmn_def.decisions) == 2

    def test_analyze_catch_events(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        event_log = _make_sample_event_log()
        dmn_doc = engine.analyze_catch_events(doc, event_log)
        assert dmn_doc.title == "Event Mining: TestProcess"
        assert len(dmn_doc.dmn_definitions) == 1
        dmn_def = dmn_doc.dmn_definitions[0]
        assert dmn_def.id == "event_mining"
        assert len(dmn_def.decisions) >= 1

    def test_to_dmn(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        dmn_doc = engine.to_dmn(doc)
        assert dmn_doc.title == "DMN Export: TestProcess"
        assert len(dmn_doc.dmn_definitions) == 1
        assert len(dmn_doc.dmn_definitions[0].decisions) == 2

    def test_to_dmn_filtered(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        dmn_doc = engine.to_dmn(doc, decision_point_id="dp1")
        assert len(dmn_doc.dmn_definitions[0].decisions) == 1

    def test_validate_valid(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        errors = engine.validate(doc)
        assert errors == []

    def test_validate_missing_process_id(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        errors = engine.validate(doc)
        assert isinstance(errors, list)

    def test_get_statistics(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        stats = engine.get_statistics(doc)
        assert stats["num_processes"] == 1
        assert stats["num_decision_points"] == 2
        assert stats["num_catch_event_definitions"] == 1
        assert stats["has_default_clustering"] is True
        assert len(stats["processes"]) == 1
        p1 = stats["processes"][0]
        assert p1["id"] == "p1"
        assert len(p1["decision_points"]) == 2

    def test_unsupported_format_raises(self):
        engine = ProcessMiningEngine()
        with pytest.raises(ValueError, match="Unsupported process mining format"):
            engine.loads("{}", fmt="unknown")

    def test_analyze_decision_points_empty_log(self):
        engine = ProcessMiningEngine()
        doc = _make_sample_doc()
        empty_log = EventLogDocument(
            title="Empty", document_id="e",
            kind=DocumentStandard.LSDM,
            source=LogSource.XES,
            events=[], traces=[],
            media_type=MEDIA_TYPES["xes_xml"],
        )
        dmn_doc = engine.analyze_decision_points(doc, empty_log)
        assert len(dmn_doc.dmn_definitions[0].decisions) == 2

    def test_engine_from_knowledge_package(self):
        from engines.knowledge import ProcessMiningEngine as KPE
        assert KPE is ProcessMiningEngine
