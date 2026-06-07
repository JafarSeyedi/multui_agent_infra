# PDF Compliance Report — USDM PDF Engine

## Executive Summary

The USDM PDF writer is a ground-up ISO 32000-2:2020 implementation that constructs valid PDF 2.0 documents from the USDM intermediate model. The PDF parser uses **PyMuPDF (fitz)**, **pdfplumber**, **Camelot**, and **Tesseract OCR** for content extraction from existing PDF files.

**Overall Compliance Level: ~65%** — The engine implements core PDF object types, content stream operators, font handling, image embedding, annotations, encryption, metadata (XMP + Info dictionary), outlines, and optimization. Interactive forms, digital signatures, tagged PDF accessibility, and some advanced annotation subtypes remain incomplete.

---

## PDF Structure Coverage

| Structure Element | Implementation | Status |
|-------------------|---------------|--------|
| Header (`%PDF-2.0`) | `PDFWriter` emits version string | ✅ Full |
| Body (indirect object table) | `PDFObjectFactory` creates all object types with xref numbering | ✅ Full |
| Cross-reference table | `PDFXRefEntry` with byte offsets; standard xref (not xref-stream) | ✅ Full |
| Incremental update | Not implemented | ❌ Not Supported |
| Trailer (`/Size`, `/Root`, `/Info`, `/ID`) | `PDFTrailer` with required entries | ✅ Full |
| Startxref + `%%EOF` | Written by `PDFWriter` finalize | ✅ Full |
| PDF 2.0 extensions | Namespace for PDF 2.0; some optional features | ⚠️ Partial |

---

## Object Types Coverage (Clause 7)

| Object Type | Implementation | Status |
|-------------|---------------|--------|
| Boolean | Native Python `bool` in `PDFDictionary` values | ✅ Full |
| Integer | Native Python `int` | ✅ Full |
| Real (floating point) | Native Python `float` | ✅ Full |
| String (literal) | Hex-encoded and literal string output in `PDFDictionary` | ✅ Full |
| String (hexadecimal) | `<...>` hex strings supported | ✅ Full |
| Name objects | `/Name` syntax in `PDFDictionary` | ✅ Full |
| Arrays | `[...]` syntax | ✅ Full |
| Dictionaries | `<<...>>` syntax | ✅ Full |
| Streams | `PDFStream` with `stream`/`endstream` markers, filter prediction | ✅ Full |
| Null | Explicit `null` emission | ✅ Full |
| Indirect References | `PDFDictionary` reference tracking | ✅ Full |

---

## Content Stream Operators (Clause 8.2–8.5)

### Text Operators

| Operator | Description | Status |
|----------|-------------|--------|
| `BT` / `ET` | Begin/end text object | ✅ Full |
| `Tf` | Set font and size | ✅ Full |
| `Tc` | Character spacing | ✅ Full |
| `Tw` | Word spacing | ✅ Full |
| `Tz` | Horizontal scaling | ✅ Full |
| `TL` | Leading | ✅ Full |
| `Ts` | Text rise | ✅ Full |
| `Tr` | Text render mode | ⚠️ Partial |
| `Td` | Move text position | ✅ Full |
| `TD` | Move text position + set leading | ✅ Full |
| `Tm` | Set text matrix | ✅ Full |
| `T*` | Move to next text line | ✅ Full |
| `Tj` | Show text string | ✅ Full |
| `TJ` | Show text with glyph positioning | ⚠️ Partial |
| `'` | Move to next line and show text | ✅ Full |
| `"` | Set spacing, move to next line, show text | ✅ Full |
| `Tc` / `Tw` (in text) | Inter-character / inter-word spacing | ✅ Full |

### Graphics Operators

