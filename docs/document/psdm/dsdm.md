Below is the complete documentation for the **Data Standard Definition Model (DSDM)** and its full suite of parsers.  
It covers the model’s architecture, every parser’s capabilities, available options, schema‑driven features, and practical usage examples.

---

# **DSDM – Data Standard Definition Model**

## 1. Overview

DSDM is a **format‑neutral representation of instance data** (JSON, XML, YAML, CSV, SQL results, binary serialisations, NoSQL records). It is built atop the **Metadata Standard Definition Model (MSDM)** which describes data schemas, tables, type systems, and constraints.

The two models are fully aligned:  
- **DSDM nodes** can be linked to their **MSDM definitions** (`Entity` / `Attribute`) via `SchemaBinding`.  
- Parsers can use an MSDM schema to **validate fields, coerce types, and inject default values** while building the DSDM tree.  
- Writers can use the same binding to enforce field ordering, required‑field checks, and type‑aware serialisation.

DSDM is designed to be the single internal representation for all data inside a document pipeline, enabling seamless conversion between formats and schema‑based processing.

---

## 2. Core Components

### 2.1 `DataNode`

A node in a hierarchical data tree.

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | `str` | Unique identifier for the node. |
| `path` | `str` | Absolute path from the root (e.g., `$.store.book[0].title`). |
| `name` | `str \| None` | Key or tag name. |
| `kind` | `DataNodeKind` | **Structural type**: `OBJECT`, `ARRAY`, `SCALAR`, `XML_ELEMENT`, `XML_ATTRIBUTE`, `XML_TEXT`, `XML_COMMENT`, etc. |
| `value` | `DataValue \| None` | Typed scalar value (for leaf nodes). |
| `children` | `list[DataNode]` | Child nodes. |
| `attributes` | `list[DataNode]` | XML attributes (only for XML elements). |
| `metadata` | `dict[str, Any]` | Free‑form metadata (namespaces, missing‑required flags, etc.). |
| `namespace` | `str \| None` | XML namespace URI or prefix. |
| `is_required` | `bool` | Whether the field is required (from schema). |
| `validation_rules` | `list[str]` | Deprecated – use `schema_binding` instead. |
| **`schema_binding`** | `SchemaBinding \| None` | **Key integration point** – links this node to its MSDM definition. |

### 2.2 `DataValue`

A strongly‑typed atomic value.

| Field | Type | Description |
|-------|------|-------------|
| `scalar_type` | `ScalarType` | MSDM scalar type (e.g., `STRING`, `INT`, `FLOAT`, `BOOLEAN`, `DATETIME`, `BINARY`, etc.). |
| `value` | `Any` | The actual Python value. |
| `lexical_value` | `str \| None` | The original string representation (for round‑tripping). |

### 2.3 `DataDocument`

The root container for a data tree, extending `BaseDocument`.

| Field | Type | Description |
|-------|------|-------------|
| `root` | `DataNode` | The top‑level data node. |
| `schema_ref` | `DataSchemaReference \| None` | Optional reference to the MSDM schema that describes this data. |
| `capabilities` | `DataDocumentCapabilities` | Hints about the original format (comments, namespaces, etc.). |

### 2.4 `SchemaBinding`

Connects a `DataNode` to exactly one MSDM definition.

| Field | Type | Description |
|-------|------|-------------|
| `entity` | `Entity \| None` | The MSDM entity (for OBJECT nodes that represent a whole entity). |
| `attribute` | `Attribute \| None` | The MSDM attribute (for leaf or field nodes). |
| `source_schema` | `MSDMDocument \| None` | The originating schema document. |

---

## 3. Integration with MSDM

The **base parser** (`BaseDSDMParser`) provides a shared pipeline:

1. **Parse raw bytes → DataNode tree** (using `_parse_to_datanode`).  
2. **Schema binding** (if an `MSDMDocument` is supplied via `DSDMParseOptions.schema`):  
   - Recursively matches node names to entity/attribute definitions.  
   - Injects **default values** from `Attribute.default_value`.  
   - **Coerces types** (e.g., CSV strings → `int`, `float`, `datetime`) based on `Attribute.data_type`.  
   - Marks **required fields** that are missing.  
3. **Validation** can be run after tree construction using `DataDocument.validate_against_schema()` (checks patterns and constraints).

Writers (not covered in this document) can then use the `schema_binding` to enforce field order and required checks during serialisation.

---

## 4. Parser Base Classes

### 4.1 `BaseDSDMParser` (extends `BaseDocumentParser`)

All DSDM parsers inherit from this class.  
**Key methods:**

- `parse_bytes(data, document_id, source_name, metadata, options) -> DataDocument`
- `_parse_to_datanode(raw_bytes, options) -> DataNode` (abstract)
- `_detect_media_type(source_name) -> str` (abstract)

### 4.2 `DSDMParseOptions`

Extends `ParseOptions` with schema‑related switches:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `schema` | `MSDMDocument \| None` | `None` | Schema to bind and validate against. |
| `inject_defaults` | `bool` | `True` | If `True`, missing values are replaced with the schema’s default. |
| `validate_against_schema` | `bool` | `True` | Enable post‑parse validation (calls `_bind_schema`). |

---

## 5. Format‑Specific Parsers

### 5.1 JSON Parser

**Class:** `JSONParser`  
**File:** `json_parser.py`  
**Media type:** `application/json`  
**Extensions:** `.json`

**Capabilities:**
- Parses any valid JSON (object, array, scalar) into a `DataNode` tree.
- Supports schema‑driven validation/defaults via the base parser (post‑tree binding).

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.json_parser import JSONParser
from engines.document.parsers.dsdm_parsers.base_dsdm_parser import DSDMParseOptions
from engines.document.models.msdm_models import MSDMDocument  # load your schema

parser = JSONParser()

# Without schema
doc = await parser.parse_bytes(
    json_bytes,
    document_id="doc1",
    source_name="data.json"
)

