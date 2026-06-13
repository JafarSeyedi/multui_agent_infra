from __future__ import annotations

import json
import pytest

from engines.knowledge.models.query_models import (
    UnifiedQueryDocument,
    QueryLanguage,
    QueryTransport,
    ResultsetFormat,
    MdxQuery,
    DaxQuery,
    SqlTabularQuery,
    PowerQueryM,
    JpqlQuery,
    OqlQuery,
    GraphqlQueryDocument,
    GraphqlOperation,
    XmlaTransport,
    RestTransport,
)
from engines.knowledge.query import QueryEngine


@pytest.fixture
def sample_mdx_text() -> str:
    return """
    SELECT
      {[Measures].[Sales Amount]} ON COLUMNS,
      {[Product].[Category].Members} ON ROWS
    FROM [Sales]
    WHERE ([Date].[2024])
    """


@pytest.fixture
def sample_dax_text() -> str:
    return "EVALUATE SUMMARIZE('Sales', [Product], [Sales Amount])"


@pytest.fixture
def sample_sql_tabular_text() -> str:
    return "SELECT * FROM [$SYSTEM.DISCOVER_CUBES] WHERE CUBE_NAME = 'Sales'"


@pytest.fixture
def sample_m_text() -> str:
    return "let Source = Sql.Database(\"server\", \"db\") in Source"


@pytest.fixture
def sample_jpql_text() -> str:
    return "SELECT e FROM Employee e WHERE e.salary > :minSalary ORDER BY e.name"


@pytest.fixture
def sample_oql_text() -> str:
    return "SELECT FROM Employee FETCH 10"


@pytest.fixture
def sample_graphql_query_text() -> str:
    return "query GetUser($id: ID!) { user(id: $id) { id name email } }"


@pytest.mark.asyncio
async def test_mdx_parse(sample_mdx_text):
    from engines.knowledge.models.parsers.query_models import MdxParser

    parser = MdxParser()
    doc = await parser.parse_bytes(sample_mdx_text.encode(), "mdx_test", "mdx_test")
    assert doc.language == QueryLanguage.MDX
    assert doc.mdx is not None
    assert doc.mdx.cube_name == "Sales"
    assert len(doc.mdx.axes) >= 1
    assert doc.mdx.slicer is not None


@pytest.mark.asyncio
async def test_mdx_write_roundtrip(sample_mdx_text):
    from engines.knowledge.models.parsers.query_models import MdxParser
    from engines.knowledge.models.writers.query_models import MdxWriter

    parser = MdxParser()
    writer = MdxWriter()
    doc = await parser.parse_bytes(sample_mdx_text.encode(), "roundtrip", "roundtrip")
    output = await writer.write(doc)
    doc2 = await parser.parse_bytes(output, "roundtrip2", "roundtrip2")
    assert doc2.language == doc.language
    assert doc2.mdx is not None
    assert doc2.mdx.cube_name == doc.mdx.cube_name


@pytest.mark.asyncio
async def test_dax_parse(sample_dax_text):
    from engines.knowledge.models.parsers.query_models import DaxParser

    parser = DaxParser()
    doc = await parser.parse_bytes(sample_dax_text.encode(), "dax_test", "dax_test")
    assert doc.language == QueryLanguage.DAX
    assert doc.dax is not None
    assert doc.dax.expression != ""


@pytest.mark.asyncio
async def test_sql_tabular_parse(sample_sql_tabular_text):
    from engines.knowledge.models.parsers.query_models import SqlTabularParser

    parser = SqlTabularParser()
    doc = await parser.parse_bytes(sample_sql_tabular_text.encode(), "sql_test", "sql_test")
    assert doc.language == QueryLanguage.SQL_TABULAR
    assert doc.sql is not None
    assert doc.sql.dmv_name == "MDSCHEMA_CUBES" or "DISCOVER_CUBES" in doc.sql.dmv_name


@pytest.mark.asyncio
async def test_m_parse(sample_m_text):
    from engines.knowledge.models.parsers.query_models import PowerQueryMParser

    parser = PowerQueryMParser()
    doc = await parser.parse_bytes(sample_m_text.encode(), "m_test", "m_test")
    assert doc.language == QueryLanguage.M_POWER_QUERY
    assert doc.m_query is not None
    assert "Sql.Database" in doc.m_query.let_expression


