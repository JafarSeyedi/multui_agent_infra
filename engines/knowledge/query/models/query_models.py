from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from engines.document.models.base import BaseDocument


class QueryLanguage(str, Enum):
    MDX = "mdx"
    DAX = "dax"
    SQL_TABULAR = "sql_tabular"
    M_POWER_QUERY = "m_power_query"
    JPQL = "jpql"
    OQL = "oql"
    GRAPHQL = "graphql"


class QueryTransport(str, Enum):
    XMLA_SOAP = "xmla_soap"
    REST_JSON = "rest_json"
    GRPC_PROTOBUF = "grpc_protobuf"


class ResultsetFormat(str, Enum):
    MDX_CELLSET = "mdx_cellset"
    FLAT_TABLE = "flat_table"
    JSON_API = "json_api"
    SIREN_HYPERMEDIA = "siren_hypermedia"


class QuerySource(BaseModel):
    name: str
    source_type: str = "cube"
    connection_string: str | None = None


class QueryColumn(BaseModel):
    name: str
    data_type: str | None = None
    expression: str | None = None
    aggregator: str | None = None


class QueryParameter(BaseModel):
    name: str
    value: Any = None
    data_type: str | None = None


class QueryDefinition(BaseModel):
    language: QueryLanguage = QueryLanguage.MDX
    source: str = ""
    text: str = ""
    parameters: list[QueryParameter] = Field(default_factory=list)


class MdxAxis(BaseModel):
    axis: str = "ROWS"
    dimension: str | None = None
    hierarchy: str | None = None
    level: str | None = None
    member: str | None = None
    set_expression: str | None = None


class MdxCalculatedMember(BaseModel):
    name: str = ""
    expression: str = ""
    format_string: str | None = None
    solve_order: int | None = None


class MdxQuery(BaseModel):
    cube_name: str = ""
    axes: list[MdxAxis] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    calculated_members: list[MdxCalculatedMember] = Field(default_factory=list)
    slicer: str | None = None
    non_empty: bool = False
    cell_properties: list[str] = Field(default_factory=list)
    query_text: str | None = None


class DaxQuery(BaseModel):
    table_name: str | None = None
    expression: str = ""
    measures: list[str] = Field(default_factory=list)
    filter: str | None = None
    eval_context: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)


class SqlTabularQuery(BaseModel):
    dialect: str = "tsql"
    catalog: str | None = None
    schema_name: str | None = None
    dmv_name: str | None = None
    statement: str = ""
    tables: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class PowerQueryM(BaseModel):
    let_expression: str = ""
    variables: dict[str, str] = Field(default_factory=dict)
    output: str = ""
    parameters: list[QueryParameter] = Field(default_factory=list)


class JpqlQuery(BaseModel):
    entity_name: str | None = None
    statement: str = ""
    fields: list[str] = Field(default_factory=list)
    parameters: list[QueryParameter] = Field(default_factory=list)


class OqlQuery(BaseModel):
    entity_name: str | None = None
    statement: str = ""
    fields: list[str] = Field(default_factory=list)
    parameters: list[QueryParameter] = Field(default_factory=list)


class GraphqlField(BaseModel):
    name: str = ""
    alias: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    fields: list[GraphqlField] = Field(default_factory=list)


class GraphqlOperation(BaseModel):
    kind: str = "query"
    name: str | None = None
    fields: list[GraphqlField] = Field(default_factory=list)
    variable_definitions: dict[str, str] = Field(default_factory=dict)


class GraphqlFragment(BaseModel):
    name: str = ""
    on_type: str = ""
    fields: list[GraphqlField] = Field(default_factory=list)


class GraphqlError(BaseModel):
    message: str = ""
    locations: list[dict[str, Any]] = Field(default_factory=list)
    path: list[str] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)


class GraphqlQueryDocument(BaseModel):
    operations: list[GraphqlOperation] = Field(default_factory=list)
    fragments: list[GraphqlFragment] = Field(default_factory=list)
    response_data: dict[str, Any] = Field(default_factory=dict)
    response_errors: list[GraphqlError] = Field(default_factory=list)
    query_text: str | None = None


class XmlaTransport(BaseModel):
    request_type: str = ""
    restrictions: dict[str, str] = Field(default_factory=dict)
    properties: dict[str, str] = Field(default_factory=dict)
    rows: list[dict[str, str]] = Field(default_factory=list)
    execute_result: str | None = None


class RestTransport(BaseModel):
    endpoint: str = ""
    method: str = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None


class CellValue(BaseModel):
    value: Any = None
    format_string: str | None = None
    ordinal: int = 0


class CellAxis(BaseModel):
    name: str = ""
    members: list[dict[str, Any]] = Field(default_factory=list)


class MdxCellset(BaseModel):
    axes: list[CellAxis] = Field(default_factory=list)
    cells: list[CellValue] = Field(default_factory=list)
    cube_name: str | None = None


class FlatTableResult(BaseModel):
    columns: list[QueryColumn] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0


class UnifiedQueryDocument(BaseDocument):
    language: QueryLanguage | None = None
    transport: QueryTransport | None = None
    resultset_format: ResultsetFormat | None = None
    source: QuerySource | None = None
    query_definition: QueryDefinition | None = None
    parameters: list[QueryParameter] = Field(default_factory=list)
    mdx: MdxQuery | None = None
    dax: DaxQuery | None = None
    sql: SqlTabularQuery | None = None
    m_query: PowerQueryM | None = None
    jpql: JpqlQuery | None = None
    oql: OqlQuery | None = None
    graphql: GraphqlQueryDocument | None = None
    xmla_transport: XmlaTransport | None = None
    rest_transport: RestTransport | None = None
    cellset: MdxCellset | None = None
    table: FlatTableResult | None = None
    model_config = ConfigDict(populate_by_name=True)

    @property
    def sources(self) -> list[QuerySource]:
        if self.source is None:
            return []
        return [self.source]
