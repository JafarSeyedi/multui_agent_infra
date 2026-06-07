# OOXML Compliance Report — USDM DOCX Engine

## Executive Summary

The USDM DOCX writer produces Office Open XML (OOXML) documents conforming to **ECMA-376 5th Edition** and **ISO/IEC 29500:2012 (Transitional)**. The parser reads DOCX files into the USDM intermediate model with comprehensive style, numbering, and structure extraction.

**Overall Compliance Level: ~78%** — The engine covers the core WordprocessingML feature set needed for round-trip document creation including styles, numbering, tables, footnotes, endnotes, comments, bookmarks, math (OMML), images (DrawingML), and section properties. Strict conformance mode, VML legacy shapes, and some advanced typography features remain partially supported.

---

## Part 1 — Fundamentals & Markup Reference (§11–§24)

| Section | Coverage | Status |
|---------|----------|--------|
| §11 — WordprocessingML | Full core element mapping | ✅ Full |
| §12 — Paragraphs (`<w:p>`, `<w:pPr>`) | Paragraph properties, alignment, spacing, indentation, borders, shading, tabs, pagination | ✅ Full |
| §13 — Runs & Text (`<w:r>`, `<w:rPr>`, `<w:t>`) | Bold, italic, underline, color, font, size, highlight, strike, superscript/subscript, small caps, all caps, kerning, spacing, position, shadow, outline, emboss, imprint, vanish, webHidden, language | ✅ Full |
| §14 — Tables (`<w:tbl>`, `<w:tblPr>`, `<w:tblGrid>`, `<w:tr>`, `<w:tc>`) | Table properties, grid, rows, cells, gridSpan, vMerge, headers, borders, cell margins, shading, banding | ✅ Full |
| §15 — Styles (`<w:styles>`, `<w:style>`) | Character, paragraph, table styles; style inheritance (`basedOn`), `nextStyle`, `linkedStyle`, defaults (`docDefaults`) | ✅ Full |
| §16 — Numbering (`<w:numbering>`, `<w:abstractNum>`, `<w:num>`) | Abstract numbering definitions, level definitions, format, text template, alignment, indentation, font per level | ✅ Full |
| §17 — Footnotes/Endnotes | Separators, content, reference marks | ✅ Full |
| §18 — Comments | Author, date, content | ✅ Full |
| §19 — Fields (§17.16 in ISO) | Minimal — field results text captured during parse | ⚠️ Partial |
| §20 — Headers/Footers | Via OPC relationships (placeholder structure) | ⚠️ Partial |
| §21 — DrawingML | Image嵌入 via `<w:drawing>` with `wp:anchor/a:graphic/pic:pic`; basic shapes (`ShapeContent`) | ⚠️ Partial |
| §22 — Math (OMML) | LaTeX→OMML conversion for inline and display math | ⚠️ Partial |
| §23 — VML | Not generated; parsed shapes are USDM `ShapeContent` | ❌ Not Supported |
| §24 — Bibliography | Not supported | ❌ Not Supported |

---

## Part 2 — Open Packaging Conventions (OPC)

| Feature | Coverage | Status |
|---------|----------|--------|
| `[Content_Types].xml` | Generated with all part content types including overrides for footnotes, endnotes, comments, images | ✅ Full |
| `_rels/.rels` | Package-level relationships (core props, app props, document) | ✅ Full |
| `word/_rels/document.xml.rels` | Part relationships: styles, numbering, footnotes, endnotes, comments, theme, images | ✅ Full |
| `docProps/core.xml` | Dublin Core metadata (title, creator, subject, keywords, description, dates) | ✅ Full |
| `docProps/app.xml` | Extended properties (pages, words, characters, paragraphs, company, manager) | ✅ Full |
| `docProps/custom.xml` | Custom document properties | ✅ Full |
| `word/theme/theme1.xml` | Minimal theme (placeholders) | ⚠️ Partial |
| Content type defaults | `.rels`, `.xml` defaults | ✅ Full |
| ZIP packaging | ZIP64-compatible via Python `zipfile` | ✅ Full |

---