@pytest.mark.asyncio
async def test_jpql_parse(sample_jpql_text):
    from engines.knowledge.models.parsers.query_models import JpqlParser

    parser = JpqlParser()
    doc = await parser.parse_bytes(sample_jpql_text.encode(), "jpql_test", "jpql_test")
    assert doc.language == QueryLanguage.JPQL
    assert doc.jpql is not None
    assert doc.jpql.entity_name == "Employee"


@pytest.mark.asyncio
async def test_oql_parse(sample_oql_text):
    from engines.knowledge.models.parsers.query_models import OqlParser

    parser = OqlParser()
    doc = await parser.parse_bytes(sample_oql_text.encode(), "oql_test", "oql_test")
    assert doc.language == QueryLanguage.OQL
    assert doc.oql is not None
    assert doc.oql.entity_name == "Employee"


@pytest.mark.asyncio
async def test_graphql_parse(sample_graphql_query_text):
    from engines.knowledge.models.parsers.query_models import GraphqlQueryParser

    parser = GraphqlQueryParser()
    doc = await parser.parse_bytes(sample_graphql_query_text.encode(), "gql_test", "gql_test")
    assert doc.language == QueryLanguage.GRAPHQL
    assert doc.graphql is not None
    assert len(doc.graphql.operations) >= 1
    assert doc.graphql.operations[0].kind == "query"


@pytest.mark.asyncio
async def test_xmla_parse_execute():
    from engines.knowledge.models.parsers.query_models import XmlaQueryParser

    xmla = b"""<?xml version="1.0"?>
    <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
      <Body>
        <ExecuteResponse xmlns="urn:schemas-microsoft-com:xml-analysis">
          <RequestType>SQL</RequestType>
          <row><Column1>Value1</Column1></row>
        </ExecuteResponse>
      </Body>
    </Envelope>"""
    parser = XmlaQueryParser()
    doc = await parser.parse_bytes(xmla, "xmla_test", "xmla_test")
    assert doc.language in (QueryLanguage.MDX, QueryLanguage.SQL_TABULAR)
    assert doc.xmla_transport is not None
    assert doc.xmla_transport.request_type == "SQL"


@pytest.mark.asyncio
async def test_dax_rest_json():
    from engines.knowledge.models.parsers.query_models import DaxParser

    payload = {
        "queries": [{"Expression": "EVALUATE 'Sales'"}],
        "endpoint": "https://api.powerbi.com/v1/datasets/xxx",
    }
    parser = DaxParser()
    doc = await parser.parse_bytes(json.dumps(payload).encode(), "dax_rest_test", "dax_rest_test")
    assert doc.transport == QueryTransport.REST_JSON
    assert doc.dax is not None


@pytest.mark.asyncio
async def test_engine_detect_language():
    engine = QueryEngine()
    assert engine.detect_language("SELECT * FROM Cube") == QueryLanguage.MDX
    assert engine.detect_language("EVALUATE") == QueryLanguage.DAX
    assert engine.detect_language("let Source = ...") == QueryLanguage.M_POWER_QUERY
    assert engine.detect_language("query { field }") == QueryLanguage.GRAPHQL
    assert engine.detect_language("SELECT e FROM Employee") == QueryLanguage.JPQL


@pytest.mark.asyncio
async def test_engine_parse_text(sample_mdx_text):
    engine = QueryEngine()
    doc = await engine.async_parse(sample_mdx_text)
    assert doc.mdx is not None


@pytest.mark.asyncio
async def test_engine_convert():
    engine = QueryEngine()
    await engine.async_parse("SELECT * ON COLUMNS FROM [Sales]")
    output = await engine.async_convert(QueryLanguage.MDX)
    assert "SELECT" in output.upper()


@pytest.mark.asyncio
async def test_graphql_response():
    from engines.knowledge.models.parsers.query_models import GraphqlQueryParser

    resp = {"data": {"user": {"id": "1", "name": "Alice"}}, "errors": []}
    parser = GraphqlQueryParser()
    doc = await parser.parse_bytes(json.dumps(resp).encode(), "gql_resp", "gql_resp")
    assert doc.graphql.response_data.get("user", {}).get("id") == "1"