# engines/document/models/media_types.py

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel
from .standard import DocumentStandard


# ------------------------
# Document Formats
# ------------------------
class DocumentFormat(str, Enum):

    # USDM
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"
    LATEX = "latex"
    RTF = "rtf"
    TXT = "txt"

    # PSDM
    PPTX = "pptx"
    PPT = "ppt"
    ODP = "odp"

    # ESDM
    XLSX = "xlsx"
    XLS = "xls"
    ODS = "ods"
    CSV = "csv"
    TSV = "tsv"
    PRN = "prn"                 # fixed‑width text
    PARQUET = "parquet"
    ARROW = "arrow"
    FEATHER = "feather"

    # DSDM
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    TOML = "toml"
    BSON = "bson"
    CBOR = "cbor"
    MESSAGEPACK = "messagepack"

    # CSDM
    DXF = "dxf"
    DWG = "dwg"
    IFC = "ifc"
    STL = "stl"
    STEP = "step"

    # MSDM formats
    JSON_SCHEMA = "json_schema"
    XSD = "xsd"
    SQL_DDL = "sql_ddl"
    ERD = "erd"               # generic, usually XML/JSON
    UML_XMI = "uml_xmi"
    PLANTUML = "plantuml"
    PROTOBUF = "proto"
    AVRO_SCHEMA = "avro_schema"
    THRIFT_IDL = "thrift"
    GRAPHQL_SCHEMA = "graphql_schema"
    OWL = "owl"
    CUE = "cue"
    # MSDM – NoSQL & time‑series
    CQL = "cql"                                     # Cassandra
    MONGODB_SCHEMA = "mongodb_schema"               # MongoDB validator / Mongoose
    INFLUXDB_SCHEMA = "influxdb_schema"             # InfluxDB measurements
    ELASTICSEARCH_MAPPING = "elasticsearch_mapping" # Elasticsearch
    NEO4J_SCHEMA = "neo4j_schema"                   # Neo4j / Cypher schema
    PYTHON_MODEL = "python_model"          # or "py_model"
    TYPESCRIPT_INTERFACE = "typescript_interface"
        
    # SSDM formats
    OPENAPI_JSON = "openapi_json"
    OPENAPI_YAML = "openapi_yaml"
    WSDL = "wsdl"
    YANG = "yang"
    MIB = "mib"
    ASYNCAPI = "asyncapi"
    RAML = "raml"
    API_BLUEPRINT = "apib"
    WEB_IDL = "webidl"
    POSTMAN_COLLECTION = "postman_collection"
    CDDL = "cddl"
    MCP = "mcp"
    
    TSDM_JSON = "tsdm_json"

    # OSDM formats
    BPMN_XML = "bpmn_xml"
    CMMN_XML = "cmmn_xml"
    DMN_XML = "dmn_xml"
    PNML_XML = "pnml_xml"
    GRAPHML_XML = "graphml_xml"
    CNCF_SERVERLESS_WORKFLOW_JSON = "cncf_serverless_workflow_json"
    CNCF_SERVERLESS_WORKFLOW_YAML = "cncf_serverless_workflow_yaml"
    CEP_JSON = "cep_json"
    UML_STATE_MACHINE_XML = "uml_state_machine_xml"
    SCXML_XML = "scxml_xml"
    EPC_XML = "epc_xml"
    AWS_STEP_FUNCTIONS_JSON = "aws_step_functions_json"
    AZURE_LOGIC_APPS_JSON = "azure_logic_apps_json"
    AIRFLOW_DAG_PY = "airflow_dag_py"
    PREFECT_DAG_PY = "prefect_dag_py"
    YAWL_XML = "yawl_xml"
    XPDL_XML = "xpd_xml"    
    
    UNKNOWN = "unknown"


