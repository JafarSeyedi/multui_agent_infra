# PSDM User Guide

## Overview

The Presentation Structured Document Model (PSDM) allows you to read, modify, and write presentation files (PPTX) and generate HTML presentations from multiple frameworks.

## Installation

The PSDM subsystem is included in the multi_agent_infra package. No additional installation is required.

## Quick Start

### Reading a PPTX File

```python
import asyncio
from engines.document.parsers.psdm_parsers.pptx.parser import PPTXParser

async def read_presentation():
    parser = PPTXParser()
    with open("presentation.pptx", "rb") as f:
        data = f.read()
    doc = await parser.parse_bytes(data, "doc-001", "presentation.pptx")
    print(f"Slides: {len(doc.slides)}")
    print(f"Title: {doc.title}")
    return doc

doc = asyncio.run(read_presentation())
```

### Writing a PPTX File

```python
import asyncio
from engines.document.writers.psdm_writers.pptx.writer import PPTXWriter
from engines.document.models.psdm_models import (
    PSDMDocument, Slide, SlideMaster, SlideLayout,
    PresentationProperties, Theme,
)
from engines.document.models.usdm_models import (
    ShapeContent, RichTextContent, LogicalElement,
)
from engines.document.models.base import ElementType

async def create_presentation():
    doc = PSDMDocument(
        title="My Presentation",
        document_id="my-presentation",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    doc.presentation_properties = PresentationProperties(
        slide_width=9144000,
        slide_height=6858000,
    )
    
    # Create a slide
    slide = Slide(slide_id="slide1")
    shape = ShapeContent(
        shape_type="rectangle",
        x=1000000, y=1000000,
        width=5000000, height=3000000,
        text=RichTextContent(spans=[]),
    )
    slide.elements.append(LogicalElement(
        element_id="shape1",
        element_type=ElementType.SHAPE,
        content=shape,
    ))
    doc.slides.append(slide)
    
    # Write to file
    writer = PPTXWriter()
    await writer.write_to_file(doc, "output.pptx")
    
asyncio.run(create_presentation())
```

### Generating HTML Presentations

The PSDM subsystem includes writers for multiple HTML presentation frameworks.

#### Reveal.js

```python
from engines.document.writers.psdm_writers.revealjs.writer import RevealJSWriter

writer = RevealJSWriter()
html_bytes = await writer.write(doc)
with open("presentation.html", "wb") as f:
    f.write(html_bytes)
```

#### Impress.js

```python
from engines.document.writers.psdm_writers.impressjs.writer import ImpressJSWriter

writer = ImpressJSWriter()
html_bytes = await writer.write(doc)
```

#### Custom HTML Presentation (Stagecraft)

```python
from engines.document.writers.psdm_writers.stagecraft.writer import StagecraftWriter

writer = StagecraftWriter()
html_bytes = await writer.write(doc)
```

## Supported Features

### Presentation Properties
- Slide dimensions
- Show type (default, kiosk, speaker)
- Loop settings
- Print settings (paper size, orientation, scale)
- Slide synchronization
- Auto-advance

### Slide Content
- Shapes (geometric, text)
- Images
- Tables
- Charts
- SmartArt/Diagrams
- Media (audio/video)
- OLE objects

### Slide Properties
- Background (color/image)
- Transitions (fade, push, wipe, etc.)
- Animations
- Speaker notes
- Comments
- Hyperlinks

### Presentation Structure
- Slide masters
- Slide layouts
- Sections
- Custom shows
- Handout master
- Notes master

## Model Reference

### PlaceholderType
Standard placeholder types for shapes:
- title, subtitle, body
- picture, chart, table
- media, object
- slideNumber, header, footer, date

### TransitionType
Available transition effects:
- fade, push, wipe
- split, cover, uncover
- zoom, random, none

### AnimationType
Available animation effects:
- appear, fadeIn, flyIn
- zoomIn, spin, grow
- customPath

### ShowType
Presentation show modes:
- default, kiosk, speaker

## Writing Custom Writers

To create a custom presentation writer:

```python
from engines.document.models.psdm_models import PSDMDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions

class MyCustomWriter(BaseDocumentWriter):
    def __init__(self, options=None):
        super().__init__(options or WriteOptions())
    
    async def write(self, document):
        psdm = document
        html = self._generate_html(psdm)
        return html.encode("utf-8")
    
    async def write_stream(self, document):
        yield await self.write(document)
    
    async def write_to_file(self, document, target, options=None):
        data = await self.write(document)
        target.write_bytes(data)
    
    def get_supported_media_types(self):
        return ["text/html"]
    
    def get_supported_extensions(self):
        return [".html"]
    
    def _generate_html(self, psdm):
        # Your HTML generation logic here
        return "<html>...</html>"
```

## Troubleshooting

### Common Issues

1. **ImportError for models**: Ensure you import from the correct module path:
   - `from engines.document.models.psdm_models import ...`
   - `from engines.document.models.usdm_models import ...`

2. **Parser errors with.xdr namespace**: This is handled internally for DrawingML compatibility.

3. **Writer produces invalid PPTX**: Ensure all required fields are set:
   - slide_id for each slide
   - name for slide masters/layouts
   - proper relationship IDs in metadata

## Performance Tips

1. For large presentations, use `write_stream()` for incremental output
2. Cache parsed DrawingML shapes when processing multiple slides
3. Use `preserve_order=True` in ParseOptions for consistent output ordering