# With schema
options = DSDMParseOptions(schema=my_msdm_document)
doc = await parser.parse_bytes(
    json_bytes,
    document_id="doc1",
    source_name="data.json",
    options=options
)
```

---

### 5.2 XML Parser

**Class:** `XMLParser`  
**File:** `xml_parser.py`  
**Media type:** `application/xml`  
**Extensions:** `.xml`

**Capabilities:**
- Parses XML using Python’s `xml.etree.ElementTree`.
- Preserves **namespace** information and XML‑specific node kinds: `XML_ELEMENT`, `XML_ATTRIBUTE`, `XML_TEXT`.
- Schema‑binding is applied after the tree is built; currently there is no automatic mapping of XML namespaces to MSDM namespaces (can be handled by custom logic).

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.xml_parser import XMLParser

parser = XMLParser()
doc = await parser.parse_bytes(xml_bytes, "doc1", "config.xml", options=options)
```

---

### 5.3 YAML Parser

**Class:** `YAMLParser`  
**File:** `yaml_parser.py`  
**Media type:** `application/x-yaml`  
**Extensions:** `.yaml`, `.yml`

**Capabilities:**
- Uses PyYAML’s `safe_load`.
- Supports all YAML structures (mappings, sequences, scalars).
- Comments are **not** preserved; the `parse_comments` option is ignored.
- Schema‑binding and defaults work post‑parse.

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.yaml_parser import YAMLParser

parser = YAMLParser()
doc = await parser.parse_bytes(yaml_bytes, "doc1", "config.yaml", options=options)
```

---

### 5.4 CSV / TSV Parser

**Class:** `CSVTSVParser`  
**File:** `csv_tsv_parser.py`  
**Media type:** `text/csv` (or `text/tab-separated-values`)  
**Extensions:** `.csv`, `.tsv`, `.tab`

**Capabilities:**
- Reads CSV/TSV with configurable delimiter (`options.custom["delimiter"]`).
- First row is treated as a header (field names).
- **Schema‑driven parsing** (when `options.schema` is supplied):
  - Maps header names (case‑insensitive) to MSDM attributes.
  - **Coerces string values** to the target types: `INT`, `FLOAT`, `BOOLEAN`, `DATETIME`, `DATE`, `TIME`, `UUID`, `BINARY` (base64), `DECIMAL`.
  - Injects **default values** for missing fields.
  - Marks missing required fields with `metadata["_required_missing"] = True`.
- Output tree: an `ARRAY` node containing `OBJECT` nodes (each row).

**Custom Options:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `delimiter` | `str` | `","` | The column delimiter. |

**Usage (schemaless):**

```python
from engines.document.parsers.dsdm_parsers.csv_tsv_parser import CSVTSVParser

parser = CSVTSVParser()
options = DSDMParseOptions()
doc = await parser.parse_bytes(csv_bytes, "doc1", "data.csv", options=options)
# doc.root.kind == ARRAY, children are OBJECTs with field names from header
```

**Usage (with schema):**

```python
# Assume 'person_entity' has attributes: name(string), age(int), email(string, required)
options = DSDMParseOptions(schema=my_schema)
doc = await parser.parse_bytes(csv_bytes, "doc1", "people.csv", options=options)
# 'age' will be DataValue(scalar_type=INT), missing email will be flagged
```

---

### 5.5 SQL Data Parser

**Class:** `SQLDataParser`  
**File:** `sql_parser.py`  
**Media type:** `application/vnd.sql-data+json`  
**Extensions:** `.sql_data`

**Capabilities:**
- **Byte input**: expects a JSON‑encoded list of row objects.
- **Live database connection**: via `fetch_from_database()` using the `AsyncDBConnection` protocol.
- Full **MSDM integration**:
  - Maps column names (case‑insensitive) to entity attributes.
  - Coerces Python types from the DB driver (e.g., `datetime`, `Decimal`, `UUID`, `bytes`) to the corresponding DSDM `ScalarType`.
  - Injects defaults and marks required fields.
- Auto‑generates `SELECT` query from an entity (or uses a custom query).

**AsyncDBConnection Protocol:**

Any async database driver that provides `execute(query, params=None) -> list[dict[str, Any]]` can be used (e.g., `asyncpg`, `aiosqlite`, `Motor`’s `db.command`, etc.).

**Usage – Byte Parsing:**

```python
parser = SQLDataParser()
# Suppose raw_bytes contains JSON: [{"id": 1, "name": "Alice"}, ...]
doc = await parser.parse_bytes(raw_bytes, "doc1", "result.json",
                               options=DSDMParseOptions(schema=user_entity_schema))
```

**Usage – Live Database:**

```python
# asyncpg connection
conn = await asyncpg.connect(...)

# Define a DSDM entity
from engines.document.models.msdm_models import Entity, Attribute, DataType, ScalarType
user_entity = Entity(
    name="users",
    kind=EntityKind.TABLE,
    attributes=[
        Attribute(name="id", data_type=DataType(base=ScalarType.INT), required=True),
        Attribute(name="name", data_type=DataType(base=ScalarType.STRING)),
        Attribute(name="created_at", data_type=DataType(base=ScalarType.DATETIME))
    ]
)

parser = SQLDataParser()
options = DSDMParseOptions(schema=MSDMDocument(entities=[user_entity], ...))
doc = await parser.fetch_from_database(
    connection=conn,
    entity=user_entity,
    options=options,
    query_override="SELECT id, name, created_at FROM users WHERE active = true"
)
# doc.root is an ARRAY of OBJECTs with typed values
```

---

### 5.6 Binary Parsers

#### 5.6.1 Generic Binary

**Class:** `BinaryParser`  
**File:** `binary_parser.py`  
**Media type:** `application/octet-stream`  
**Extensions:** (none specific)

Represents any opaque binary data as a single `SCALAR` node with `BINARY` type and base64 lexical value.

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.binary_parser import BinaryParser
parser = BinaryParser()
doc = await parser.parse_bytes(binary_blob, "doc1", "file.bin")
node = doc.root  # kind == SCALAR, value.scalar_type == BINARY
```

