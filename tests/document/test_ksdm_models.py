# tests/document/test_ksdm_models.py
"""
Tests for KSDM models: KSDMDocument, Entity, Relation, enums.
"""

from engines.document.models.ksdm_models import (
    Entity,
    EntityType,
    KSDMDocument,
    Relation,
    RelationType,
)
from engines.document.models.standard import DocumentStandard


def test_ksdm_document_creation():
    doc = KSDMDocument(
        title="Org Chart",
        document_id="ksdm-001",
        ontology={"namespaces": {"ex": "http://example.org/"}},
        entities=[
            Entity(
                id="ent_1",
                type=EntityType.PERSON,
                label="Alice",
                properties={"age": 30},
                embedding=[0.1, 0.2, 0.3],
            )
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
        attributes={"graph_name": "org_chart"},
    )
    assert doc.kind == DocumentStandard.KSDM
    assert len(doc.entities) == 1
    assert len(doc.relations) == 1
    assert doc.entities[0].type == EntityType.PERSON
    assert doc.entities[0].embedding == [0.1, 0.2, 0.3]
    assert doc.relations[0].type == RelationType.WORKS_FOR
    assert doc.relations[0].weight == 0.9
    assert doc.relations[0].timestamp == "2024-01-01"


def test_entity_type_enum():
    assert EntityType.PERSON == "Person"
    assert EntityType.ORGANIZATION == "Organization"
    assert EntityType.LOCATION == "Location"


def test_relation_type_enum():
    assert RelationType.WORKS_FOR == "worksFor"
    assert RelationType.LOCATED_IN == "locatedIn"
    assert RelationType.PART_OF == "partOf"


def test_entity_embedding():
    entity = Entity(id="e1", type=EntityType.PERSON, embedding=[0.1, 0.2])
    assert entity.embedding == [0.1, 0.2]

    entity2 = Entity(id="e2", type=EntityType.ORGANIZATION)
    assert entity2.embedding == []