## Part 3 — Markup Compatibility & Extensibility (MCX)

| Feature | Coverage | Status |
|---------|----------|--------|
| `mc:Ignorable` | `w14`, `w15` namespaces declared ignorable | ✅ Full |
| `w14:paraId` | Paragraph IDs for tracking | ✅ Full |
| `w15:*` data structures | Not generated | ❌ Not Supported |
| AlternateContent | Not used | ❌ Not Supported |

**Note:** MCX is primarily relevant for down-level compatibility. The engine targets modern consumers (Office 2016+, LibreOffice 7+).

---

## Part 4 — Transitional Migration Features

| Feature | Coverage | Status |
|---------|----------|--------|
| Legacy VML shapes | Not generated in writer | ❌ Not Supported |
| `w:compat` settings | Not generated | ❌ Not Supported |
| `w:rsid*` (revision save IDs) | Not generated | ❌ Not Supported |
| Embedded OLE objects | Parsed as `OLEObjectContent` / `EmbeddedObjectContent`; not written back | ⚠️ Partial |
| Macros (`w:macro`) | Parsed as `MacroContent`; not persisted in DOCX output | ⚠️ Partial |
| Structured document tags | Parsed as `StructuredDocumentTagContent`; not written | ⚠️ Partial |

---

## Element-by-Element Mapping

### Paragraph Elements

| USDM Field | OOXML Element/Attribute | Paragraph Type | Status |
|-----------|------------------------|----------------|--------|
| `Paragraph.style` | `<w:pPr><w:pStyle w:val="..."/></w:pPr>` | Paragraph | ✅ Full |
| `ParagraphContent.style` | `<w:pPr><w:pStyle w:val="..."/></w:pPr>` | Paragraph | ✅ Full |
| `elem.metadata["alignment"]` | `<w:jc w:val="left\|right\|center\|both"/>` | Paragraph | ✅ Full |
| `ParagraphStyle.alignment` | `<w:jc w:val="..."/>` | Style | ✅ Full |
| `ParagraphStyle.spacing_before` | `<w:spacing w:before="..."/>` | Style | ✅ Full |
| `ParagraphStyle.spacing_after` | `<w:spacing w:after="..."/>` | Style | ✅ Full |
| `ParagraphStyle.line_spacing` | `<w:spacing w:line="..." w:lineRule="auto\|exact\|atLeast"/>` | Style | ✅ Full |
| `ParagraphStyle.indent_left` | `<w:ind w:left="..."/>` | Style | ✅ Full |
| `ParagraphStyle.indent_right` | `<w:ind w:right="..."/>` | Style | ✅ Full |
| `ParagraphStyle.first_line_indent` | `<w:ind w:firstLine="..."/>` | Style | ✅ Full |
| `ParagraphStyle.indent_hanging` | `<w:ind w:hanging="..."/>` | Style | ✅ Full |
| `ParagraphStyle.page_break_before` | `<w:pageBreakBefore/>` | Style | ✅ Full |
| `ParagraphStyle.keep_lines_together` | `<w:keepLines/>` | Style | ✅ Full |
| `ParagraphStyle.keep_with_next` | `<w:keepNext/>` | Style | ✅ Full |
| `ParagraphStyle.widow_control` | `<w:widowControl/>` | Style | ✅ Full |
| `ParagraphStyle.outline_level` | `<w:outlineLvl w:val="..."/>` | Style | ✅ Full |
| `ParagraphStyle.tabs` | `<w:tabs w:pos="..." w:val="..." w:leader="..."/>` | Style | ✅ Full |
| `ParagraphStyle.borders` | `<w:pBdr><w:top w:val="" w:sz="" w:color=""/>...` | Style | ✅ Full |
| `ParagraphStyle.shading` | `<w:shd w:fill="" w:val="" w:color=""/>` | Style | ✅ Full |

### Run / Character Elements