#### 5.6.2 MessagePack

**Class:** `MsgPackParser`  
**File:** `msgpack_parser.py`  
**Media type:** `application/msgpack`  
**Extensions:** `.msgpack`

Parses MessagePack bytes to a Python structure and then to a DSDM tree (schema binding works post‑parse).

#### 5.6.3 CBOR

**Class:** `CBORParser`  
**File:** `cbor_parser.py`  
**Media type:** `application/cbor`  
**Extensions:** `.cbor`

Parses CBOR (RFC 7049) data using the `cbor2` library.

#### 5.6.4 BSON

**Class:** `BSONParser`  
**File:** `bson_parser.py`  
**Media type:** `application/bson`  
**Extensions:** `.bson`

Decodes BSON (MongoDB’s serialisation). If multiple documents are found, they are returned as an `ARRAY`; a single document becomes an `OBJECT`.

#### 5.6.5 Pickle

**Class:** `PickleParser`  
**File:** `pickle_parser.py`  
**Media type:** `application/python-pickle`  
**Extensions:** `.pickle`, `.pkl`

Requires `unsafe_operations_allowed=True` in `ParseOptions` for security.

#### 5.6.6 Protobuf

**Class:** `ProtobufParser`  
**File:** `protobuf_parser.py`  
**Media type:** `application/protobuf`  
**Extensions:** `.pb`

**Requires schema** – two custom options must be set in `DSDMParseOptions.custom`:

| Option | Type | Description |
|--------|------|-------------|
| `protobuf_descriptor` | `bytes` | Serialised `FileDescriptorSet` for the protobuf schema. |
| `message_name` | `str` | Fully qualified message name (e.g., `my.package.User`). |

Internally uses the descriptor pool and dynamic message factory to deserialise the binary message, then converts it to a Python dict (using `google.protobuf.json_format`) and builds the DSDM tree.

**Usage:**

```python
options = DSDMParseOptions(
    schema=my_msdm_entity,  # optional MSDM representation
    custom={
        "protobuf_descriptor": compiled_fds_bytes,
        "message_name": "tutorial.Person"
    }
)
parser = ProtobufParser()
doc = await parser.parse_bytes(proto_bytes, "doc1", "person.pb", options=options)
```

---

### 5.7 NoSQL Data Parsers

These parsers can consume raw bytes (e.g., BSON for MongoDB) or connect to live databases.

#### 5.7.1 MongoDB Parser

**Class:** `MongoDBParser` (extends `BSONParser`)  
**File:** `mongodb_parser.py`

**Capabilities:**
- Parses `.bson` files (inherited from `BSONParser`).
- `fetch_collection(collection, entity, query, options) -> DataDocument`
  - Takes a Motor/PyMongo **collection** object.
  - Projects fields based on the MSDM entity’s attributes.
  - Coerces MongoDB‑specific types (`ObjectId` → string, `Decimal128` → `Decimal`, `Binary`, `Code`, `Timestamp`, `DBRef`).
  - Inserts defaults and marks required fields.

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.mongodb_parser import MongoDBParser

parser = MongoDBParser()
doc = await parser.fetch_collection(
    collection=mongo_db.users,
    entity=user_entity,
    query={"active": True},
    options=DSDMParseOptions(schema=my_schema)
)
```

#### 5.7.2 Cassandra Parser

**Class:** `CassandraParser`  
**File:** `cassandra_parser.py`

**`fetch_from_cassandra(session, entity, keyspace, options) -> DataDocument`**

- Uses an async Cassandra `Session` to run a SELECT.
- Maps row attributes to the MSDM entity’s attributes.
- Coerces Cassandra driver return types (e.g., `decimal.Decimal`, `uuid.UUID`, `datetime`, `date`, `time`, `set`, `list`, `dict`).

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.cassandra_parser import CassandraParser

parser = CassandraParser()
doc = await parser.fetch_from_cassandra(
    session=cassandra_session,
    entity=product_entity,
    keyspace="inventory"
)
```

#### 5.7.3 Redis Parser

**Class:** `RedisParser`  
**File:** `redis_parser.py`

**`fetch_from_redis(redis_client, pattern, count, entity, options) -> DataDocument`**

- Scans keys using `SCAN` and fetches values with `MGET`.
- Produces an **OBJECT** where each key is a field name and the value is a scalar.
- If an MSDM entity is provided, the **first attribute** defines the type for all values (useful for typed caches).

**Usage:**

```python
from engines.document.parsers.dsdm_parsers.redis_parser import RedisParser

parser = RedisParser()
doc = await parser.fetch_from_redis(
    redis_client=redis_conn,
    pattern="user:*",
    entity=value_entity  # e.g., a single attribute 'value' of type int
)
# doc.root is an OBJECT with keys like "user:1" -> DataValue(INT, 42)
```

---

## 6. Schema Inference from Data

When a `DataDocument` is built without a schema (e.g., from JSON), you can **derive an MSDM schema** automatically using the class method `DataDocument.infer_msdm()`.

```python
msdm = DataDocument.infer_msdm(
    data_document=doc,
    entity_name="User",
    kind=EntityKind.OBJECT
)
# msdm is an MSDMDocument with one entity containing attributes for each field,
# typed as STRUCT for nested objects or ARRAY for arrays
```

This satisfies the requirement: *“msdm can be extracted from raw data because some data files … are self descriptive.”*

---

## 7. DSDM Utilities

Located in `dsdm_utils.py`:

- `scalar_value(value) -> DataValue` – converts a Python value to a `DataValue` (handles `bool`, `int`, `float`, `bytes` → BINARY, `str`).
- `build_node_from_python(value, path, name, ...) -> DataNode` – converts Python `dict`/`list`/scalar into a full `DataNode` tree (handles XML dict representations).
- `node_to_python(node) -> DataNode` – the inverse, for writers.
- `xml_to_python_dict(root) -> dict` – converts an XML‑structured `DataNode` to a human‑readable nested dict.

