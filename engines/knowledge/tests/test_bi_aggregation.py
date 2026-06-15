from __future__ import annotations

import json
import pytest
import xml.etree.ElementTree as ET

from engines.knowledge.bi_aggregation.models import (
    UnifiedBiAggregationDocument,
    AggregationSource,
    Dimension,
    DimensionAttribute,
    DimensionHierarchy,
    DimensionLevel,
    Measure,
    AggregationRelationship,
)
from engines.knowledge.bi_aggregation import BiAggregationEngine


@pytest.fixture
def sample_mondrian_xml() -> bytes:
    return b"""<?xml version="1.0"?>
<Schema name="SalesSchema">
  <Cube name="Sales">
    <Dimension name="Customer" type="StandardDimension">
      <Hierarchy hasAll="true">
        <Level name="Country" column="country"/>
        <Level name="City" column="city"/>
      </Hierarchy>
    </Dimension>
    <Measure name="Revenue" column="amount" aggregator="sum" visible="true"/>
  </Cube>
</Schema>"""


@pytest.fixture
def sample_tmsl_json() -> bytes:
    payload = {
        "model": {
            "name": "AdventureWorks",
            "tables": [
                {
                    "name": "DimCustomer",
                    "columns": [
                        {"name": "CustomerKey", "dataType": "int64", "sourceColumn": "CustomerKey"},
                        {"name": "FullName", "dataType": "string", "sourceColumn": "FullName"},
                    ],
                    "measures": [
                        {"name": "TotalSales", "expression": "SUM(Sales[Amount])", "formatString": "Currency"}
                    ],
                }
            ],
            "relationships": [
                {
                    "name": "FK_Customer",
                    "fromTable": "FactSales",
                    "fromColumn": "CustomerKey",
                    "toTable": "DimCustomer",
                    "toColumn": "CustomerKey",
                }
            ],
        }
    }
    return json.dumps(payload).encode("utf-8")


@pytest.fixture
def sample_cdm_json() -> bytes:
    payload = {
        "name": "SalesModel",
        "entities": [
            {
                "name": "Customer",
                "attributes": [
                    {"name": "CustomerId", "dataType": "string"},
                    {"name": "FullName", "dataType": "string"},
                ],
            }
        ],
        "relationships": [
            {
                "name": "CustomerToOrder",
                "fromEntity": "Customer",
                "fromAttribute": "CustomerId",
                "toEntity": "Order",
                "toAttribute": "CustomerId",
            }
        ],
    }
    return json.dumps(payload).encode("utf-8")


@pytest.fixture
def sample_calcite_json() -> bytes:
    payload = {
        "version": "1.0",
        "defaultSchema": "SALES",
        "schemas": [
            {
                "name": "SALES",
                "tables": [
                    {
                        "name": "EMPS",
                        "type": "custom",
                        "operand": {
                            "columns": [
                                {"name": "EMPNO", "type": "int"},
                                {"name": "ENAME", "type": "varchar"},
                            ]
                        },
                    }
                ],
            }
        ],
    }
    return json.dumps(payload).encode("utf-8")


@pytest.fixture
def sample_awxml() -> bytes:
    root = ET.Element("AWManifest")
    root.set("name", "SalesWorkspace")
    cube = ET.SubElement(root, "cube")
    cube.set("name", "SalesCube")
    dim = ET.SubElement(root, "dimension")
    dim.set("name", "Product")
    h = ET.SubElement(dim, "hierarchy")
    h.set("name", "Default")
    ET.SubElement(h, "level", {"name": "Category"})
    ET.SubElement(h, "level", {"name": "Subcategory"})
    return ET.tostring(root, encoding="unicode").encode("utf-8")


@pytest.fixture
def sample_sap_cds() -> bytes:
    root = ET.Element("Schema")
    root.set("name", "CDS_Schema")
    entity = ET.SubElement(root, "Entity")
    entity.set("name", "SalesOrder")
    ET.SubElement(entity, "Element", {"name": "OrderId", "type": "string"})
    ET.SubElement(entity, "Element", {"name": "Amount", "type": "decimal"})
    ET.SubElement(entity, "measure", {"name": "TotalAmount", "aggregation": "sum"})
    assoc = ET.SubElement(root, "Association")
    assoc.set("name", "ToCustomer")
    assoc.set("source", "SalesOrder")
    assoc.set("target", "Customer")
    return ET.tostring(root, encoding="unicode").encode("utf-8")


@pytest.fixture
def sample_cognos_fmf() -> bytes:
    root = ET.Element("FrameworkManager")
    root.set("name", "CognosModel")
    subj = ET.SubElement(root, "QuerySubject")
    subj.set("name", "Orders")
    ET.SubElement(subj, "QueryItem", {"name": "OrderId"})
    ET.SubElement(subj, "QueryItem", {"name": "Total", "aggregation": "sum"})
    return ET.tostring(root, encoding="unicode").encode("utf-8")