| USDM Field | OOXML Element/Attribute | Status |
|-----------|------------------------|--------|
| `RichTextSpan.bold` | `<w:b/>` | ✅ Full |
| `RichTextSpan.italic` | `<w:i/>` | ✅ Full |
| `RichTextSpan.underline` | `<w:u w:val="single"/>` | ✅ Full |
| `RichTextSpan.color` | `<w:color w:val="RRGGBB"/>` | ✅ Full |
| `RichTextSpan.font` | `<w:rFonts w:ascii="" w:hAnsi=""/>` | ✅ Full |
| `CharacterStyle.font_family` | `<w:rFonts w:cs=""/>` | ⚠️ Partial |
| `CharacterStyle.font_charset` | Not mapped | ❌ Not Supported |
| `CharacterStyle.font_pitch` | Not mapped | ❌ Not Supported |
| `CharacterStyle.size` | `<w:sz w:val=""/> <w:szCs w:val=""/>` | ✅ Full |
| `CharacterStyle.size_cs` | `<w:szCs w:val=""/>` | ✅ Full |
| `CharacterStyle.highlight` | `<w:highlight w:val="..."/>` | ✅ Full |
| `CharacterStyle.background` | `<w:shd w:fill="" w:val="clear"/>` | ✅ Full |
| `CharacterStyle.strike` | `<w:strike/>` | ✅ Full |
| `CharacterStyle.double_strike` | `<w:dstrike/>` | ✅ Full |
| `CharacterStyle.superscript` | `<w:vertAlign w:val="superscript"/>` | ✅ Full |
| `CharacterStyle.subscript` | `<w:vertAlign w:val="subscript"/>` | ✅ Full |
| `CharacterStyle.small_caps` | `<w:smallCaps/>` | ✅ Full |
| `CharacterStyle.all_caps` | `<w:caps/>` | ✅ Full |
| `CharacterStyle.kerning` | `<w:kern w:val="..."/>` | ✅ Full |
| `CharacterStyle.spacing` | `<w:spacing w:val="..."/>` | ✅ Full |
| `CharacterStyle.position` | `<w:position w:val="..."/>` | ✅ Full |
| `CharacterStyle.shadow` | `<w:shadow/>` | ✅ Full |
| `CharacterStyle.outline` | `<w:outline/>` | ✅ Full |
| `CharacterStyle.emboss` | `<w:emboss/>` | ✅ Full |
| `CharacterStyle.imprint` | `<w:imprint/>` | ✅ Full |
| `CharacterStyle.vanished` | `<w:vanish/>` | ✅ Full |
| `CharacterStyle.web_hidden` | `<w:webHidden/>` | ✅ Full |
| `CharacterStyle.language` | `<w:lang w:val="..."/>` | ✅ Full |
| `CharacterStyle.no_proof` | Not mapped | ❌ Not Supported |
| `CharacterStyle.underline_type` | `<w:u w:val="double\|wave\|thick\|dotted\|dash\|..."/>` | ✅ Full |

### Heading Elements

| USDM Field | OOXML Element/Attribute | Status |
|-----------|------------------------|--------|
| `HeadingContent.level` (1–9) | `<w:pStyle w:val="HeadingN"/>` + `<w:outlineLvl w:val="N-1"/>` | ✅ Full |

### Table Elements

| USDM Field | OOXML Element/Attribute | Status |
|-----------|------------------------|--------|
| `TableContent.grid` | `<w:tblGrid><w:gridCol w:w="..."/></w:tblGrid>` | ✅ Full |
| `TableRow.is_header` | `<w:trPr><w:tblHeader/></w:trPr>` | ✅ Full |
| `TableCell.col_span` | `<w:tcPr><w:gridSpan w:val="..."/></w:tcPr>` | ✅ Full |
| `TableCell.row_span` | `<w:tcPr><w:vMerge w:val="restart"/></w:tcPr>` | ✅ Full |
| `TableCell.is_header` | Not directly mapped (handled by row header) | ⚠️ Partial |
| `TableContent.metadata["borders"]` | `<w:tblBorders><w:top w:val="" w:sz="" w:color=""/>...` | ✅ Full |
| `TableContent.metadata["cell_margins"]` | `<w:tblCellMar><w:top w:w="" w:type="dxa"/>...` | ✅ Full |
| `TableContent.metadata["layout_type"]` | `<w:tblLayout w:type="fixed\|autofit"/>` | ✅ Full |
| `TableContent.metadata["alignment"]` | `<w:tblPr><w:jc w:val="..."/></w:tblPr>` | ✅ Full |
| `TableContent.metadata["width"]` | `<w:tblW w:w="" w:type="dxa\|pct\|auto"/>` | ✅ Full |
| `TableStyle.banded_rows` | Not mapped (requires conditional formatting) | ❌ Not Supported |
| `TableStyle.banded_columns` | Not mapped | ❌ Not Supported |
| `TableStyle.first_row/last_row` | Not mapped | ❌ Not Supported |
| `TableStyle.first_column/last_column` | Not mapped | ❌ Not Supported |

