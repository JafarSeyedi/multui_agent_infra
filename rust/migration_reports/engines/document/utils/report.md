# Migration Report: `engines/document/utils/`

**Analyzed**: 2026-06-13
**Files**: 6 (3 empty stubs, 3 with code)
**Rust target**: `rust/crates/engines-document-utils/` (proposed)

---

## 1. Pre-refactor Analysis

### File inventory

| File | Status | Lines | Description |
|------|--------|-------|-------------|
| `__init__.py` | Active | 9 | Re-exports `BinaryCodec`, `BinaryCodecAdvanced`, `StreamingBinaryCodec` |
| `binary_codec.py` | Active | 100 | Binary encoding/decoding, SHA256 hashing |
| `streaming_binary_codec.py` | Active | 46 | Chunked file-to-payload / payload-to-file |
| `docx_utils.py` | **Empty stub** | 0 | Reserved — no content |
| `ooxml_constants.py` | **Empty stub** | 0 | Reserved — no content |
| `xml_parser.py` | **Empty stub** | 0 | Reserved — no content |

### Dependency graph (internal)

```
__init__.py
  └─ binary_codec.py
  └─ streaming_binary_codec.py ──→ binary_codec.py (uses BinaryCodecAdvanced)
```

### No external consumers found

A repo-wide search for `engines.document.utils`, `BinaryCodec`, and `StreamingBinaryCodec` returned zero results outside the `utils/` package itself. These modules are exported but **currently unused** by any parser, writer, or engine.

### Dead / commented-out code

- `binary_codec.py:57-67` — `GZIP_BASE64`, `ZLIB_BASE64`, `BROTLI_BASE64` encoding branches are fully commented out. The corresponding variants (`GZIP_BASE64`, etc.) do **not exist** in the `BinaryEncoding` enum (`base.py:72-78`).
- `BinaryEncoding.ASCII85` and `BinaryEncoding.URL_SAFE_BASE64` are defined but never handled by either codec — they will raise `ValueError` at runtime.
- `CompressionMethod` enum (`GZIP`, `DEFLATE`, `BROTLI`, `LZ4`, `ZSTD`) exists in `base.py` but is never read or set by any utils code.

### Empty stub risk

`docx_utils.py`, `ooxml_constants.py`, and `xml_parser.py` are zero-length files. If these are awaiting implementation, the Rust counterpart should reserve the crate/namespace but not allocate effort.

---

## 2. Migration Notes — Rust Candidate Scoring

| Component | Score (1-5) | Rationale |
|-----------|-------------|-----------|
| `BinaryCodec` | **4** | Pure data transformation — no Python runtime dependency. Direct `base64` + `sha2` crate mapping. High performance leverage. |
| `BinaryCodecAdvanced` | **4** | Same as above + multi-encoding dispatch. Tight encode/decode loops benefit from native speed. |
| `StreamingBinaryCodec` | **3** | I/O-bound workload — Rust gains are marginal. Chunked SHA256 per block is a hot spot. |
| `docx_utils.py` | **0** | Empty. Do not migrate. |
| `ooxml_constants.py` | **0** | Empty. Do not migrate. |
| `xml_parser.py` | **0** | Empty. Do not migrate. |
| **Package overall** | **3** | 50% of files are empty stubs; the real codecs are good candidates. |

---

## 3. Ownership Map — Function Signatures

All three classes are **stateless** — every method is `@staticmethod`. There is no `self`, no mutable state, no global state.

### `BinaryCodec`

| Signature | Owns | Returns |
|-----------|------|---------|
| `from_bytes(data: bytes, media_type: MediaType, text_encoding: str | None) -> BinaryPayload` | Takes borrowed `data` and `media_type`; allocates & returns new `BinaryPayload` | `BinaryPayload` (owned) |
| `to_bytes(payload: BinaryPayload, text_encoding: str | None) -> bytes` | Takes a reference to `payload`; returns newly allocated `bytes` | `Vec<u8>` (owned) |

### `BinaryCodecAdvanced`

| Signature | Owns | Returns |
|-----------|------|---------|
| `encode(data: bytes, encoding: BinaryEncoding, text_encoding: str | None) -> str` | Takes borrowed `data`; returns owned `String` | `String` (owned) |
| `decode(payload: BinaryPayload, text_encoding: str | None) -> bytes` | Borrows `payload.data` (the encoded string); returns owned `Vec<u8>` | `Vec<u8>` (owned) |

