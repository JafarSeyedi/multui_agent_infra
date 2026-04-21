# File structure:
docx_models.py for intermediate DOCX-specific data structures
docx_extractor.py for extracting content from DOCX XML
docx_style_parser.py for style handling
docx_table_parser.py for table-specific parsing
docx_math_parser.py for mathematical equations
docx_image_extractor.py for image extraction
docx_utils.py for shared utilities
docx_parser.py as the main orchestrator
__init__.py for public exports


## DOCX Parser Pipeline

```
DOCX File (ZIP archive)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACTION LAYER                         │
│                                                             │
│  docx_extractor.py                                          │
│    - Unzips the .docx file                                  │
│    - Reads document.xml, styles.xml, numbering.xml, etc.    │
│    - Parses XML into raw Python dictionaries/lists          │
│    - Coordinates extraction across all XML parts            │
│                                                             │
│  Supporting extractors (called by docx_extractor):          │
│    - docx_image_extractor.py → extracts images from media/  │
│    - docx_math_parser.py → parses OMML (Office Math ML)     │
│    - docx_style_parser.py → parses styles.xml               │
│    - docx_table_parser.py → parses table XML structures     │
│    - docx_utils.py → shared XML utilities, namespaces       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    INTERMEDIATE MODELS                       │
│                                                             │
│  docx_models.py                                             │
│    - DOCXDocument, DOCXParagraph, DOCXTable, etc.           │
│    - These are pure data containers (dataclasses)           │
│    - They represent DOCX-specific concepts                  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONVERSION LAYER                          │
│                                                             │
│  docx_parser.py (main parser class)                         │
│    - Orchestrates the entire flow                           │
│    - Calls docx_extractor to get intermediate DOCXDocument  │
│    - Contains mapping logic to convert:                     │
│        DOCXDocument → USDMDocument                          │
│        DOCXParagraph → ParagraphContent + DocumentElement   │
│        DOCXTable → TableContent                             │
│        DOCXStyle → StyleSheet                               │
│        DOCXMath → MathContent                               │
│        etc.                                                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    USDMDocument (final output)
```

## File Responsibilities:

| File | Layer | Responsibility |
|------|-------|----------------|
| `docx_extractor.py` | Extraction | Unzip, read all XML parts, coordinate sub-extractors, return populated `DOCXDocument` |
| `docx_image_extractor.py` | Extraction | Extract images from `word/media/`, store in `binary_parts` |
| `docx_math_parser.py` | Extraction | Parse OMML XML into `DOCXMath` objects |
| `docx_style_parser.py` | Extraction | Parse `styles.xml` into `DOCXStyle` objects |
| `docx_table_parser.py` | Extraction | Parse table XML (`w:tbl`) into `DOCXTable` objects |
| `docx_utils.py` | Extraction | Shared helpers (namespace maps, XML traversal, unit conversion) |
| `docx_models.py` | Models | **Intermediate** dataclasses - DOCX-specific representation |
| `docx_parser.py` | Conversion | **Main entry point** - Converts `DOCXDocument` → `USDMDocument` |

## Key Clarification:

**The conversion from intermediate models to USDM happens in `docx_parser.py`**, NOT in the extraction files.

`docx_math_parser.py` (which you requested) is purely an **extraction** file. It:
- Takes OMML XML (from `document.xml` or an equation object)
- Returns a `DOCXMath` intermediate object

The later conversion from `DOCXMath` to `USDMDocument`'s `MathContent` happens in `docx_parser.py`.

Does this clarify the architecture? If so, I will generate `docx_math_parser.py` as an extraction file that parses OMML XML and returns `DOCXMath` objects.



# DOCXParser class:

Provides the main public API (parse, parse_bytes, parse_fileobj)

Orchestrates the two-phase parsing:

Phase 1: Uses DOCXExtractor to get DOCXDocument

Phase 2: Converts DOCXDocument to USDMDocument

Converts all DOCX elements to USDM equivalents:

Paragraphs → ParagraphContent / HeadingContent

Text runs → RichTextSpan objects

Tables → TableContent

Lists → ListContent (with merging of consecutive items)

Styles → StyleSheet

Handles metadata extraction

Manages document structure (sections, pages)

Provides configuration options for track changes, comments, hidden text

The parser returns a fully populated USDMDocument ready for further processing or writing to other formats.