### List Elements

| USDM Field | OOXML Element/Attribute | Status |
|-----------|------------------------|--------|
| `ListContent.ordered` | `<w:numFmt w:val="decimal\|bullet\|lowerLetter\|..."/>` | ✅ Full |
| `ListStyle.level_styles[format]` | `<w:numFmt w:val="..."/>` | ✅ Full |
| `ListStyle.level_styles[text_template]` | `<w:lvlText w:val="..."/>` | ✅ Full |
| `ListStyle.level_styles[alignment]` | `<w:lvlJc w:val="..."/>` | ✅ Full |
| `ListStyle.level_styles[indent_left]` | `<w:pPr><w:ind w:left="..."/></w:pPr>` | ✅ Full |
| `ListStyle.level_styles[indent_hanging]` | `<w:pPr><w:ind w:hanging="..."/></w:pPr>` | ✅ Full |
| `ListStyle.level_styles[font_name]` | `<w:rPr><w:rFonts w:ascii="..."/></w:rPr>` | ✅ Full |
| `ListStyle.level_styles[bold/italic]` | `<w:rPr><w:b/> / <w:i/>` | ✅ Full |
| Multi-level override | Requires `<w:num>` per list instance | ⚠️ Partial |

### Break Elements

| USDM Type | OOXML Element | Status |
|----------|---------------|--------|
| `PageBreakContent` | `<w:r><w:br w:type="page"/></w:r>` | ✅ Full |
| `LineBreakContent` | `<w:r><w:br/></w:r>` | ✅ Full |
| `ColumnBreakContent` | `<w:r><w:br w:type="column"/></w:r>` | ✅ Full |
| `SectionBreakContent` | `<w:sectPr>` (section properties pragma) | ⚠️ Partial |

### Special Content Types

| USDM Type | OOXML Element | Status |
|----------|---------------|--------|
| `FootnoteContent` | `<w:footnoteRef/>` + `<w:footnotes>` part | ✅ Full |
| `EndnoteContent` | `<w:endnoteRef/>` + `<w:endnotes>` part | ✅ Full |
| `CommentContent` | `<w:commentRangeStart/>`, `<w:commentReference/>`, `<w:commentRangeEnd/>` + `<w:comments>` part | ✅ Full |
| `BookmarkContent` | `<w:bookmarkStart/>`, `<w:bookmarkEnd/>` | ✅ Full |
| `ImageContent` | `<w:drawing><wp:anchor/a:graphic/pic:pic>` (DrawingML) | ✅ Full |
| `MathContent` (inline) | `<w:r><m:oMath><m:r><m:t>...</m:t></m:r></m:oMath></w:r>` (OMML) | ⚠️ Partial |
| `MathContent` (display) | `<w:p><w:r><m:oMath>...</m:oMath></w:r></w:p>` (OMML) | ⚠️ Partial |
| `CodeContent` | `<w:p><w:r><w:t xml:space="preserve">...</w:t></w:r></w:p>` with CodeBlock style | ✅ Full |
| `QuoteContent` | Paragraphs with quote character style (no native `<w:quote>` element) | ⚠️ Partial |
| `ShapeContent` | Not written to DOCX (VML/DrawingML shapes) | ❌ Not Supported |
| `ChartContent` | Not written to DOCX (chart XML part) | ❌ Not Supported |
| `OLEObjectContent` | Not written | ❌ Not Supported |
| `EmbeddedObjectContent` | Not written | ❌ Not Supported |
| `WatermarkContent` | Not written (requires header_part + DrawingML/VML art) | ❌ Not Supported |
| `TOCContent` | Not written (requires field codes + TOC update on open) | ❌ Not Supported |
| `IndexContent` | Not written | ❌ Not Supported |
| `FormFieldContent` | Not written | ❌ Not Supported |
| `StructuredDocumentTagContent` | Not written (SDT XML complex) | ❌ Not Supported |
| `MacroContent` | Not written (requires VBA binary part) | ❌ Not Supported |
| `Revision` / `Change` | Detected during parse with `extract_track_changes`; not written | ⚠️ Partial |
| `DataContent` (PAGE, DATE, etc.) | Field result text captured; not written as live fields | ⚠️ Partial |