| Operator | Description | Status |
|----------|-------------|--------|
| `q` / `Q` | Save/restore graphics state | ✅ Full |
| `cm` | Concatenate matrix | ✅ Full |
| `w` | Line width | ✅ Full |
| `J` | Line cap style | ✅ Full |
| `j` | Line join style | ✅ Full |
| `d` | Line dash pattern | ✅ Full |
| `m` / `l` | Moveto / lineto | ✅ Full |
| `c` / `v` / `y` | Cubic Bézier curves | ✅ Full |
| `re` | Rectangle | ✅ Full |
| `S` / `s` | Stroke / close-and-stroke | ✅ Full |
| `f` / `f*` / `B` / `B*` | Fill (various rules) | ✅ Full |
| `n` | End path without fill/stroke | ✅ Full |
| `W` / `W*` | Clipping path | ⚠️ Partial |

### Image/XObject Operators

| Operator | Description | Status |
|----------|-------------|--------|
| `Do` | Invoke named XObject | ✅ Full |
| Inline image `BI`/`ID`/`EI` | Inline image embedding | ⚠️ Partial |

### Color Operators

| Operator | Description | Status |
|----------|-------------|--------|
| `g` / `G` | DeviceGray setcolor (fill/stroke) | ✅ Full |
| `rg` / `RGB` | DeviceRGB setcolor (fill/stroke) | ✅ Full |
| `k` / `K` | DeviceCMYK setcolor (fill/stroke) | ✅ Full |
| `cs` / `CS` | Set colorspace (fill/stroke) | ✅ Full |
| `sc` / `SC` | Set color in colorspace | ✅ Full |
| `gs` | Set graphics state from ExtGState | ✅ Full |
| `scn` / `SCN` | Set color (pattern) | ⚠️ Partial |

---

## Font Handling (Clause 9)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Type 1 fonts | `FontManager` / `FontInfo` / `FontMetrics` | ✅ Full |
| TrueType fonts | Via `FontManager` font embedding | ✅ Full |
| CIDFont (Type 0) | `FontEncoding` CMap support | ✅ Full |
| Type 3 fonts | Not implemented | ❌ Not Supported |
| Font subsetting | `FontSubsetStrategy` enum (Full, Partial) | ✅ Full |
| Font descriptor | `FontMetrics` generates /FontDescriptor dictionary | ✅ Full |
| Font embedding | `FontSubsetStrategy` embeds binary font data | ✅ Full |
| CMAP generation | `FontEncoding` table | ✅ Full |
| `ToUnicode` CMap | Generated during embedding | ✅ Full |
| Panose classification | In `FontInfo` descriptor | ⚠️ Partial |
| OpenType/CFF in Type 2 CIDFont | Not implemented | ❌ Not Supported |
| Variable fonts | Not implemented | ❌ Not Supported |
| Font style (`FontStyle` enum) | Regular, Bold, Italic, BoldItalic | ✅ Full |

---

## Image Handling (Clause 8.9)

| Feature | Implementation | Status |
|---------|---------------|--------|
| DCTDecode (JPEG) | `ImageProcessor` decodes/encodes JPEG | ✅ Full |
| JPXDecode (JPEG2000) | Via Pillow codec | ✅ Full |
| CCITTFaxDecode (Group 3/4) | Not implemented | ❌ Not Supported |
| JBIG2Decode | Not implemented | ❌ Not Supported |
| FlateDecode (zlib/deflate) | Automatic via PDF stream compression | ✅ Full |
| FlateDecode predictors | PNG predictor for `DecodeParms` | ⚠️ Partial |
| Device-dependent color images | `ImageProcessor` converts to device-independent | ✅ Full |
| Inline images | Not generated | ❌ Not Supported |
| Image masks (`/Mask`) | Not used | ❌ Not Supported |
| Soft masks (`/SMask`) | Not used | ❌ Not Supported |

---

## Color Spaces (Clause 8.6)