### `StreamingBinaryCodec`

| Signature | Owns | Returns |
|-----------|------|---------|
| `chunk_file_to_payloads(path: str, media_type: MediaType, encoding: BinaryEncoding) -> Generator[BinaryPayload]` | Takes owned `path`; owns the file handle; yields owned `BinaryPayload` per chunk | `impl Iterator<Item = BinaryPayload>` |
| `payloads_to_file(payloads: list[BinaryPayload], output_path: str) -> None` | Borrows `payloads` slice; owns `output_path`; owns file handle for writing | `Result<()>` (in Rust) |

**Key insight**: No shared ownership, no `Rc`/`Arc`, no interior mutability. Direct `&[u8]` → `Vec<u8>` transforms.

---

## 4. Suggested PyO3 Binding

### Approach: Free functions in a `utils` crate

The codecs are stateless static methods. A class wrapper in PyO3 would be pure ceremony. Recommended:

```rust
// Proposed crate: rust/crates/engines-document-utils/src/lib.rs

use pyo3::prelude::*;

#[pyfunction]
fn encode_binary(data: &[u8], encoding: &str, text_encoding: Option<&str>) -> PyResult<String> { ... }

#[pyfunction]
fn decode_binary(data: &str, encoding: &str, text_encoding: Option<&str>) -> PyResult<Vec<u8>> { ... }

#[pyfunction]
fn payload_from_bytes(data: &[u8], media_type: &str, ...) -> PyResult<PyObject> { ... }

#[pyfunction]
fn chunk_file_to_payloads(path: &str, ...) -> PyResult<Vec<PyObject>> { ... }

pub fn init_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encode_binary, m)?)?;
    m.add_function(wrap_pyfunction!(decode_binary, m)?)?;
    m.add_function(wrap_pyfunction!(payload_from_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(chunk_file_to_payloads, m)?)?;
    Ok(())
}
```

**Alternative**: Single `Utils` namespace struct with `impl` blocks — provides logical grouping without class ceremony.

**Recommendation**: Publish as a standalone crate `engines-document-utils` so it can be used from Rust natively (by document parsers/writers) and via PyO3 (for backward compat).

---

## 5. Libraries Analysis

| Python dependency | Rust equivalent | Crates.io notes |
|-------------------|-----------------|-----------------|
| `base64.b64encode` / `b64decode` | `base64` crate | `Engine::encode(&[u8])` / `Engine::decode(&str)` — use `engine::general_purpose::STANDARD` |
| `base64.b32encode` / `b32decode` | `data-encoding` crate | `BASE32.encode()` / `BASE32.decode()` |
| `base64.b16encode` / `b16decode` | `data-encoding` or `hex` crate | `hex::encode()` / `hex::decode()` — or `data-encoding::HEXUPPER` |
| `hashlib.sha256` | `sha2` crate | `Sha256::digest(&[u8])` → `format!("{:x}")` |
| `bytes.fromhex` / `.hex()` | `hex` crate | `hex::decode()` / `hex::encode()` |
| gzip (commented out) | `flate2` crate | `read::GzEncoder` / `read::GzDecoder` |
| zlib (commented out) | `flate2` crate | `Compress` / `Decompress` with `Compression::zlib_conf()` |
| brotli (commented out) | `brotli` crate | `BrotliCompress` / `BrotliDecompress` |
| msgpack (in formats but not utils) | `rmp-serde` | `to_vec()` / `from_slice()` |

### BinaryPayload model in Rust

The Pydantic `BinaryPayload` model should be mirrored as a Rust struct with `serde::Serialize` / `serde::Deserialize`:

```rust
#[derive(Serialize, Deserialize)]
struct BinaryPayload {
    media_type: String,
    encoding: String,
    bytes_content: Option<Vec<u8>>,
    data: Option<String>,
    size_bytes: u64,
    sha256: String,
    chunk_index: u32,
    total_chunks: u32,
    compressed: bool,
    compression_algorithm: Option<String>,
    original_size: Option<u64>,
}
```

---

## 6. Performance Hot Paths