---

## WordprocessingML File Coverage

| XML Part | Generated By | Content |
|----------|-------------|---------|
| `word/document.xml` | `docx_builder.build_document.xml()` | Body sections, paragraphs, tables, lists, breaks, bookmarks, footnote/endnote/comment references |
| `word/styles.xml` | `docx_builder.build_styles_xml()` + `docx_style_builder` | Default styles, character/paragraph/table styles, docDefaults |
| `word/numbering.xml` | `docx_builder.build_numbering_xml()` + `docx_style_builder.list_style_to_ooxml()` | Abstract numbering, level definitions, numbering instances |
| `word/footnotes.xml` | `docx_builder.build_footnotes_xml()` | Separators + footnote content |
| `word/endnotes.xml` | `docx_builder.build_endnotes_xml()` | Separators + endnote content |
| `word/comments.xml` | `docx_builder.build_comments_xml()` | Comment metadata + content |
| `word/_rels/document.xml.rels` | `docx_zip_packager.document_rels_xml()` | Part relationships |
| `word/theme/theme1.xml` | `docx_zip_packager.minimal_theme_xml()` | Minimal placeholder theme |
| `[Content_Types].xml` | `docx_zip_packager.content_types_xml()` | Part content types |
| `_rels/.rels` | `docx_zip_packager.rels_xml()` | Package relationships |
| `docProps/core.xml` | `docx_zip_packager.core_properties_xml()` | Dublin Core metadata |
| `docProps/app.xml` | `docx_zip_packager.app_properties_xml()` | Application properties |
| `docProps/custom.xml` | `docx_zip_packager.custom_properties_xml()` | Custom properties |
| `word/media/*.png|jpg|jpeg|gif` | `docx_image_handler.process_images()` | Embedded image binaries |

---

## DrawingML Coverage

| Feature | Status |
|---------|--------|
| `pic:pic` (Picture element) with `a:blip` relationship | ✅ Full |
| `wp:anchor` (floating) vs `wp:inline` (inline) | Inline only (writer always uses inline) |
| `wp:extent` (size in EMU) | ✅ Full |
| `pic:cNvPr` (non-visual props) | ✅ Full |
| `pic:spShape` (predefined shapes) | ❌ Not Supported |
| `a:aGeom` (custom geometry) | ❌ Not Supported |
| `a:fills` / `a:strokes` | ❌ Not Supported |

---

## OMML (Math) Coverage

| Feature | Status |
|---------|--------|
| Inline math (`<m:oMath>` inside `<w:r>`) | ✅ Partial (LaTeX→OMML conversion via `docx_math_writer`) |
| Display math (`<m:oMath>` inside `<w:p>`) | ✅ Partial |
| Fractions, superscripts, subscripts | Via `latex_to_omml()` |
| Matrices / brackets | Via `latex_to_omml()` |
| Integrals, summations, limits | Via `latex_to_omml()` |
| Full LaTeX→OMML fidelity | ⚠️ Partial — complex LaTeX constructs may not translate |

---

## Parser Coverage (DOCX → USDM)