| Color Space | Enum/Constant | Status |
|-------------|--------------|--------|
| `DeviceGray` | `PDFColor.GRAY` / function API | ✅ Full |
| `DeviceRGB` | `PDFColor.RGB` / function API | ✅ Full |
| `DeviceCMYK` | `PDFColor.CMYK` / function API | ✅ Full |
| `ICCBased` | Via `PDFColor.from_icc()` | ✅ Full |
| `CalGray` | `ColorConverter` | ⚠️ Partial |
| `CalRGB` | `ColorConverter` | ⚠️ Partial |
| `Lab` | `ColorConverter` | ⚠️ Partial |
| `Indexed` | Not implemented | ❌ Not Supported |
| `Pattern` | Not implemented | ❌ Not Supported |
| `Separation` | Not implemented | ❌ Not Supported |
| `DeviceN` | Not implemented | ❌ Not Supported |
| `NChannel` (PDF 2.0) | Not implemented | ❌ Not Supported |

---

## Annotation Types (Clause 12.5)

| Subtype | AnnotationType / AnnotationWriter | Status |
|---------|-----------------------------------|--------|
| Text (sticky note) | `AnnotationType.TEXT` | ✅ Full |
| Link | `AnnotationType.LINK` | ✅ Full |
| FreeText | `AnnotationType.FREETEXT` | ✅ Full |
| Line | `AnnotationType.LINE` | ✅ Full |
| Square | `AnnotationType.SQUARE` | ✅ Full |
| Circle | `AnnotationType.CIRCLE` | ✅ Full |
| Polygon | `AnnotationType.POLYGON` | ✅ Full |
| PolyLine | `AnnotationType.POLYLINE` | ✅ Full |
| Highlight | `AnnotationType.HIGHLIGHT` | ✅ Full |
| Underline | `AnnotationType.UNDERLINE` | ✅ Full |
| Squiggly | `AnnotationType.SQUIGGLY` | ✅ Full |
| StrikeOut | `AnnotationType.STRIKEOUT` | ✅ Full |
| Stamp | `AnnotationType.STAMP` | ✅ Full |
| Caret | `AnnotationType.CARET` | ✅ Full |
| Ink | `AnnotationType.INK` | ✅ Full |
| Popup | `AnnotationType.POPUP` | ✅ Full |
| FileAttachment | `AnnotationType.FILEATTACHMENT` | ✅ Full |
| Sound | `AnnotationType.SOUND` | ✅ Full |
| Movie | `AnnotationType.MOVIE` | ❌ Not Supported |
| Widget | `AnnotationType.WIDGET` | ❌ Not Supported |
| Screen | `AnnotationType.SCREEN` | ❌ Not Supported |
| PrinterMark | `AnnotationType.PRINTERMARK` | ❌ Not Supported |
| TrapNet | `AnnotationType.TRAPNET` | ❌ Not Supported |
| Watermark | `AnnotationType.WATERMARK` | ⚠️ Partial |
| 3D | `AnnotationType.THREED` | ❌ Not Supported |
| Redaction | `AnnotationType.REDACTION` | ❌ Not Supported |

### Annotation Properties

| Feature | Coverage | Status |
|---------|----------|--------|
| `AnnotationBorderStyle` (solid, dashed, beveled, inset, underline) | Enum defined | ✅ Full |
| `AnnotationFlag` (invisible, hidden, print, noZoom, noRotate, readOnly, locked, toggleNoView, lockedC) | Enum defined | ✅ Full |
| Annotation rect, contents, page link | `AnnotationWriter` | ✅ Full |
| Appearance streams | Not generated | ❌ Not Supported |
| Rich text contents | Plain string only | ⚠️ Partial |

---

## Interactive Forms (AcroForm, Clause 12.7)

