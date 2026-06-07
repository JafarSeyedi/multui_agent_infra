# PSDM Technical Documentation

## Architecture Overview

The Presentation Structured Document Model (PSDM) is a comprehensive presentation document model. It provides:

1. **PSDMDocument Model** - Top-level presentation document (ISO/IEC 29500 PPTX standard compliance)
2. **PPTX Parser** - Reads .pptx files into PSDMDocument
3. **PPTX Writer** - Writes PSDMDocument to .pptx ZIP archives
4. **HTML Writers** - Converts PSDMDocument to various HTML presentation frameworks
5. **USDMSourceLayer** - Source-layer wrapper for PSDMDocument (READ operation)
6. **USDMTransformationLayer** - Transformation wrapper for PSDMDocument (WRITE operation)

## Core Model Classes

### PSDMDocument
```python
class PSDMDocument(BaseDocument):
    slides: list[Slide]
    slide_masters: dict[str, SlideMaster]
    handout_master: HandoutMaster | None
    notes_master: NotesMaster | None
    presentation_properties: PresentationProperties
    stylesheet: StyleSheet
    theme: Theme | None
    custom_shows: CustomShowCollection
    sections: list[PresentationSection]
```

### Slide
```python
class Slide:
    slide_id: str
    layout: SlideLayout | None
    background_color: str | None
    background_image: ImageContent | None
    elements: list[LogicalElement]
    transition: PresentationTransition
    animations: list[Animation]
    notes: NotesSlide | None
    comments: list[SlideComment]
    media_references: list[MediaReference]
    show_header: bool | None
    show_footer: bool | None
    show_date: bool | None
    show_slide_number: bool | None
```

### PresentationProperties
```python
class PresentationProperties:
    slide_width: float | None
    slide_height: float | None
    auto_advance: bool
    show_type: ShowType
    loop: bool
    paper_size: str | None
    orientation: str | None
    scale: int | None
    sync_id: str | None
```

## Parser Architecture

### PPTXParser
Located at: engines/document/parsers/psdm_parsers/pptx/parser.py

The PPTXParser is responsible for:
1. Opening and validating the ZIP archive structure
2. Parsing presentation.xml for global settings
3. Parsing slide masters and layouts
4. Parsing each slide with its elements, transitions, and animations
5. Parsing relationships (images, charts, media, OLE objects)
6. Parsing notes and comments
7. Assembling everything into a PSDMDocument

### Key Helper Modules
- shape_parser.py - Parses shape elements from DrawingML
- table_parser.py - Parses table elements into USDM TableContent
- animation_parser.py - Parses animation effects
- media_parser.py - Parses audio/video references and loads binary data
- ole_parser.py - Parses embedded OLE objects
- notes_parser.py - Parses speaker notes
- comments_parser.py - Parses slide comments
- master_parser.py - Parses slide masters and layouts
- theme_parser.py - Parses color schemes and fonts
- relationship_utils.py - Utilities for working with OPC relationships

## Writer Architecture

### PPTXWriter
Located at: engines/document/writers/psdm_writers/pptx/writer.py

The PPTXWriter is responsible for:
1. Creating [Content_Types].xml
2. Creating _rels/.rels
3. Building presentation.xml with all properties
4. Building theme, masters, layouts
5. Building individual slides with shapes, tables, charts, diagrams
6. Handling media, charts, diagrams, OLE objects
7. Creating notes and comments parts
8. Assembling the final ZIP archive

### HTML Writers (Presentation Frameworks)
Multiple HTML writers convert PSDMDocument to presentation-ready HTML:

| Writer | Framework | Location |
|--------|-----------|----------|
| RevealJSWriter | reveal.js | psdm_writers/revealjs/writer.py |
| StagecraftWriter | Stagecraft (custom) | psdm_writers/stagecraft/writer.py |
| ImpressJSWriter | impress.js | psdm_writers/impressjs/writer.py |
| ShowerWriter | Shower | psdm_writers/shower/writer.py |
| HeedJSWriter | HeedJS | psdm_writers/heedjs/writer.py |
| DeckJSWriter | deck.js | psdm_writers/deckjs/writer.py |

## Data Flow

PPTX File -> PPTXParser -> PSDMDocument -> PPTXWriter -> PPTX File
                              |
                    HTML Writers -> HTML Presentations

## Extension Points

### Adding a New Writer
1. Create a new module under engines/document/writers/psdm_writers/{framework}/
2. Inherit from BaseDocumentWriter
3. Implement: write(), write_stream(), write_to_file(), get_supported_extensions(), get_supported_media_types()
4. Export in __init__.py

### Adding a New Parser
1. Create a new module under engines/document/parsers/psdm_parsers/{format}/
2. Inherit from BaseDocumentParser
3. Implement: parse(), parse_bytes(), supported_extensions
4. Export in __init__.py

## Testing

### Test Suite Structure
- tests/document/test_psdm_models.py - Model validation tests
- tests/document/test_psdm_pptx_writer.py - PPTX writer tests
- tests/document/test_psdm_writers.py - HTML writer tests
- tests/document/test_psdm_parser.py - PPTX parser tests

### Running Tests
pytest tests/document/test_psdm_*.py -v

### Test Coverage
- Model instantiation and validation
- Parser output validation
- Writer binary output validation
- All presentation writer framework outputs

## Known Limitations

1. Parser: Chart and diagram binary data resolution depends on DrawingML helpers
2. Writer: Chart XML generation uses simplified output
3. Round-trip: Full round-trip fidelity requires additional binary handling
4. Animations: Complex animation sequences are simplified
