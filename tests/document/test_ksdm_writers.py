# tests/document/test_ksdm_writers.py
"""
Tests for KSDM writers.
"""
import json

import pytest
import yaml

from engines.document.parsers.ksdm_parsers import (
    KSDMJSONParser,
)
from engines.document.writers.ksdm_writers import (
    CSVGraphWriter,
    KSDMJSONWriter,
    KSDMYAMLWriter,
    RMLYAMLWriter,
)
from engines.document.models.ksdm_models import (
    Entity,
    EntityType,
    KSDMDocument,
    Relation,
    RelationType,
)
from engines.document.models.media_types import MEDIA_TYPES


@pytest.fixture
def sample_ksdm_doc():
    return KSDMDocument(
        title="Org Chart",
        document_id="ksdm-001",
        ontology={"namespaces": {"ex": "http://example.org/"}},
        entities=[
            Entity(
                id="ent_1",
                type=EntityType.PERSON,
                label="Alice",
                properties={"age": 30, "department": "Engineering"},
                embedding=[0.1, 0.2, 0.3],
            ),
            Entity(
                id="ent_2",
                type=EntityType.ORGANIZATION,
                label="Acme Corp",
                properties={"founded": 1990},
            ),
        ],
        relations=[
            Relation(
                id="rel_1",
                source_id="ent_1",
                target_id="ent_2",
                type=RelationType.WORKS_FOR,
                weight=0.9,
                timestamp="2024-01-01",
            )
        ],
        attributes={"graph_name": "org_chart", "version": "1.0"},
        media_type=MEDIA_TYPES.get("json", MEDIA_TYPES["bi_model_json"]),
    )


@pytest.mark.asyncio
async def test_ksdm_json_writer(sample_ksdm_doc):
    writer = KSDMJSONWriter()
    data = await writer.write(sample_ksdm_doc)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["kind"] == "ksdm"
    assert len(parsed["entities"]) == 2
    assert len(parsed["relations"]) == 1
    assert parsed["entities"][0]["type"] == "Person"
    assert parsed["entities"][0]["embedding"] == [0.1, 0.2, 0.3]
    assert parsed["relations"][0]["weight"] == 0.9


@pytest.mark.asyncio
async def test_ksdm_yaml_writer(sample_ksdm_doc):
    writer = KSDMYAMLWriter()
    data = await writer.write(sample_ksdm_doc)
    parsed = yaml.safe_load(data.decode("utf-8"))
    assert parsed["kind"] == "ksdm"
    assert len(parsed["entities"]) == 2
    assert len(parsed["relations"]) == 1


@pytest.mark.asyncio
async def test_ksdm_json_roundtrip(sample_ksdm_doc):
    writer = KSDMJSONWriter()
    parser = KSDMJSONParser()

    data = await writer.write(sample_ksdm_doc)
    doc2 = await parser.parse_bytes(data, "roundtrip", "roundtrip.ksdm.json")

    assert len(doc2.entities) == 2
    assert len(doc2.relations) == 1
    assert doc2.entities[0].embedding == [0.1, 0.2, 0.3]
    assert doc2.relations[0].weight == 0.9
    assert doc2.attributes == {"graph_name": "org_chart", "version": "1.0"}


@pytest.mark.asyncio
async def test_csv_graph_writer(sample_ksdm_doc):
    writer = CSVGraphWriter()
    data = await writer.write(sample_ksdm_doc)
    text = data.decode("utf-8")
    assert "source_id" in text
    assert "target_id" in text
    assert "relation_type" in text
    assert "ent_1" in text
    assert "ent_2" in text
    assert "worksFor" in text
    assert "0.9" in text


@pytest.mark.asyncio
async def test_rml_yaml_writer(sample_ksdm_doc):
    writer = RMLYAMLWriter()
    data = await writer.write(sample_ksdm_doc)
    parsed = yaml.safe_load(data.decode("utf-8"))
    assert "@prefix" in parsed or "rml_mapping" in parsed