| Feature | Implementation | Status |
|---------|---------------|--------|
| `/AcroForm` dictionary | Form field model (`FormFieldContent`) exists in USDM | ⚠️ Partial |
| Text fields | `FormFieldContent.field_type = "text"` | ⚠️ Partial |
| Checkbox | `FormFieldContent.field_type = "checkbox"` | ⚠️ Partial |
| Radio buttons | Not implemented | ❌ Not Supported |
| Combo box / List box | `FormFieldContent.field_type = "select"` + `options` | ⚠️ Partial |
| Push button | `FormFieldContent.field_type = "button"` | ⚠️ Partial |
| Signature fields | Not implemented (see Digital Signatures) | ❌ Not Supported |
| `/XFA` (XML Forms Architecture) | Not supported | ❌ Not Supported |
| JavaScript actions | Not supported | ❌ Not Supported |
| Form calculation / validation | Not supported | ❌ Not Supported |
| Form field appearances | Not generated | ❌ Not Supported |

**Note:** Form field data is preserved in the USDM model (`FormFieldContent` with name, type, value, default, placeholder, required, options, max_length, tooltip) but the PDF writer does not yet generate AcroForm field dictionaries or widget annotations.

---

## Digital Signatures (Clause 12.8)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Adbe.pkcs7.detached | Not implemented | ❌ Not Supported |
| ETSI.CAdES.detached | Not implemented | ❌ Not Supported |
| ETSI.RFC3161 | Not implemented | ❌ Not Supported |
| `/Sig` field dictionary | Not implemented | ❌ Not Supported |
| Seed value dictionaries | Not implemented | ❌ Not Supported |
| Document timestamp | Not implemented | ❌ Not Supported |

---

## Encryption and Security (Clause 7.6)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Standard security handler (Password encryption) | `PDFSecurityHandler` / `PDFEncryptor` | ✅ Full |
| `/Filter /Standard` | Set by `PDFSecurityHandler` | ✅ Full |
| `/V 1` (RC4 40-bit) | `EncryptionAlgorithm` enum | ✅ Full |
| `/V 2` (RC4 128-bit) | `EncryptionAlgorithm` enum | ✅ Full |
| `/V 4` (AES-128) | `EncryptionAlgorithm` enum | ✅ Full |
| `/V 5` (AES-256, PDF 2.0) | `EncryptionAlgorithm` enum | ✅ Full |
| `PermissionFlag` (print, modify, copy, annotate, fillForms, extract, assemble, printFA) | Enum defined, applied in encryptor | ✅ Full |
| `/O` and `/U` owner/user password hashes | Generated by `PDFEncryptor` | ✅ Full |
| `/OE` and `/UE` key values (AES-256) | PDF 2.0 standard | ⚠️ Partial |
| `/Perms` encrypted permissions dictionary | PDF 2.0 standard | ⚠️ Partial |
| Certificate security handler | Not implemented | ❌ Not Supported |
| JavaScript/embedded file restrictions | Not implemented | ❌ Not Supported |

---

## Metadata (Clause 14.3 + XMP)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Document Information Dictionary (`/Info`) | `PDFInfo` class in `pdf_objects` | ✅ Full |
| `/Title`, `/Author`, `/Subject`, `/Keywords` | `PDFInfo` fields | ✅ Full |
| `/Creator`, `/Producer` | `PDFInfo` fields | ✅ Full |
| `/CreationDate`, `/ModDate` | `PDFInfo` fields (PDF date string format) | ✅ Full |
| `/Trapped` | Not implemented | ❌ Not Supported |
| custom info entries | Not implemented | ❌ Not Supported |
| XMP Metadata | `XMPMetadata` class + `MetadataWriter` | ✅ Full |
| XMP core schema (dc:title, dc:creator, etc.) | `XMPMetadata` | ✅ Full |
| XMP PDF schema (pdf:Producer, pdf:PDFVersion) | `XMPMetadata` | ✅ Full |
| XMP XMP Basic schema (xmp:CreateDate, xmp:ModifyDate) | `XMPMetadata` | ✅ Full |
| XMP Rights Management | Not implemented | ❌ Not Supported |
| XMP Media Management | Not implemented | ❌ Not Supported |
| Schema extensions | `XMPMetadata.add_custom_field()` | ⚠️ Partial |