---

## 8. Summary of Parsers

| Parser | Format | Schema‑driven | Coercion | Defaults | Required | Live Connection |
|--------|--------|---------------|----------|----------|----------|-----------------|
| JSONParser | JSON | ✅ (post‑bind) | ❌ (native) | ✅ | ✅ | – |
| XMLParser | XML | ✅ (post‑bind) | ❌ (native) | ✅ | ✅ | – |
| YAMLParser | YAML | ✅ (post‑bind) | ❌ (native) | ✅ | ✅ | – |
| CSVTSVParser | CSV/TSV | ✅ (inline) | ✅ (string→typed) | ✅ | ✅ | – |
| SQLDataParser | SQL result / DB | ✅ (inline) | ✅ (DB types) | ✅ | ✅ | ✅ |
| BinaryParser | Binary blob | ✅ (post‑bind) | ❌ | ✅ | ✅ | – |
| MsgPackParser | MsgPack | ✅ (post‑bind) | ❌ | ✅ | ✅ | – |
| CBORParser | CBOR | ✅ (post‑bind) | ❌ | ✅ | ✅ | – |
| BSONParser | BSON | ✅ (post‑bind) | ❌ | ✅ | ✅ | – |
| PickleParser | Pickle | ✅ (post‑bind) | ❌ | ✅ | ✅ | – |
| ProtobufParser | Protobuf | ✅ (required) | ❌ (relies on protobuf schema) | ✅ | ✅ | – |
| MongoDBParser | MongoDB BSON / live | ✅ (live) | ✅ (Mongo types) | ✅ | ✅ | ✅ |
| CassandraParser | Cassandra rows | ✅ (live) | ✅ (Cassandra types) | ✅ | ✅ | ✅ |
| RedisParser | Redis key‑value | ✅ (optional) | ✅ (value type attr) | ✅ | ✅ | ✅ |

---

## 9. Quick Start Example (JSON + Schema)

```python
import asyncio
from engines.document.parsers.dsdm_parsers.json_parser import JSONParser
from engines.document.parsers.dsdm_parsers.base_dsdm_parser import DSDMParseOptions
from engines.document.models.msdm_models import MSDMDocument, Entity, Attribute, DataType, ScalarType

# 1. Define an MSDM schema
person_entity = Entity(
    name="Person",
    kind=EntityKind.OBJECT,
    attributes=[
        Attribute(name="name", data_type=DataType(base=ScalarType.STRING), required=True),
        Attribute(name="age", data_type=DataType(base=ScalarType.INT), default_value="0"),
        Attribute(name="email", data_type=DataType(base=ScalarType.STRING))
    ]
)
schema = MSDMDocument(
    title="Person schema",
    document_id="schema1",
    media_type="application/json",
    entities=[person_entity]
)

# 2. Parse JSON
json_data = b'{"name": "Alice", "email": "a@example.com"}'
parser = JSONParser()
options = DSDMParseOptions(schema=schema, inject_defaults=True)
doc = asyncio.run(parser.parse_bytes(json_data, "doc1", "person.json", options=options))

# 3. Inspect
root = doc.root
for child in root.children:
    if child.name == "age":
        print(child.value.value)  # 0 (default injected)
    if child.name == "name":
        print(child.value.value)  # Alice
```

---

## 10. Extending

New format parsers should subclass `BaseDSDMParser`, implement `_parse_to_datanode`, and optionally override `_bind_schema` if special binding logic is needed. Writers follow the same pattern inheriting from `BaseDSDMWriter`.

All the infrastructure is designed to keep the models clean and the conversion logic separate, ensuring maintainability and alignment between DSDM and MSDM.

# 11. DSDM Writers – Full Documentation

This section complements the parser documentation (Sections 1–10) and describes every writer capable of converting a DSDM `DataDocument` back into a target format.  
All writers inherit from `BaseDSDMWriter` and can leverage an optional MSDM schema for type‑aware formatting, field ordering, required‑field enforcement, and extra‑field stripping.

---

## 11.1 Writer Base Class & Options

### 11.1.1 `BaseDSDMWriter` (extends `BaseDocumentWriter`)

All writers share this foundation. Key methods:

- `write(document: DataDocument) -> bytes` – serialise the whole document.
- `write_stream(document: DataDocument) -> AsyncIterator[bytes]` – yields the serialised bytes.
- `write_to_file(document, target: Path, options: dict | None)` – write to a file.

Abstract methods that concrete writers must implement:

- `_serialise_root(root_node: DataNode, options: DSDMWriteOptions) -> bytes`
- `_serialise_node(node: DataNode, options: DSDMWriteOptions) -> bytes`

The base class also provides schema‑aware helpers:

- `_get_attribute_order(node, options) -> list[str] | None`
- `_should_include_field(field_name, node, options) -> bool`
- `_check_required_fields(node, options) -> None`

### 11.1.2 `DSDMWriteOptions`

Extends `WriteOptions` with writer‑specific settings:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `schema` | `MSDMDocument \| None` | `None` | MSDM schema to drive field order, omission, and required checks. |
| `strip_extra_fields` | `bool` | `False` | If `True`, fields not in the schema are omitted from output. |
| `require_all_required` | `bool` | `True` | If `True`, a missing required field raises a `ValueError` before writing. |

Additional format‑specific options can be placed in `options.custom` (e.g., CSV delimiter, binary format choice).

---

## 11.2 Format‑Specific Writers

### 11.2.1 JSON Writer

**Class:** `JSONWriter`  
**Media type:** `application/json`  
**Extensions:** `.json`

**Capabilities:**  
- Serialises any DSDM tree to JSON.  
- Respects `pretty_print` (indentation).  
- Accepts schema for field ordering and required‑field validation.

**Sample usage (file):**