@pytest.mark.asyncio
async def test_mondrian_parse(sample_mondrian_xml):
    from engines.knowledge.bi_aggregation.models.parsers import MondrianSchemaParser

    parser = MondrianSchemaParser()
    doc = await parser.parse_bytes(sample_mondrian_xml, "mondrian_test", "mondrian_test")
    assert doc.name == "SalesSchema"
    assert len(doc.sources) == 1
    assert doc.sources[0].name == "Sales"
    assert len(doc.dimensions) == 1
    assert doc.dimensions[0].name == "Customer"
    assert len(doc.dimensions[0].hierarchies) == 1
    assert len(doc.dimensions[0].hierarchies[0].levels) == 2
    assert doc.dimensions[0].hierarchies[0].levels[0].name == "Country"
    assert len(doc.measures) == 1
    assert doc.measures[0].name == "Revenue"
    assert doc.measures[0].aggregator == "sum"


@pytest.mark.asyncio
async def test_tmsl_parse(sample_tmsl_json):
    from engines.knowledge.bi_aggregation.models.parsers import TmslParser

    parser = TmslParser()
    doc = await parser.parse_bytes(sample_tmsl_json, "tmsl_test", "tmsl_test")
    assert doc.name == "AdventureWorks"
    assert len(doc.sources) == 1
    assert doc.sources[0].name == "DimCustomer"
    assert len(doc.dimensions) == 1
    assert len(doc.dimensions[0].attributes) == 2
    assert len(doc.measures) == 1
    assert doc.measures[0].name == "TotalSales"
    assert len(doc.relationships) == 1
    assert doc.relationships[0].source_table == "FactSales"


@pytest.mark.asyncio
async def test_cdm_parse(sample_cdm_json):
    from engines.knowledge.bi_aggregation.models.parsers import CdmParser

    parser = CdmParser()
    doc = await parser.parse_bytes(sample_cdm_json, "cdm_test", "cdm_test")
    assert doc.name == "SalesModel"
    assert len(doc.sources) == 1
    assert doc.sources[0].name == "Customer"
    assert len(doc.relationships) == 1
    assert doc.relationships[0].source_table == "Customer"


@pytest.mark.asyncio
async def test_calcite_parse(sample_calcite_json):
    from engines.knowledge.bi_aggregation.models.parsers import CalciteParser

    parser = CalciteParser()
    doc = await parser.parse_bytes(sample_calcite_json, "calcite_test", "calcite_test")
    assert doc.name == "SALES"
    assert len(doc.sources) == 1
    assert doc.sources[0].name == "EMPS"
    assert len(doc.dimensions) == 1
    assert len(doc.dimensions[0].attributes) == 2


@pytest.mark.asyncio
async def test_awxml_parse(sample_awxml):
    from engines.knowledge.bi_aggregation.models.parsers import AwxmlParser

    parser = AwxmlParser()
    doc = await parser.parse_bytes(sample_awxml, "aw_test", "aw_test")
    assert doc.name == "SalesWorkspace"
    assert len(doc.sources) == 1
    assert doc.sources[0].name == "SalesCube"
    assert len(doc.dimensions) == 1
    assert doc.dimensions[0].name == "Product"


@pytest.mark.asyncio
async def test_sap_cds_parse(sample_sap_cds):
    from engines.knowledge.bi_aggregation.models.parsers import SapCdsParser

    parser = SapCdsParser()
    doc = await parser.parse_bytes(sample_sap_cds, "cds_test", "cds_test")
    assert doc.name == "CDS_Schema"
    assert len(doc.sources) >= 1
    assert any(s.name == "SalesOrder" for s in doc.sources)
    assert len(doc.measures) >= 1


@pytest.mark.asyncio
async def test_cognos_fmf_parse(sample_cognos_fmf):
    from engines.knowledge.bi_aggregation.models.parsers import CognosFmfParser

    parser = CognosFmfParser()
    doc = await parser.parse_bytes(sample_cognos_fmf, "cognos_test", "cognos_test")
    assert doc.name == "CognosModel"
    assert len(doc.sources) >= 1


@pytest.mark.asyncio
async def test_tableau_hyper_stub_raises():
    from engines.knowledge.bi_aggregation.models.parsers import TableauHyperParser

    parser = TableauHyperParser()
    with pytest.raises(RuntimeError, match="tableauhyperapi"):
        await parser.parse_bytes(b"dummy", "hyper_test", "hyper_test")