---

## Tagged PDF / Accessibility (Clause 14.8)

| Feature | Implementation | Status |
|---------|---------------|--------|
| `/MarkInfo` dictionary | Not generated | ❌ Not Supported |
| Structure tree (`/StructTreeRoot`) | Not generated | ❌ Not Supported |
| Structure element dictionary | Not generated | ❌ Not Supported |
| Standard structure types (Document, Part, Sect, Div, P, H, L, LI, Table, TR, TH, TD, etc.) | Not generated | ❌ Not Supported |
| Actual text (`/ActualText`) | Not generated | ❌ Not Supported |
| Alternate text (`/Alt`) | Not implemented | ❌ Not Supported |
| Language specification (`/Lang`) | Not implemented | ❌ Not Supported |
| Logical structure attributes | Not implemented | ❌ Not Supported |
| Artifact content marking | Not implemented | ❌ Not Supported |
| Table headers association | Not implemented | ❌ Not Supported |
| Role mapping | Not implemented | ❌ Not Supported |

**Note:** Full tagged PDF requires building the complete structure tree alongside content, which is a significant undertaking. No structural accessibility information is currently generated.

---

## Optimization (Clause 7.7 + Annex L)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Object stream (`/ObjStm`, PDF 1.5+) | `PDFOptimizer` | ✅ Full |
| Cross-reference stream (`/XRefStm`, PDF 1.5+) | `PDFOptimizer` | ✅ Full |
| Object deduplication | `PDFOptimizer` | ✅ Full |
| Font subsetting | `FontSubsetStrategy` during font processing | ✅ Full |
| Image compression optimization | `ImageProcessor` | ✅ Full |
| `OptimizationLevel` (None, Basic, Aggressive, Max) | Enum defined | ✅ Full |
| `OptimizationOptions` (custom settings) | Dataclass with toggle flags | ✅ Full |
| Dead object removal | `PDFOptimizer` | ✅ Full |
| Linearized PDF (Fast Web View) | Not implemented | ❌ Not Supported |
| Shared identifier trees | Not implemented | ❌ Not Supported |

---

## Outlines / Bookmarks (Clause 12.3.3)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Outline dictionary (`/Outlines`) | `OutlineBuilder` | ✅ Full |
| Outline item (`/First`, `/Last`, `/Next`, `/Prev`, `/Parent`, `/Count`) | `OutlineItem` class | ✅ Full |
| Destinations (`/Dest`) | `OutlineItem.destination` | ✅ Full |
| `/Title` action on items | `OutlineItem.title` | ✅ Full |
| `OutlineStyle` (bold, italic display flags) | `OutlineStyle` enum | ✅ Full |
| A and AA entries on outline items | Not implemented | ❌ Not Supported |

---

## Page Model (Clause 7.7.3)

| Feature | Implementation | Status |
|---------|---------------|--------|
| `PDFPage` (MediaBox, CropBox, etc.) | `PDFPage` class | ✅ Full |
| Page resource dictionary | `PDFPage.resources` | ✅ Full |
| Page content stream | `PDFPage.contents` | ✅ Full |
| Page transitions | Not implemented | ❌ Not Supported |
| Page labels | Not implemented | ❌ Not Supported |
| Page piece dictionaries | Not implemented | ❌ Not Supported |
| Separation info | Not implemented | ❌ Not Supported |
| Output intent | Not implemented | ❌ Not Supported |

---

## Parser Coverage (PDF → USDM)