```python
from engines.document.writers.dsdm_writers.json_writer import JSONWriter
from engines.document.parsers.dsdm_parsers.json_parser import JSONParser
from engines.document.writers.dsdm_writers.base_dsdm_writer import DSDMWriteOptions
import asyncio

# Parse a JSON file first (or create a DataDocument manually)
parser = JSONParser()
doc = asyncio.run(parser.parse_bytes(json_bytes, "doc1", "data.json"))

# Write back with pretty print
writer = JSONWriter()
options = DSDMWriteOptions(pretty_print=True, schema=my_msdm_schema)
json_output = asyncio.run(writer.write(doc))
```

**Sample usage (schema‑driven ordering):**

If `options.schema` is provided, the writer will output fields in the order defined by the entity’s attributes. Extraneous fields can be removed with `strip_extra_fields=True`.

---

### 11.2.2 XML Writer

**Class:** `XMLWriter`  
**Media type:** `application/xml`  
**Extensions:** `.xml`

**Capabilities:**  
- Converts **any** DSDM tree into well‑formed XML.  
- Object keys become element names, arrays become repeating `<item>` elements, scalars become leaf elements.  
- Native XML elements (with namespaces, attributes, text nodes) are preserved exactly.  
- Schema ordering for child elements is applied if the entity defines an ordered attribute list.

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.xml_writer import XMLWriter

writer = XMLWriter()
options = DSDMWriteOptions(pretty_print=True, schema=my_msdm_schema)
xml_bytes = asyncio.run(writer.write(doc))
with open("output.xml", "wb") as f:
    f.write(xml_bytes)
```

**Note:** The writer automatically handles nested objects, arrays, and mixed content. If the root is a plain object, it wraps everything in a `<document>` element – adjust the root tag in the writer constructor if needed (extendable).

---

### 11.2.3 YAML Writer

**Class:** `YAMLWriter`  
**Media type:** `application/x-yaml`  
**Extensions:** `.yaml`, `.yml`

**Capabilities:**  
- Writes YAML (1.1/1.2) from any DSDM tree.  
- Uses PyYAML’s `dump` with `allow_unicode`.  
- Schema validation and field ordering (via YAML mapping key order – though YAML spec does not guarantee key order, PyYAML preserves insertion order; schema can control that order).

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.yaml_writer import YAMLWriter

writer = YAMLWriter()
options = DSDMWriteOptions(schema=my_msdm_schema)
yaml_bytes = asyncio.run(writer.write(doc))
print(yaml_bytes.decode())
```

---

### 11.2.4 CSV / TSV Writer

**Class:** `CSVTSVWriter`  
**Media type:** `text/csv` (or `text/tab-separated-values`)  
**Extensions:** `.csv`, `.tsv`, `.tab`

**Capabilities:**  
- Expects a root **ARRAY of OBJECTs** (rows).  
- Header row is derived from the first row or from the MSDM entity’s attribute list (if provided).  
- Applies schema‑driven column ordering, field omission, and required checks.  
- Formats values using type‑aware conversion (dates become ISO strings, binary becomes base64, etc.).  
- Dialect options (delimiter, quoting, etc.) are set via `options.custom`:

| Custom Key | Type | Default | Description |
|------------|------|---------|-------------|
| `delimiter` | `str` | `","` | Field delimiter. |
| `quotechar` | `str` | `'"'` | Quoting character. |
| `escapechar` | `str` | `None` | Escape character. |
| `doublequote` | `bool` | `True` | Double‑quote escaping. |
| `skipinitialspace` | `bool` | `False` | Skip spaces after delimiter. |
| `lineterminator` | `str` | `"\r\n"` | Line terminator. |

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.csv_tsv_writer import CSVTSVWriter

writer = CSVTSVWriter()
options = DSDMWriteOptions(
    schema=my_msdm_schema,         # for ordering & required checks
    custom={"delimiter": ";"}
)
csv_bytes = asyncio.run(writer.write(data_document))
with open("output.csv", "wb") as f:
    f.write(csv_bytes)
```

---

### 11.2.5 Generic Binary Writer (Pluggable)

**Class:** `BinaryWriter`  
**Media type:** `application/octet-stream`  
**Extensions:** `.bin` (generic)

**Capabilities:**  
- **Mode 1 (raw passthrough):** If the root node is a BINARY scalar, the original bytes are returned unchanged.  
- **Mode 2 (structured serialisation):** For any other tree, the writer converts the DSDM tree to a Python object and then serialises it using a configurable binary format. The default is **MessagePack**.

To choose a different format, set `options.custom["binary_format"]` to one of:
- `"msgpack"` (default)
- `"cbor"`
- `"bson"`
- `"pickle"` (requires `unsafe_operations_allowed=True`)
- a custom callable that takes a Python object and returns bytes.

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.binary_writer import BinaryWriter

# Structured tree → MessagePack
writer = BinaryWriter()
options = DSDMWriteOptions(custom={"binary_format": "cbor"})
cbor_bytes = asyncio.run(writer.write(doc))

# Raw binary node passthrough
binary_node = ...  # DataNode with ScalarType.BINARY
raw_bytes = asyncio.run(writer.write(DataDocument(root=binary_node, ...)))
```

---

### 11.2.6 MessagePack Writer

**Class:** `MsgPackWriter`  
**Media type:** `application/msgpack`  
**Extensions:** `.msgpack`

**Capabilities:**  
- Directly converts the DSDM tree to Python and packs it with `msgpack.packb(use_bin_type=True)`.  
- Supports schema validation before writing.

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.msgpack_writer import MsgPackWriter

writer = MsgPackWriter()
output = asyncio.run(writer.write(doc))
```

---

### 11.2.7 CBOR Writer

**Class:** `CBORWriter`  
**Media type:** `application/cbor`  
**Extensions:** `.cbor`

Similar to MessagePack but uses `cbor2.dumps`.

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.cbor_writer import CBORWriter

writer = CBORWriter()
output = asyncio.run(writer.write(doc))
```