@pytest.mark.asyncio
async def test_mondrian_write_roundtrip(sample_mondrian_xml):
    from engines.knowledge.bi_aggregation.models.parsers import MondrianSchemaParser
    from engines.knowledge.bi_aggregation.models.writers import MondrianSchemaWriter

    parser = MondrianSchemaParser()
    writer = MondrianSchemaWriter()
    doc = await parser.parse_bytes(sample_mondrian_xml, "roundtrip", "roundtrip")
    output = await writer.write(doc)
    doc2 = await parser.parse_bytes(output, "roundtrip2", "roundtrip2")
    assert doc2.name == doc.name
    assert len(doc2.sources) == len(doc.sources)
    assert len(doc2.dimensions) == len(doc.dimensions)
    assert len(doc2.measures) == len(doc.measures)


@pytest.mark.asyncio
async def test_tmsl_write_roundtrip(sample_tmsl_json):
    from engines.knowledge.bi_aggregation.models.parsers import TmslParser
    from engines.knowledge.bi_aggregation.models.writers import TmslWriter

    parser = TmslParser()
    writer = TmslWriter()
    doc = await parser.parse_bytes(sample_tmsl_json, "roundtrip", "roundtrip")
    output = await writer.write(doc)
    doc2 = await parser.parse_bytes(output, "roundtrip2", "roundtrip2")
    assert doc2.name == doc.name
    assert len(doc2.sources) == len(doc.sources)


@pytest.mark.asyncio
async def test_engine_load_and_query(sample_mondrian_xml):
    engine = BiAggregationEngine()
    doc = await engine.async_load(sample_mondrian_xml, parser_name="mondrian")
    assert doc.name == "SalesSchema"
    cubes = engine.get_cubes()
    assert len(cubes) == 1
    assert cubes[0].name == "Sales"
    dims = engine.get_dimensions()
    assert len(dims) == 1
    measures = engine.get_measures()
    assert len(measures) == 1
    agg = engine.aggregate(group_by=["Country"], measures=["Revenue"])
    assert agg.group_by == ["Country"]
    assert agg.measures == ["Revenue"]
    aggs = engine.get_aggregations()
    assert len(aggs) == 1


@pytest.mark.asyncio
async def test_engine_convert(sample_mondrian_xml):
    engine = BiAggregationEngine()
    await engine.async_load(sample_mondrian_xml, parser_name="mondrian")
    output = await engine.async_convert("tmsl")
    parsed = json.loads(output)
    assert "model" in parsed
    assert parsed["model"]["name"] == "SalesSchema"


@pytest.mark.asyncio
async def test_cwm_parse():
    from engines.knowledge.bi_aggregation.models.parsers import CwmParser

    cwm_xml = b"""<?xml version="1.0"?>
<XMI xmi.version="1.1" xmlns:CWM="http://www.omg.org/cwm">
  <XMI.content>
    <CWM:Cube name="SalesCube"/>
    <CWM:Dimension name="CustomerDim"/>
    <CWM:Measure name="Revenue" aggregator="sum"/>
  </XMI.content>
</XMI>"""
    parser = CwmParser()
    doc = await parser.parse_bytes(cwm_xml, "cwm_test", "cwm_test")
    assert len(doc.sources) >= 1
    assert any(s.name == "SalesCube" for s in doc.sources)

    # also test without namespace prefix but with default ns
    cwm_ns = b"""<?xml version="1.0"?>
<XMI xmi.version="1.1" xmlns="http://www.omg.org/cwm" xmlns:xmi="http://www.omg.org/XMI">
  <XMI.content>
    <Cube name="NsCube"/>
    <Dimension name="NsDim"/>
  </XMI.content>
</XMI>"""
    doc2 = await parser.parse_bytes(cwm_ns, "cwm_ns_test", "cwm_ns_test")
    assert len(doc2.sources) >= 1


def test_engine_sync_load():
    engine = BiAggregationEngine()
    mondrian = b"""<?xml version="1.0"?>
<Schema name="SyncTest"><Cube name="SyncCube">
  <Dimension name="D1"><Hierarchy hasAll="true">
    <Level name="L1" column="c1"/>
  </Hierarchy></Dimension>
  <Measure name="M1" column="amt" aggregator="sum"/>
</Cube></Schema>"""
    doc = engine.load(mondrian, parser_name="mondrian")
    assert doc.name == "SyncTest"
    assert len(engine.get_cubes()) == 1


@pytest.mark.asyncio
async def test_xmla_discover_parse():
    from engines.knowledge.query.models.parsers import XmlaQueryParser as XmlaParser

    xmla = b"""<?xml version="1.0"?>
<DiscoverResponse xmlns="urn:schemas-microsoft-com:xml-analysis">
  <return>
    <root>
      <row>
        <CUBE_NAME>SalesCube</CUBE_NAME>
        <DIMENSION_NAME>Customer</DIMENSION_NAME>
        <MEASURE_NAME>Revenue</MEASURE_NAME>
      </row>
    </root>
  </return>
</DiscoverResponse>"""
    parser = XmlaParser()
    doc = await parser.parse_bytes(xmla, "xmla_test", "xmla_test")
    assert len(doc.sources) >= 1