### Hot path 1: `BinaryCodec.from_bytes()` / `BinaryCodecAdvanced.encode()` — base64 + SHA256

- For a 100 MB binary: one pass base64-encode (~500 MB/s in Rust vs ~200 MB/s in CPython) + one pass SHA256
- These are CPU-bound on string manipulation — Rust's `base64` crate uses SIMD on x86_64
- **Expected speedup**: 3-5x per call

### Hot path 2: `StreamingBinaryCodec.chunk_file_to_payloads()` — per-chunk SHA256

- Each 1 MB chunk independently computes `hashlib.sha256(block).hexdigest()`
- In Rust: `Sha256::digest(&block)` per chunk is ~2x faster. Async file reads via `tokio::fs` or `std::io::BufReader` can overlap I/O and hashing.
- **Expected speedup**: 2-4x for throughput

### Hot path 3: `StreamingBinaryCodec.payloads_to_file()` — decode + write

- Sorts payloads by `chunk_index`, decodes each in sequence, writes to file
- Sorting is trivial (`O(n log n)`, n = number of chunks). Decode is sequential.
- Rust can parallelize decode across chunks with `rayon` — `payloads.par_iter().map(|p| decode(p)).collect::<Vec<_>>()`
- **Expected speedup**: 3-10x with parallel decode

### Cold paths (no migration value)

- Empty stubs (`docx_utils.py`, `ooxml_constants.py`, `xml_parser.py`) — no code to migrate

### Profiling note

Benchmarks should target:
1. `BinaryCodecAdvanced.encode()` with BASE64 and RAW (hex) encoding
2. `BinaryCodecAdvanced.decode()` with BASE64 input
3. `StreamingBinaryCodec.chunk_file_to_payloads()` with a 100 MB+ binary file
4. `StreamingBinaryCodec.payloads_to_file()` with 100+ chunks

---

## 7. Error Handling

### Current Python behavior

| Scenario | Python behavior |
|----------|----------------|
| Unsupported `BinaryEncoding` variant | Raises `ValueError(f"Unsupported encoding: {encoding}")` |
| Corrupt base64 string | Propagates `base64.binascii.Error` (not caught) |
| File not found | Propagates `FileNotFoundError` |
| Empty file / zero bytes | Returns `BinaryPayload` with `size_bytes=0` and empty SHA256 |
| `payload.data = None` | Falls back to `''` via `payload.data or ''` — silent |
| `payload.encoding` is unknown | Raises `ValueError` |
| Binary data in `bytes_content` (not `data`) | Never accessed by any codec — dead field |

### Recommended Rust approach

```rust
#[derive(Debug, thiserror::Error)]
pub enum CodecError {
    #[error("unsupported encoding: {0}")]
    UnsupportedEncoding(String),
    #[error("base64 decode error: {0}")]
    Base64Decode(#[from] base64::DecodeError),
    #[error("hex decode error: {0}")]
    HexDecode(#[from] hex::FromHexError),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("missing payload data")]
    MissingData,
}
```

Key improvements over Python:
- `thiserror` for typed, composable errors instead of bare `ValueError`
- No silent fallback for missing data (`None` → error)
- Categorize base64 vs hex vs I/O errors separately
- File-sorted chunk decoding should verify no gaps/missing chunks

### Cross-module boundary

The `BinaryPayload` struct and `BinaryEncoding` / `CompressionMethod` enums live in `engines/document/models/base.py`. The Rust migration of these models should live in a shared models crate (e.g. `engines-document-models`). The utils crate should depend on that models crate, not duplicate the types.

---

## Summary

| Priority | Component | Action | Effort |
|----------|-----------|--------|--------|
| P0 | `BinaryCodec` + `BinaryCodecAdvanced` | Migrate to Rust `base64` + `data-encoding` + `sha2` | 2-3 days |
| P1 | `StreamingBinaryCodec` | Migrate; use `BufReader` + optional `rayon` for parallel decode | 1-2 days |
| P2 | Empty stubs (3 files) | Reserve namespace, no code migration | 0 |
| Cross-cutting | `BinaryPayload` model | Define in shared Rust models crate | 1 day |
| Cross-cutting | PyO3 bindings | Free-function module in `pyo3` feature gate | 1 day |

**Total estimated effort**: 4-6 days for a complete migration including PyO3 bindings.