---

### 11.2.8 BSON Writer

**Class:** `BSONWriter`  
**Media type:** `application/bson`  
**Extensions:** `.bson`

**Capabilities:**  
- Converts DSDM tree to Python, then encodes with `bson.encode`.  
- If the root is a list, it automatically wraps it in a document with a configurable key (`options.custom["bson_wrapper_key"]`, default `"documents"`).  
- Schema validation is applied before encoding.

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.bson_writer import BSONWriter

writer = BSONWriter()
options = DSDMWriteOptions(custom={"bson_wrapper_key": "people"})
bson_bytes = asyncio.run(writer.write(doc))
```

---

### 11.2.9 Pickle Writer

**Class:** `PickleWriter`  
**Media type:** `application/python-pickle`  
**Extensions:** `.pickle`, `.pkl`

**Capabilities:**  
- Converts the DSDM tree to Python native structures and pickles them.  
- Requires `unsafe_operations_allowed=True` in `DSDMWriteOptions` for security.

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.pickle_writer import PickleWriter

writer = PickleWriter()
options = DSDMWriteOptions(unsafe_operations_allowed=True)
pickle_bytes = asyncio.run(writer.write(doc))
```

---

### 11.2.10 Protobuf Writer

**Class:** `ProtobufWriter`  
**Media type:** `application/protobuf`  
**Extensions:** `.pb`

**Prerequisites:**  
A compiled `FileDescriptorSet` and the fully qualified message name must be provided in `options.custom`.  
The writer uses `google.protobuf.json_format.ParseDict` to populate a dynamic message from the Python dict derived from the DSDM tree, then serialises it to binary.

**Custom Options:**

| Key | Type | Description |
|-----|------|-------------|
| `protobuf_descriptor` | `bytes` | Serialised `FileDescriptorSet` (`*.desc` file). |
| `message_name` | `str` | Fully qualified protobuf message name (e.g., `"tutorial.Person"`). |

**Sample usage:**

```python
from engines.document.writers.dsdm_writers.protobuf_writer import ProtobufWriter

writer = ProtobufWriter()
options = DSDMWriteOptions(
    schema=my_msdm_schema,
    custom={
        "protobuf_descriptor": open("person.desc", "rb").read(),
        "message_name": "tutorial.Person"
    }
)
proto_bytes = asyncio.run(writer.write(doc))
```

---

## 11.3 Database‑Backed Writers (with Connection Management)

These writers can either serialise to a file or, more commonly, connect to a live database and execute write operations directly.

### 11.3.1 SQL Data Writer

**Class:** `SQLDataWriter`

**Capabilities:**  
- Generates **SQL UPSERT** statements (PostgreSQL dialect by default; configurable via custom options).  
- Can produce a file with literal `INSERT` statements, or execute directly against an async connection.  
- Requires an MSDM entity to map DSDM fields to table columns.

**Connection Protocol:**  
Any object that supports `async execute(query: str, params=None) -> None` and `async executemany(query: str, params_list: list[tuple]) -> None` works (e.g., `asyncpg`, `aiosqlite`).

**Custom Options (for database write):**

| Key | Type | Description |
|-----|------|-------------|
| `upsert_key` | `str` | Column name to use for `ON CONFLICT` (default `"id"`). |

**Sample usage – Write to file:**

```python
from engines.document.writers.dsdm_writers.sql_writer import SQLDataWriter

writer = SQLDataWriter()
options = DSDMWriteOptions(schema=user_entity_schema)
sql_text = asyncio.run(writer.write(doc))  # bytes containing SQL statements
with open("upsert.sql", "wb") as f:
    f.write(sql_text)
```

**Sample usage – Write directly to database:**

```python
import asyncpg
from engines.document.writers.dsdm_writers.sql_writer import SQLDataWriter

conn = await asyncpg.connect(dsn="...")
writer = SQLDataWriter()
options = DSDMWriteOptions(
    schema=user_entity_schema,
    custom={"upsert_key": "email"}  # use email as conflict target
)
await writer.write_to_database(
    doc=doc,
    connection=conn,
    options=options,
    table_name="users"
)
```

---

### 11.3.2 MongoDB Writer

**Class:** `MongoDBWriter`

**Capabilities:**  
- Produces BSON bytes for file output (using `BSONWriter`).  
- Provides `write_to_collection(collection, doc, options, entity)` to insert documents directly into a MongoDB collection using Motor or PyMongo async driver.  
- Converts DSDM scalar types to BSON‑compatible Python types (e.g., `Decimal` → `Decimal128`, `bytes` → `Binary`).

**Sample usage – Insert into MongoDB:**

```python
from motor.motor_asyncio import AsyncIOMotorClient
from engines.document.writers.dsdm_writers.mongodb_writer import MongoDBWriter

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.my_database
collection = db.users

writer = MongoDBWriter()
options = DSDMWriteOptions(schema=user_entity_schema)
await writer.write_to_collection(
    doc=doc,
    collection=collection,
    options=options
)
```

---

### 11.3.3 Cassandra Writer

**Class:** `CassandraWriter`

**Capabilities:**  
- Does not support file output (raises `NotImplementedError`); intended for live writes.  
- `write_to_cassandra(session, doc, keyspace, entity, options)` – converts DSDM rows into INSERT statements (asynchronous, using prepared statements).

**Sample usage:**

```python
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from engines.document.writers.dsdm_writers.cassandra_writer import CassandraWriter

cluster = Cluster(["127.0.0.1"])
session = cluster.connect("my_keyspace")

writer = CassandraWriter()
options = DSDMWriteOptions(schema=product_entity_schema)
await writer.write_to_cassandra(
    session=session,
    doc=doc,
    keyspace="my_keyspace",
    options=options
)
```

---

### 11.3.4 Redis Writer

**Class:** `RedisWriter`

**Capabilities:**  
- File output produces a JSON representation of the key‑value object.  
- `write_to_redis(redis_client, doc, options)` – writes key‑value pairs to Redis. If a value is itself an object or array, it’s stored as a JSON string.