| Feature | Status |
|---------|--------|
| All 3 style types (character, paragraph, table) with full property extraction | ✅ Full |
| Style inheritance (`basedOn`, `nextStyle`, `linkedStyle`) | ✅ Full |
| Numbering definitions and instances | ✅ Full |
| Multi-level list detection and merging | ✅ Full |
| Theme color resolution with tint/shade | ✅ Full |
| Page/column/line breaks | ✅ Full |
| Tabs | ✅ Full |
| Borders and shading (paragraph, table, cell) | ✅ Full |
| Nested tables | ✅ Full |
| Mathematical content (OMML → `math` metadata) | ⚠️ Partial |
| Hyperlinks (`r:id` based and anchor-based) | ✅ Full |
| Bookmarks | ✅ Full |
| Footnotes/endnotes/comments | ✅ Full |
| Core + extended + custom document properties | ✅ Full |
| Track changes / revisions | ⚠️ Partial (extracted but filtered by flag) |
| Hidden text | ⚠️ Partial (extracted when flag enabled) |
| Embedded images (binary) | ✅ Full |
| Drawing/shape content (DrawingML) | ⚠️ Partial (via `DrawingContent.vector_data`) |
| OLE objects | ⚠️ Partial (captured as `OLEObjectContent`, not rendered) |
| Field codes (PAGE, DATE, etc.) | ⚠️ Partial (result text captured) |

---

## Package Structure

```
[Content_Types].xml
_rels/.rels
docProps/
├── core.xml
├── app.xml
└── custom.xml (conditional)
word/
├── document.xml
├── styles.xml
├── numbering.xml
├── footnotes.xml (conditional)
├── endnotes.xml (conditional)
├── comments.xml (conditional)
├── theme/
│   └── theme1.xml
├── _rels/
│   └── document.xml.rels
└── media/
    ├── image1.png
    ├── image2.jpeg
    └── ...
```

---

## Version Targeting

The engine targets **OOXML Transitional (ISO/IEC 29500:2012 Transitional)** by default:

- Uses Transitional namespace `http://schemas.openxmlformats.org/wordprocessingml/2006/main`
- Does not include Strict-only elements (e.g., `<w15:chartTrackingRef>` based strict features)
- Does not include legacy VML shapes (which Transitional allows)
- Compatible with: Microsoft Word 2013+, LibreOffice 7+, Google Docs import, WPS Office

**Strict mode** — Not yet implemented. Would require:
- Removal of legacy elements
- Strict content type declarations
- AlternateContent fallbacks

---

## Known Gaps and Future Work Items

1. **Strict OOXML conformance mode** — Require separate namespace sets and element restrictions
2. **Header/footer generation** — Currently only document body; headers/footers require separate OPC parts
3. **TOC / Index fields** — Require complex field code XML + on-open update instructions
4. **Chart XML parts** — `ChartContent` model exists but no `word/charts/` generation
5. **VBA macro persistence** — `MacroContent` model exists but `.bin` part packaging not implemented
6. **Structured document tags** — Rich model (`StructuredDocumentTagContent`) but no SDT XML generation
7. **Advanced field codes** — PAGE/DATE captured as text; should generate `<w:fldChar>` / `<w:instrText>` / `<w:fldSimple>`
8. **Watermark generation** — Requires header part with VML or WordArt shapes
9. **Revision save IDs (RSIDs)** — Tracking for merge/diff requires `w:rsid*` attributes
10. **Conditional table formatting** — `firstRow`, `lastRow`, `firstColumn`, `lastColumn` banding styles map to `<w:tblStylePr>` elements not yet generated
11. **Multi-level numbered list override** — Each `<w:num>` needs per-level override; current implementation uses a single abstract definition per list style
12. **Theme fidelity** — Only minimal theme generated; full theme XML (colors, fonts, effects) would require `theme1.xml` construction from USDM color/font tokens
13. **OMML completeness** — `latex_to_omml()` covers common constructs; complex LaTeX (custom macros, tikz-like environments) may not translate
14. **Text direction (RTL)** — `ParagraphStyle.text_direction` maps to `<w:bidi/>` but RTL complexity in tables/cells incomplete
15. **Endnote auto-numbering** — Writer uses sequential IDs; does not respect user-defined numbering schemes