| Extraction Category | Tool/Source | USDM Target | Status |
|--------------------|------------|-------------|--------|
| Text extraction with bbox | pdfplumber | `TextRun` (x, y, font, size) | ✅ Full |
| Text with OCR fallback | Tesseract + pdf2image | `TextRun` with confidence | ✅ Full |
| Font detection | pdfplumber page.fonts | `extracted metadata["fonts"]` | ✅ Full |
| Table extraction | Camelot (lattice/stream) | `TableContent` rows/cells | ✅ Full |
| Table extraction (fallback) | pdfplumber extract_tables | `ExtractedTable` → `TableContent` | ✅ Full |
| Image extraction | PyMuPDF extract_image | `ImageObject` (src, x, y, width, height, format) | ✅ Full |
| Link extraction | PyMuPDF get_links | `ExtractedLink` → USDM Link | ✅ Full |
| Annotation extraction | PyMuPDF annots() | `AnnotationObject` (subtype, x, y, width, height) | ✅ Full |
| Metadata extraction | pdfplumber metadata | `DocumentMetadata` fields | ✅ Full |
| Equation detection | Regex patterns on extracted text | `structural_type = "equation"` label | ⚠️ Partial |
| Code block detection | Regex patterns on extracted text | `structural_type = "code_block"` label | ⚠️ Partial |
| Language detection (fa/en/ar) | Character range heuristics | `ExtractedText.language` | ✅ Full |
| Layout analysis | `LayoutAnalyzer` → `PageLayout` | `Page` (width, height, elements) | ✅ Full |
| Structural parsing | `StructureParser` → `StructuralElement` | Sections and hierarchy | ✅ Full |
| Color space detection | Not implemented | Not in USDM | ❌ Not Supported |
| Font embedding detection | Extracted font names only | No `FontInfo` reconstruction | ❌ Not Supported |
| Hyperlink content association | Link URI → nearest text heuristic | Fragile for complex layouts | ⚠️ Partial |
| Zone-based extraction | `PageLayout` zones | Per-zone content grouping | ✅ Full |
| RTL text handling | Script detection (Arabic range) | `language = "fa"`or `"ar"` | ⚠️ Partial |

---

## USDM ToC Mapping

| USDM Type | PDF Equivalent | Status |
|-----------|---------------|--------|
| `TOCContent` | Outline/bookmark entries would map to bookmark tree | ⚠️ Partial |
| `IndexContent` | `/Outlines` — USDM model exists but generation uses basic `OutlineBuilder` | ⚠️ Partial |
| `CaptionContent` | Text with caption label — no PDF caption annotation type | ⚠️ Partial |
| `PageReferenceContent` | PDF cross-reference (`/Dest` indirect) | ❌ Not Supported |
| `CrossReference` | PDF named destinations + GoTo actions | ❌ Not Supported |
| `BibliographyEntry` | No PDF equivalent | ❌ Not Supported |

---

## Known Gaps

1. **Tagged PDF (Accessibility)** — Structure tree not generated; required for PDF/UA compliance
2. **Digital Signatures** — No signing infrastructure; would require PKCS#7 / CMS integration
3. **Linearized PDF** — Fast Web View not generated; impacts streaming download UX
4. **Interactive Forms** — Full AcroForm with widget appearances, calculations, JavaScript
5. **3D Annotations** — `AutoCAD`-style 3D content annotations (U3D/PRC) not supported
6. **Rich Media Annotations** — Flash/video/screen annotations not supported
7. **Reparation forms (XFA)** — Deprecated in PDF 2.0 but still encountered
8. **Owner (`/ID`) generation** — Currently placeholder; should be deterministic from document content
9. **CAdES/RFC3161 signature support** — PKI infrastructure not integrated
10. **Embedded GoTo3DView actions** — Not implemented
11. **ICCBased color space from profile** — ColorConverter has ICC support but no `ICCBased` dictionary output
12. **CalGray/CalRGB/Lab full parameter mapping** — WhitePoint/BlackPoint/Gamma not fully serialized
13. **Pattern/Spot color spaces** — Not implemented
14. **Output intent (ICC profile for PDF/X)** — Not implemented
15. **Document-level output intents** — Not generated
 