**Sample usage:**

```python
import redis.asyncio as aioredis
from engines.document.writers.dsdm_writers.redis_writer import RedisWriter

r = await aioredis.Redis.from_url("redis://localhost")
writer = RedisWriter()
options = DSDMWriteOptions(schema=my_value_entity_schema)
await writer.write_to_redis(
    redis_client=r,
    doc=doc,
    options=options
)
```

---

## 11.4 Writer Quick Reference Table

| Writer | Output Format | File Output | Live Database Write |
|--------|---------------|-------------|---------------------|
| JSONWriter | JSON | ✅ | – |
| XMLWriter | XML | ✅ | – |
| YAMLWriter | YAML | ✅ | – |
| CSVTSVWriter | CSV / TSV | ✅ | – |
| BinaryWriter | MsgPack, CBOR, BSON, Pickle (configurable) | ✅ | – |
| MsgPackWriter | MessagePack | ✅ | – |
| CBORWriter | CBOR | ✅ | – |
| BSONWriter | BSON (file) | ✅ | – |
| PickleWriter | Python pickle | ✅ | – |
| ProtobufWriter | Protobuf binary | ✅ | – |
| SQLDataWriter | SQL statements / direct DB | ✅ (SQL dump) | ✅ (async connection) |
| MongoDBWriter | BSON / direct MongoDB | ✅ (BSON) | ✅ (collection insert) |
| CassandraWriter | direct Cassandra | ❌ | ✅ (async session) |
| RedisWriter | JSON / direct Redis | ✅ (JSON) | ✅ (key‑value set) |

All writers share the same schema‑driven features when an MSDM schema is supplied through `DSDMWriteOptions.schema`:

- Field ordering (for formats that respect order, e.g., XML, CSV, JSON).  
- Omission of extra fields (`strip_extra_fields=True`).  
- Required‑field enforcement (`require_all_required=True` raising errors).  
- Type‑aware formatting (e.g., dates in ISO format, binary as base64).

---

# **Appendix A: Known Limitations & Future Roadmap - model and parsers**

## A.1 XML Schema Binding

- **Limitation:** XML elements and attributes are treated as separate node kinds. When binding to an MSDM entity, XML attributes are matched by name just like child elements. This can cause collisions if an element and an attribute share the same name.  
- **Workaround:** Use annotations or a naming convention (e.g., `@attrib_name` for attributes) and adjust the schema‑binding logic in a custom parser if needed.

## A.2 Streaming Data

- **Limitation:** The current DSDM model requires a complete `DataNode` tree to be held in memory. Parsers that work on large datasets (SQL, Cassandra, Redis) fetch all rows at once.  
- **Future:** Introduce a stream‑friendly `DataDocumentChunk` model and `parse_stream` methods that yield partial trees, allowing memory‑efficient processing.

## A.3 Protobuf Text Format

- **Limitation:** Only binary protobuf (`application/protobuf`) is supported. The human‑readable `.textproto` format is not parsed.  
- **Future:** Create a `ProtobufTextParser` using `google.protobuf.text_format` that mirrors the same schema‑driven approach.

## A.4 Custom Data Types

- **Limitation:** The `CUSTOM` scalar type in MSDM is not automatically handled by any parser. Users must implement custom coercers.  
- **Future:** Add a plugin mechanism where users can register type‑specific converters for `CUSTOM` types based on an annotation or the `DataType` parameters.

## A.5 Writer Symmetry

- **Limitation:** Writers (serialisers from DSDM back to target formats) are not yet provided. They are needed for a complete round‑trip.  
- **Future:** Implement `BaseDSDMWriter` subclasses for each format, fully leveraging `schema_binding` for field ordering, type formatting, and required‑field enforcement.

## A.6 Constraint Validation Coverage

- **Limitation:** Currently, only `pattern` constraints are validated automatically after schema binding. Other constraints (min/max length, enumeration, numeric ranges) are ignored.  
- **Future:** Extend `_collect_validation_errors` to check all MSDM constraint types.

## A.7 Mixed Content in XML

- **Limitation:** XML mixed content (text interleaved with elements) is not fully supported. The parser treats text before/after elements as separate `XML_TEXT` nodes, but schema binding may not correctly map them.  
- **Workaround:** Use a custom entity that defines a `STRUCT` with `#text` as an attribute if mixed content is essential.


# Missing production features:

- No logging in parsers/writers.
- No input size limits or resource monitoring.
- Streaming writes are not truly incremental (everything is in memory).
- Cassandra writer doesn't handle prepared statement caching.



# **Appendix B: Known Limitations & Future Roadmap - writers**

**notes, limitations, and recommended enhancements** to bring all writers to the same level of completeness and robustness.

---

## 1. Schema‑Driven Validation Consistency

Currently, some writers call `_check_required_fields` (XML, CSV, Binary) while others (JSON, YAML, MsgPack, etc.) do **not**. This means that even if `require_all_required=True` is set, JSON and YAML writers will silently output documents with missing required fields.

**Enhancement:**  
Add a call to `self._check_required_fields(root_node, options)` at the beginning of every `_serialise_root` method (guarded by the option). This should be part of the base writer’s `write` pipeline, so all writers inherit it automatically.

---

## 2. Stripping Extra Fields

The `strip_extra_fields` option is only effective in writers that iterate over schema‑ordered children (XML, CSV). **JSON and YAML writers** use `node_to_python` which returns the entire tree unchanged – they cannot drop fields not in the schema.

**Enhancement:**  
Create a utility method `_prune_node(node, entity, options)` that recursively removes children not present in the entity. Call it from `write` before serialisation. This would make `strip_extra_fields` work universally.

---

## 3. XML Special Node Kinds

The XML writer currently maps `XML_COMMENT`, `XML_CDATA`, `XML_PROCESSING_INSTRUCTION`, and `XML_DOCTYPE` to a generic `<comment>` element with text content. This is not correct XML.

