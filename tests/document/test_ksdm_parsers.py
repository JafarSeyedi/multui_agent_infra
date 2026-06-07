# tests/document/test_ksdm_parsers.py
"""
Tests for KSDM parsers.
"""
import json

import pytest
import yaml

from engines.document.parsers.ksdm_parsers import (
    CSVGraphParser,
    KSDMJSONParser,
    KSDMYAMLParser,
    RMLYAMLParser,
)
from engines.document.models.standard import DocumentStandard


@pytest.fixture
def sample_ksdm_json():
    return {
        "version": "1.0",
        "ontology": {"namespaces": {"ex": "http://example.org/"}},
        "entities": [
            {"id": "ent_1", "type": "Person", "label": "Alice", "properties": {"age": 30}, "embedding": [0.1, 0.2]},
            {"id": "ent_2", "type": "Organization", "label": "Acme", "properties": {"founded": 1990}},
        ],
        "relations": [
            {
                "id": "rel_1",
                "source_id": "ent_1",
                "target_id": "ent_2",
                "type": "worksFor",
                "weight": 0.9,
                "timestamp": "2024-01-01",
            }
        ],
        "attributes": {"graph_name": "org_chart"},
    }


@pytest.fixture
def sample_csv_graph():
    return """source_id,target_id,relation_type,weight,timestamp
ent_1,ent_2,worksFor,0.9,2024-01-01
ent_3,ent_2,locatedIn,0.7,2024-01-02"""


@pytest.mark.asyncio
async def test_ksdm_json_parser(sample_ksdm_json):
    parser = KSDMJSONParser()
    data = json.dumps(sample_ksdm_json).encode("utf-8")
    doc = await parser.parse_bytes(data, "test-ksdm", "test.ksdm.json")
    assert doc.kind == DocumentStandard.KSDM
    assert len(doc.entities) == 2
    assert len(doc.relations) == 1
    assert doc.entities[0].type.value == "Person"
    assert doc.entities[0].embedding == [0.1, 0.2]
    assert doc.relations[0].type.value == "worksFor"
    assert doc.relations[0].weight == 0.9


@pytest.mark.asyncio
async def test_ksdm_yaml_parser(sample_ksdm_json):
    parser = KSDMYAMLParser()
    data = yaml.dump(sample_ksdm_json).encode("utf-8")
    doc = await parser.parse_bytes(data, "test-ksdm-yaml", "test.ksdm.yaml")
    assert doc.kind == DocumentStandard.KSDM
    assert len(doc.entities) == 2


@pytest.mark.asyncio
async def test_csv_graph_parser(sample_csv_graph):
    parser = CSVGraphParser()
    data = sample_csv_graph.encode("utf-8")
    doc = await parser.parse_bytes(data, "test-csv-graph", "test.csv")
    assert doc.kind == DocumentStandard.KSDM
    assert len(doc.relations) == 2
    assert len(doc.entities) == 3


@pytest.mark.asyncio
async def test_rml_yaml_parser():
    parser = RMLYAMLParser()
    data = b"""
@prefix:
  rr: "http://www.w3.org/ns/r2rml#"
  rml: "http://semweb.mmlab.be/ns/rml#"
sources:
  source_1:
    reference: "people.csv"
    format: "csv"
mappings:
  - id: "mapping_1"
    sources: ["source_1"]
    subject: "ex:person1"
    predicateobjectmap:
      - predicate: "ex:name"
        object:
          value: "Alice"
          termtype: "Literal"
"""
    doc = await parser.parse_bytes(data, "test-rml", "test.rml.yaml")
    assert doc.ontology is not None
    assert "rml_mapping" in doc.ontology


def test_parser_extensions():
    assert KSDMJSONParser().supports_extension(".ksdm.json")
    assert KSDMYAMLParser().supports_extension(".ksdm.yaml")
    assert CSVGraphParser().supports_extension(".csv")
    assert RMLYAMLParser().supports_extension(".rml.yaml")