# ------------------------
# Media classification
# ------------------------
class MediaContentKind(str, Enum):
    TEXT = "text"
    BINARY = "binary"
    STRUCTURED = "structured"
    TABULAR = "tabular"
    HIERARCHICAL = "hierarchical"
    MIXED = "mixed"
    VECTOR = "vector"
    GEOMETRIC = "geometric"
    PRESENTATION = "presentation"
    SCHEMA_DEFINITION = "schema_definition"
    SERVICE_DEFINITION = "service_definition"
    ORCHESTRATION_DEFINITION = "orchestration_definition"    
    UNKNOWN = "unknown"


# ------------------------
# Fallback: raw bytes or raw text?
# ------------------------
class MediaRawType(str, Enum):
    TEXT = "text"
    BINARY = "binary"


# ------------------------
# Core MediaType Model
# ------------------------
class MediaType(BaseModel):
    mime: str
    format: DocumentFormat
    standard: DocumentStandard
    extensions: List[str]
    kind: MediaContentKind
    raw_type: MediaRawType
    description: Optional[str] = None


# ------------------------
# FULL REGISTRY
# ------------------------
MEDIA_TYPES: Dict[str, MediaType] = {

    # ======================
    # USDM
    # ======================
    "pdf": MediaType(
        mime="application/pdf",
        format=DocumentFormat.PDF,
        standard=DocumentStandard.USDM,
        extensions=[".pdf"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY,
        description="Portable Document Format"
    ),

    "docx": MediaType(
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        format=DocumentFormat.DOCX,
        standard=DocumentStandard.USDM,
        extensions=[".docx"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.BINARY,
        description="Office Open XML Document"
    ),

    "html": MediaType(
        mime="text/html",
        format=DocumentFormat.HTML,
        standard=DocumentStandard.USDM,
        extensions=[".html", ".htm"],
        kind=MediaContentKind.MIXED,
        raw_type=MediaRawType.TEXT,
        description="HyperText Markup Language"
    ),

    "markdown": MediaType(
        mime="text/markdown",
        format=DocumentFormat.MARKDOWN,
        standard=DocumentStandard.USDM,
        extensions=[".md", ".markdown"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT,
        description="Markdown"
    ),

    "latex": MediaType(
        mime="application/x-latex",
        format=DocumentFormat.LATEX,
        standard=DocumentStandard.USDM,
        extensions=[".tex"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT,
        description="LaTeX"
    ),

    "rtf": MediaType(
        mime="application/rtf",
        format=DocumentFormat.RTF,
        standard=DocumentStandard.USDM,
        extensions=[".rtf"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT,
        description="Rich Text Format"
    ),

    "txt": MediaType(
        mime="text/plain",
        format=DocumentFormat.TXT,
        standard=DocumentStandard.USDM,
        extensions=[".txt"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT,
        description="Plain Text Document"
    ),

    # ======================
    # PSDM
    # ======================
    "pptx": MediaType(
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        format=DocumentFormat.PPTX,
        standard=DocumentStandard.PSDM,
        extensions=[".pptx"],
        kind=MediaContentKind.PRESENTATION,
        raw_type=MediaRawType.BINARY,
        description="Office Open XML Presentation"
    ),

    "ppt": MediaType(
        mime="application/vnd.ms-powerpoint",
        format=DocumentFormat.PPT,
        standard=DocumentStandard.PSDM,
        extensions=[".ppt"],
        kind=MediaContentKind.PRESENTATION,
        raw_type=MediaRawType.BINARY,
        description="Microsoft PowerPoint Presentation (legacy)"
    ),

    "odp": MediaType(
        mime="application/vnd.oasis.opendocument.presentation",
        format=DocumentFormat.ODP,
        standard=DocumentStandard.PSDM,
        extensions=[".odp"],
        kind=MediaContentKind.PRESENTATION,
        raw_type=MediaRawType.BINARY,
        description="OpenDocument Presentation"
    ),

    # ======================
    # ESDM
    # ======================
    "xlsx": MediaType(
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        format=DocumentFormat.XLSX,
        standard=DocumentStandard.ESDM,
        extensions=[".xlsx", ".xlsm", ".xltx", ".xltm"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY,
        description="Office Open XML Spreadsheet"
    ),

    "xls": MediaType(
        mime="application/vnd.ms-excel",
        format=DocumentFormat.XLS,
        standard=DocumentStandard.ESDM,
        extensions=[".xls"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY,
        description="Microsoft Excel Spreadsheet (legacy)"
    ),

    "ods": MediaType(
        mime="application/vnd.oasis.opendocument.spreadsheet",
        format=DocumentFormat.ODS,
        standard=DocumentStandard.ESDM,
        extensions=[".ods"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY,
        description="OpenDocument Spreadsheet"
    ),

    "csv": MediaType(
        mime="text/csv",
        format=DocumentFormat.CSV,
        standard=DocumentStandard.ESDM,
        extensions=[".csv"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.TEXT,
        description="Comma‑Separated Values"
    ),

    "tsv": MediaType(
        mime="text/tab-separated-values",
        format=DocumentFormat.TSV,
        standard=DocumentStandard.ESDM,
        extensions=[".tsv"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.TEXT,
        description="Tab‑Separated Values"
    ),

    "prn": MediaType(
        mime="text/plain",                             # same MIME as txt, but format is PRN
        format=DocumentFormat.PRN,
        standard=DocumentStandard.ESDM,
        extensions=[".prn"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.TEXT,
        description="Fixed‑Width Text File"
    ),

    "parquet": MediaType(
        mime="application/parquet",
        format=DocumentFormat.PARQUET,
        standard=DocumentStandard.ESDM,
        extensions=[".parquet"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY,
        description="Apache Parquet"
    ),

    "arrow": MediaType(
        mime="application/vnd.apache.arrow.file",
        format=DocumentFormat.ARROW,
        standard=DocumentStandard.ESDM,
        extensions=[".arrow"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY,
        description="Apache Arrow IPC"
    ),

    "feather": MediaType(
        mime="application/vnd.apache.feather",
        format=DocumentFormat.FEATHER,
        standard=DocumentStandard.ESDM,
        extensions=[".feather"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY,
        description="Feather Binary Format"
    ),

    # ======================
    # DSDM
    # ======================
    "json": MediaType(
        mime="application/json",
        format=DocumentFormat.JSON,
        standard=DocumentStandard.DSDM,
        extensions=[".json"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.TEXT,
        description="JavaScript Object Notation"
    ),

    "xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.XML,
        standard=DocumentStandard.DSDM,
        extensions=[".xml"],
        kind=MediaContentKind.HIERARCHICAL,
        raw_type=MediaRawType.TEXT,
        description="Extensible Markup Language"
    ),

    "yaml": MediaType(
        mime="application/x-yaml",
        format=DocumentFormat.YAML,
        standard=DocumentStandard.DSDM,
        extensions=[".yaml", ".yml"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.TEXT,
        description="YAML"
    ),

    "toml": MediaType(
        mime="application/toml",
        format=DocumentFormat.TOML,
        standard=DocumentStandard.DSDM,
        extensions=[".toml"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.TEXT,
        description="TOML Configuration"
    ),

    "bson": MediaType(
        mime="application/bson",
        format=DocumentFormat.BSON,
        standard=DocumentStandard.DSDM,
        extensions=[".bson"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY,
        description="Binary JSON"
    ),

    "cbor": MediaType(
        mime="application/cbor",
        format=DocumentFormat.CBOR,
        standard=DocumentStandard.DSDM,
        extensions=[".cbor"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY,
        description="Concise Binary Object Representation"
    ),

    "messagepack": MediaType(
        mime="application/msgpack",
        format=DocumentFormat.MESSAGEPACK,
        standard=DocumentStandard.DSDM,
        extensions=[".msgpack"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY,
        description="MessagePack"
    ),

    # ======================
    # CSDM
    # ======================
    "dxf": MediaType(
        mime="image/vnd.dxf",
        format=DocumentFormat.DXF,
        standard=DocumentStandard.CSDM,
        extensions=[".dxf"],
        kind=MediaContentKind.VECTOR,
        raw_type=MediaRawType.BINARY,
        description="AutoCAD DXF"
    ),

    "dwg": MediaType(
        mime="image/vnd.dwg",
        format=DocumentFormat.DWG,
        standard=DocumentStandard.CSDM,
        extensions=[".dwg"],
        kind=MediaContentKind.VECTOR,
        raw_type=MediaRawType.BINARY,
        description="AutoCAD DWG"
    ),

    "ifc": MediaType(
        mime="application/ifc",
        format=DocumentFormat.IFC,
        standard=DocumentStandard.CSDM,
        extensions=[".ifc"],
        kind=MediaContentKind.GEOMETRIC,
        raw_type=MediaRawType.BINARY,
        description="Industry Foundation Classes (IFC)"
    ),

    "stl": MediaType(
        mime="application/sla",                        # common MIME for STL
        format=DocumentFormat.STL,
        standard=DocumentStandard.CSDM,
        extensions=[".stl"],
        kind=MediaContentKind.GEOMETRIC,
        raw_type=MediaRawType.BINARY,
        description="Stereolithography (STL)"
    ),

    "step": MediaType(
        mime="application/step",
        format=DocumentFormat.STEP,
        standard=DocumentStandard.CSDM,
        extensions=[".step", ".stp"],
        kind=MediaContentKind.GEOMETRIC,
        raw_type=MediaRawType.TEXT,                   # STEP is a text‑based ISO format
        description="ISO 10303 STEP"
    ),


    # ======================
    # MSDM
    # ======================
    "json_schema": MediaType(
        mime="application/schema+json",
        format=DocumentFormat.JSON_SCHEMA,
        standard=DocumentStandard.MSDM,
        extensions=[".schema.json"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="JSON Schema"
    ),
    "xsd": MediaType(
        mime="application/xml",
        format=DocumentFormat.XSD,
        standard=DocumentStandard.MSDM,
        extensions=[".xsd"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="XML Schema Definition"
    ),
    "sql_ddl": MediaType(
        mime="text/plain",
        format=DocumentFormat.SQL_DDL,
        standard=DocumentStandard.MSDM,
        extensions=[".sql", ".ddl"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="SQL Data Definition Language"
    ),
    "erd": MediaType(
        mime="application/xml",               # often stored as XML
        format=DocumentFormat.ERD,
        standard=DocumentStandard.MSDM,
        extensions=[".erd"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Entity‑Relationship Diagram (generic)"
    ),
    "uml_xmi": MediaType(
        mime="application/xmi+xml",
        format=DocumentFormat.UML_XMI,
        standard=DocumentStandard.MSDM,
        extensions=[".xmi", ".uml"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="UML XMI"
    ),
        "plantuml": MediaType(
        mime="text/plain",
        format=DocumentFormat.PLANTUML,
        standard=DocumentStandard.MSDM,
        extensions=[".plantuml", ".puml", ".pu"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="PlantUML Diagram"
    ),
    "proto": MediaType(
        mime="text/plain",
        format=DocumentFormat.PROTOBUF,
        standard=DocumentStandard.MSDM,
        extensions=[".proto"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Protobuf IDL"
    ),
    "avro_schema": MediaType(
        mime="application/vnd.apache.avro+json",
        format=DocumentFormat.AVRO_SCHEMA,
        standard=DocumentStandard.MSDM,
        extensions=[".avsc"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Apache Avro Schema"
    ),
    "thrift_idl": MediaType(
        mime="text/plain",
        format=DocumentFormat.THRIFT_IDL,
        standard=DocumentStandard.MSDM,
        extensions=[".thrift"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Apache Thrift IDL"
    ),
    "graphql_schema": MediaType(
        mime="application/graphql-schema+json",   # common MIME
        format=DocumentFormat.GRAPHQL_SCHEMA,
        standard=DocumentStandard.MSDM,
        extensions=[".graphql", ".gql"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="GraphQL Schema"
    ),
    "owl": MediaType(
        mime="application/rdf+xml",
        format=DocumentFormat.OWL,
        standard=DocumentStandard.MSDM,
        extensions=[".owl", ".rdf"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Web Ontology Language (OWL)"
    ),
    "cue": MediaType(
        mime="text/plain",
        format=DocumentFormat.CUE,
        standard=DocumentStandard.MSDM,
        extensions=[".cue"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="CUE Data Language"
    ),
    
    
    # ======================
    # MSDM - NoSQL, Time-based
    # ======================
    
    "cql": MediaType(
        mime="text/plain",
        format=DocumentFormat.CQL,
        standard=DocumentStandard.MSDM,
        extensions=[".cql", ".cqlsh"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Cassandra Query Language Schema"
    ),
    "mongodb_schema": MediaType(
        mime="application/json",
        format=DocumentFormat.MONGODB_SCHEMA,
        standard=DocumentStandard.MSDM,
        extensions=[".mongoose.js", ".validator.json"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="MongoDB Schema (Mongoose / Validator)"
    ),
    "influxdb_schema": MediaType(
        mime="text/plain",
        format=DocumentFormat.INFLUXDB_SCHEMA,
        standard=DocumentStandard.MSDM,
        extensions=[".influxql", ".flux"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="InfluxDB Measurement Schema"
    ),
    "elasticsearch_mapping": MediaType(
        mime="application/json",
        format=DocumentFormat.ELASTICSEARCH_MAPPING,
        standard=DocumentStandard.MSDM,
        extensions=[".mapping.json", ".es.json"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Elasticsearch Index Mapping"
    ),
    "neo4j_schema": MediaType(
        mime="text/plain",
        format=DocumentFormat.NEO4J_SCHEMA,
        standard=DocumentStandard.MSDM,
        extensions=[".cypher", ".cql"],   # note: .cql also used for Cassandra, detection will distinguish
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Neo4j Cypher Schema"
    ),    
    "python_model": MediaType(
        mime="text/plain",
        format=DocumentFormat.PYTHON_MODEL,
        standard=DocumentStandard.MSDM,
        extensions=[".py"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Python class for model definition"
    ),    
    "typescript_interface": MediaType(
        mime="text/plain",
        format=DocumentFormat.TYPESCRIPT_INTERFACE,
        standard=DocumentStandard.MSDM,
        extensions=[".ts"],
        kind=MediaContentKind.SCHEMA_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Python class for model definition"
    ),    

    # ======================
    # SSDM
    # ======================
    "openapi_yaml": MediaType(
        mime="application/x-yaml",
        format=DocumentFormat.OPENAPI_YAML,
        standard=DocumentStandard.SSDM,
        extensions=[".yaml", ".yml"],       # detected by content
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="OpenAPI (Swagger) YAML"
    ),
    "openapi_json": MediaType(
        mime="application/json",
        format=DocumentFormat.OPENAPI_JSON,
        standard=DocumentStandard.SSDM,
        extensions=[".json"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="OpenAPI (Swagger) JSON"
    ),
    "wsdl": MediaType(
        mime="application/xml",
        format=DocumentFormat.WSDL,
        standard=DocumentStandard.SSDM,
        extensions=[".wsdl"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="WSDL Service Definition"
    ),
    "yang": MediaType(
        mime="application/yang",
        format=DocumentFormat.YANG,
        standard=DocumentStandard.SSDM,
        extensions=[".yang"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="YANG Data Model"
    ),
    "mib": MediaType(
        mime="text/plain",
        format=DocumentFormat.MIB,
        standard=DocumentStandard.SSDM,
        extensions=[".mib"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="SNMP MIB"
    ),
    "asyncapi": MediaType(
        mime="application/json",
        format=DocumentFormat.ASYNCAPI,
        standard=DocumentStandard.SSDM,
        extensions=[".asyncapi.json", ".asyncapi.yaml"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="AsyncAPI"
    ),
    "raml": MediaType(
        mime="application/raml+yaml",
        format=DocumentFormat.RAML,
        standard=DocumentStandard.SSDM,
        extensions=[".raml"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="RAML"
    ),
    "apib": MediaType(
        mime="text/vnd.apiblueprint+markdown",
        format=DocumentFormat.API_BLUEPRINT,
        standard=DocumentStandard.SSDM,
        extensions=[".apib"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="API Blueprint"
    ),
    "webidl": MediaType(
        mime="text/plain",
        format=DocumentFormat.WEB_IDL,
        standard=DocumentStandard.SSDM,
        extensions=[".webidl"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Web IDL"
    ),
    "postman_collection": MediaType(
        mime="application/json",
        format=DocumentFormat.POSTMAN_COLLECTION,
        standard=DocumentStandard.SSDM,
        extensions=[".postman_collection.json"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Postman Collection"
    ),
    "cddl": MediaType(
        mime="text/plain",
        format=DocumentFormat.CDDL,
        standard=DocumentStandard.SSDM,
        extensions=[".cddl"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="CBOR Data Definition Language"
    ),
    "mcp": MediaType(
        mime="application/json",
        format=DocumentFormat.MCP,
        standard=DocumentStandard.SSDM,
        extensions=[".mcp.json"],
        kind=MediaContentKind.SERVICE_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Model Context Protocol Server Manifest"
    ),

    # ======================
    # TSDM
    # ======================
    "tsdm_json": MediaType(
        mime="application/json",
        format=DocumentFormat.TSDM_JSON,
        standard=DocumentStandard.TSDM,
        extensions=[".tsdm.json", ".tools.json"],
        kind=MediaContentKind.STRUCTURED,   # or a new kind "tool_definition"
        raw_type=MediaRawType.TEXT,
        description="TSDM Tool Definition (JSON)"
    ),    

    # ======================
    # OSDM
    # ======================
    "bpmn_xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.BPMN_XML,
        standard=DocumentStandard.OSDM,
        extensions=[".bpmn", ".bpmn2"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="BPMN 2.0 XML"
    ),
    "cmmn_xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.CMMN_XML,
        standard=DocumentStandard.OSDM,
        extensions=[".cmmn"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="CMMN 1.1 XML"
    ),
    "dmn_xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.DMN_XML,
        standard=DocumentStandard.OSDM,
        extensions=[".dmn"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="DMN 1.x XML"
    ),
    "pnml_xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.PNML_XML,
        standard=DocumentStandard.OSDM,
        extensions=[".pnml"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Petri Net Markup Language"
    ),
    "graphml_xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.GRAPHML_XML,
        standard=DocumentStandard.OSDM,
        extensions=[".graphml"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="GraphML"
    ),
    "cncf_serverless_workflow_json": MediaType(
        mime="application/json",
        format=DocumentFormat.CNCF_SERVERLESS_WORKFLOW_JSON,
        standard=DocumentStandard.OSDM,
        extensions=[".sw.json"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="CNCF Serverless Workflow JSON"
    ),
    "cncf_serverless_workflow_yaml": MediaType(
        mime="application/x-yaml",
        format=DocumentFormat.CNCF_SERVERLESS_WORKFLOW_YAML,
        standard=DocumentStandard.OSDM,
        extensions=[".sw.yaml", ".sw.yml"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="CNCF Serverless Workflow YAML"
    ),
    "cep_json": MediaType(
        mime="application/json",
        format=DocumentFormat.CEP_JSON,
        standard=DocumentStandard.OSDM,
        extensions=[".cep.json"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT,
        description="Complex Event Processing Definition (JSON)"
    ),



    "uml_state_machine_xml": MediaType(
        mime="application/xml", format=DocumentFormat.UML_STATE_MACHINE_XML,
        standard=DocumentStandard.OSDM, extensions=[".uml", ".xmi"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="UML State Machine (XMI or XML)"
    ),
    "scxml_xml": MediaType(
        mime="application/xml", format=DocumentFormat.SCXML_XML,
        standard=DocumentStandard.OSDM, extensions=[".scxml"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="SCXML State Chart"
    ),
    "epc_xml": MediaType(
        mime="application/xml", format=DocumentFormat.EPC_XML,
        standard=DocumentStandard.OSDM, extensions=[".epc", ".epml"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="Event‑driven Process Chain"
    ),
    "aws_step_functions_json": MediaType(
        mime="application/json", format=DocumentFormat.AWS_STEP_FUNCTIONS_JSON,
        standard=DocumentStandard.OSDM, extensions=[".asl.json"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="AWS Step Functions ASL JSON"
    ),
    "azure_logic_apps_json": MediaType(
        mime="application/json", format=DocumentFormat.AZURE_LOGIC_APPS_JSON,
        standard=DocumentStandard.OSDM, extensions=[".logicapp.json"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="Azure Logic Apps Workflow JSON"
    ),
    "airflow_dag_py": MediaType(
        mime="text/x-python", format=DocumentFormat.AIRFLOW_DAG_PY,
        standard=DocumentStandard.OSDM, extensions=[".py"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="Apache Airflow DAG (Python)"
    ),
    "prefect_dag_py": MediaType(
        mime="text/x-python", format=DocumentFormat.PREFECT_DAG_PY,
        standard=DocumentStandard.OSDM, extensions=[".py"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="Prefect DAG (Python)"
    ),
    "yawl_xml": MediaType(
        mime="application/xml", format=DocumentFormat.YAWL_XML,
        standard=DocumentStandard.OSDM, extensions=[".yawl"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="YAWL Specification"
    ),
    "xpd_xml": MediaType(
        mime="application/xml", format=DocumentFormat.XPDL_XML,
        standard=DocumentStandard.OSDM, extensions=[".xpdl", ".xml"],
        kind=MediaContentKind.ORCHESTRATION_DEFINITION,
        raw_type=MediaRawType.TEXT, description="XPDL Process Definition"
    ),
    # ======================
    # FALLBACK TYPES
    # ======================
    "binary": MediaType(
        mime="application/octet-stream",
        format=DocumentFormat.UNKNOWN,
        standard=DocumentStandard.UNKNOWN,
        extensions=[".bin"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY,
        description="Generic Binary Data"
    ),

    "text_generic": MediaType(              # renamed to avoid conflict with the USDM "txt"
        mime="text/plain",
        format=DocumentFormat.UNKNOWN,
        standard=DocumentStandard.UNKNOWN,
        extensions=[".text", ".log"],       # additional text extensions not captured above
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT,
        description="Plain Text (generic)"
    ),
}


class MediaTypeRegistry:
    """Logical wrapper around MEDIA_TYPES data."""
    
    _items = MEDIA_TYPES

    @classmethod
    def get_by_format(cls, fmt: DocumentFormat) -> Optional[MediaType]:
        for mt in cls._items.values():
            if mt.format == fmt:
                return mt
        return None

    @classmethod
    def get_by_extension(cls, ext: str) -> Optional[MediaType]:
        if not ext.startswith("."): ext = f".{ext}"
        for mt in cls._items.values():
            if ext.lower() in [e.lower() for e in mt.extensions]:
                return mt
        return None

    @classmethod
    def get_by_mime(cls, mime: str) -> Optional[MediaType]:
        for mt in cls._items.values():
            if mt.mime == mime:
                return mt
        return None

    @classmethod
    def all(cls) -> List[MediaType]:
        return list(cls._items.values())