**Required fix:**  
- `XML_COMMENT` → `<!-- text -->`  
- `XML_CDATA` → `<![CDATA[ text ]]>`  
- `XML_PROCESSING_INSTRUCTION` → `<?target ...?>`  
- `XML_DOCTYPE` → `<!DOCTYPE ...>` (if relevant)

The Python `xml.etree.ElementTree` does not natively support these constructs in tree building. Use `lxml` or build string segments manually for full fidelity.

---

## 4. Binary Writer – Raw Bytes Detection

The check `root_node.value.scalar_type.value == "binary"` relies on the enum’s string value. It is fragile if the enum constant changes. Use `root_node.value.scalar_type == ScalarType.BINARY` instead.

**Fix:** Replace with direct enum comparison.

---

## 5. Protobuf Writer – Input Assumptions

The writer calls `node_to_python(root_node)` and expects the resulting Python object to be a dict that maps exactly to the protobuf message. If the DSDM tree is an array or contains non‑object roots, `ParseDict` will fail.

**Enhancement:**  
Add validation: if the root node is not an OBJECT (or a dict), raise a clear error. Document that the DSDM tree must represent a single message, not a collection.

---

## 6. Database Writers – Entity Resolution

All database writers (SQL, MongoDB, Cassandra, Redis) accept an explicit `entity` argument but also allow falling back to `options.schema.entities[0]`. If the schema contains multiple entities, the writer silently picks the first. This can be confusing.

**Enhancement:**  
If `entity` is `None` and the schema has more than one entity, either require an explicit `entity` or add an `entity_name` option. At minimum, emit a warning.

---

## 7. SQL Writer – Dialect Abstraction

The generated UPSERT uses PostgreSQL syntax (`ON CONFLICT ... DO UPDATE`). For other databases (MySQL, SQLite, SQL Server) the statement is different.

**Enhancement:**  
Make the SQL dialect configurable via `options.custom["sql_dialect"]` (e.g., `"postgresql"`, `"sqlite"`, `"mysql"`) and generate the appropriate UPSERT/INSERT OR REPLACE statement. Also, `E'\\\\x...'` hex escaping for binary is PostgreSQL‑specific.

---

## 8. MongoDB Writer – Missing BSON Type Conversions

The writer correctly converts `Decimal` to `Decimal128` and `bytes` to `Binary`, but it **does not handle**:

- `datetime` → `bson.datetime.datetime` (or just pass through if BSON encoder handles it)  
- `date` / `time` → these are not natively BSON; store as strings or custom types.  
- `ObjectId` strings – should be converted to `ObjectId` if the schema marks it.

**Enhancement:**  
Add a type‑aware converter similar to the parser’s coercion, mapping DSDM scalar types to BSON‑safe Python types.

---

## 9. Cassandra Writer – Prepared Statement Caching

Currently `write_to_cassandra` prepares the INSERT statement **once per call**. For large datasets, this is efficient, but if the user calls the writer multiple times with the same entity, the prepared statement is recreated.

**Enhancement:**  
Allow caching of prepared statements (e.g., by passing a `prepared_statements` dictionary or using an LRU cache). This is a minor performance optimisation.

---

## 10. Redis Writer – Handling Non‑String Keys

In `write_to_redis`, keys are taken from `child.name`. If the original data contained non‑string keys (e.g., integers), they are already converted to strings by the parser. The writer uses them directly. This is fine, but it’s worth noting that numeric keys become strings in Redis.

---

## 11. YAML Writer – Mapping Key Order

Though the YAML spec does not require key order, the writer relies on PyYAML’s insertion order. If `strip_extra_fields` or schema ordering is desired, the writer must first prune and order the Python dict before dumping. Currently it does not.

**Enhancement:** Apply pruning/ordering as part of the common `write` pipeline.

---

## 12. Stream Writing

Only the base writer defines `write_stream` but it simply yields the entire byte result. True streaming (e.g., for huge CSV or array‑of‑objects) is not supported – the whole document is kept in memory.

**Future:**  
Implement incremental writers that build output in chunks (especially for formats like CSV, JSON lines, or BSON documents) and yield parts asynchronously.

---

## 13. Writer Error Collection

Unlike the parsers, writers do not have a built‑in error collection mechanism (they raise exceptions). For batch operations (e.g., writing 10,000 rows to a database), a single error aborts the whole batch.

**Enhancement:**  
Add an option `continue_on_error` that logs errors and continues, or returns a list of failed rows.

---

## 14. Unicode, Encoding, and Binary

Most writers use `options.encoding` consistently. The generic binary writer ignores it (it outputs raw bytes). That’s acceptable, but it should be documented that `encoding` is unused in raw binary mode.

---

## 15. Testing and Edge Cases

No unit tests are provided yet. Edge cases like:

- Circular references (not possible with current tree, but if someone manually creates them)  
- Extremely deep nesting (> recursion limit)  
- Mixed‑content XML (text + elements interleaved)

Should be tested and documented as known limitations.

---

## Summary of Recommended Improvements

| Area | Priority | Action |
|------|----------|--------|
| Required‑field checking in all writers | High | Move to base `write` method or add call in each writer. |
| Strip extra fields in JSON/YAML/Binary | High | Implement a tree‑pruning utility. |
| XML special node handling | High | Properly emit comments, CDATA, PIs. |
| Protobuf input validation | Medium | Ensure root is an object. |
| SQL dialect abstraction | Medium | Add `sql_dialect` custom option. |
| MongoDB BSON type completeness | Medium | Handle datetime, ObjectId, etc. |
| Entity ambiguity if multiple entities | Low | Add `entity_name` option or warning. |
| Streaming support | Low | Future roadmap item. |
| Batch error handling | Low | Optional `continue_on_error` flag. |


---

*This documentation covers version 1.0 of DSDM. For the latest updates, refer to the source code in `engines/document/parsers/dsdm_parsers/`.*



