# Markdown Compliance Report — USDM Markdown Engine

## Executive Summary

The USDM Markdown writer produces documents conforming to **CommonMark 0.30** with **GitHub-Flavored Markdown (GFM)** extensions. The parser uses the Python `markdown` library with a custom tree processor to convert Markdown into the USDM intermediate model.

**Overall Compliance Level: ~60%** — The writer covers CommonMark leaf blocks (headings, code, paragraphs), container blocks (block quotes, lists), and inline elements (emphasis, links, images). GFM tables are supported. The parser processes headings, paragraphs, lists, code, block quotes, images, and links from the markdown AST. Definition lists, front matter, task lists, and inline formatting are not fully supported.

---

## CommonMark 0.30 Specification Coverage

### Leaf Blocks

| Spec Section | Element | Writer | Parser | Status |
|-------------|---------|--------|--------|--------|
| §4.1 Thematic breaks | `---`, `***`, `___` | Not generated | Not parsed | ❌ Not Supported |
| §4.2 ATX headings | `#` – `######` | `HeadingContent.level` → `#` * N | ✅ Full | ✅ Full |
| §4.2 Closing ATX headings | `Heading ###` | Not generated | N/A | ❌ Not Supported |
| §4.3 Setext headings | `===` / `---` underline | Not generated | N/A | ❌ Not Supported |
| §4.4 Indented code | 4-space / tab indent | Not generated (fenced preferred) | ✅ Full | ⚠️ Partial |
| §4.5 Fenced code | `` ``` `` / `~~~` | `CodeContent` → `` ```{language} `` | ✅ Full | ✅ Full |
| §4.5 Fence info string | ` ```python` | `CodeContent.language` | ✅ Full | ✅ Full |
| §4.6 HTML blocks | Raw HTML | Not generated | Not parsed | ❌ Not Supported |
| §4.7 Link ref definitions | `[id]: url` | Not generated | Not parsed | ❌ Not Supported |
| §4.8 Paragraphs | Plain text | `ParagraphContent` | ✅ Full | ✅ Full |
| §4.9 Blank lines | Between blocks | Emitted | Handled | ✅ Full |

### Container Blocks

| Spec Section | Element | Writer | Parser | Status |
|-------------|---------|--------|--------|--------|
| §5.1 Block quotes | `>` | `QuoteContent` → `> text` | ✅ Full | ✅ Full |
| §5.1 Lazy continuation | `> line1\nline2` | Not generated | N/A | ❌ Not Supported |
| §5.2 Ordered lists | `1. 2. 3.` | `ListContent.ordered=True` | ✅ Full | ✅ Full |
| §5.2 Bullet lists | `- * +` | `ListContent.ordered=False` | ✅ Full | ✅ Full |
| §5.2 List indentation | Multi-level | Single level only | Single level | ⚠️ Partial |
| §5.2 Task lists | `- [ ]` / `- [x]` | Not generated | Not parsed | ❌ Not Supported |

### Inlines

| Spec Section | Element | Writer | Parser | Status |
|-------------|---------|--------|--------|--------|
| §6.1 Code spans | `` `code` `` | `RichTextSpan.code` → `` `code` `` | Plain text only | ⚠️ Partial |
| §6.2 Emphasis | `*text*` / `_text_` | Style `"italic"` → `*text*` | Pulled from `_extract_text` | ⚠️ Partial |
| §6.2 Strong | `**text**` | Style `"bold"` → `**text**` | Pulled from `_extract_text` | ⚠️ Partial |
| §6.3 Links | `[text](url)` | `LinkContent` → `[text](url)` | Not parsed as inline | ⚠️ Partial |
| §6.3 Reference links | `[text][id]` | Not generated | Not parsed | ❌ Not Supported |
| §6.4 Images | `![alt](src)` | `ImageContent` → `![alt](src)` | ✅ Full | ⚠️ Partial |
| §6.5 Autolinks | `<url>` | Not generated | Not parsed | ❌ Not Supported |
| §6.6 Raw HTML | Inline HTML | Not generated | Not parsed | ❌ Not Supported |
| §6.7 Hard line breaks | `  \n` or `\\n` | Not generated | Not parsed | ❌ Not Supported |
| §6.9 Textual content | Plain text | `RichTextSpan.text` | Extracted from leaves | ✅ Full |

---

## GFM Extensions Coverage

| Extension | Feature | Writer | Parser | Status |
|-----------|---------|--------|--------|--------|
| Tables | Pipe tables | `TableContent` → `| col |\n|---|\n| data | ✅ Full | ❌ Not Supported |
| Tables | Column alignment (`:---:`) | Not generated | N/A | ❌ Not Supported |
| Strikethrough | `~~text~~` | Mapped to `<u>` (wrong — see gaps) | Not parsed | ❌ Not Supported |
| Autolinks | Bare URLs | Not generated | Not parsed | ❌ Not Supported |
| Task lists | `- [ ]` / `- [x]` | Not generated | Not parsed | ❌ Not Supported |
| Footnotes | `[^1]` | Not generated | Not parsed | ❌ Not Supported |

---

## Extended Markdown

| Feature | Status |
|---------|--------|
| Definition lists | ❌ Not Supported |
| Attributes (`{#id .class}`) | ❌ Not Supported |
| Front matter (YAML) | ❌ Not Supported |
| Abbreviations | ❌ Not Supported |
| Math (`$...$`, `$$...$$`) | Via `RichTextSpan.math` → `$$...$$` | ⚠️ Partial |
| Citations | ❌ Not Supported |

---

## Element Mapping Tables

### Block Elements

| USDM Type | Markdown Output | Parser Input | Status |
|-----------|----------------|-------------|--------|
| `HeadingContent` (1–6) | `#` – `######` | `<h1>`–`<h6>` via AST | ✅ Full |
| `HeadingContent` (>6) | `######` (clamped) | N/A | ⚠️ Partial |
| `ParagraphContent` | Plain text line | `<p>` via AST | ✅ Full |
| `CodeContent` | `` ```{lang}\ncode\n``` `` or `~~~` | `<pre><code>` or indented | ✅ Full |
| `QuoteContent` | `> quoted text` | `<blockquote>` via AST | ✅ Full |
| `ListContent.ordered` | `1. item` | `<ol><li>` via AST | ✅ Full |
| `ListContent.unordered` | `- item` | `<ul><li>` via AST | ✅ Full |
| `TableContent` | Pipe table | Not parsed | ⚠️ Partial |
| `ImageContent` | `![alt](src)` | `<img>` via AST | ⚠️ Partial |
| `LinkContent` | `[text](url)` | `<a>` via AST | ⚠️ Partial |
| `PageBreakContent` | Not generated | N/A | ❌ Not Supported |
| `LineBreakContent` | Not generated | N/A | ❌ Not Supported |
| `SectionBreakContent` | Not generated | N/A | ❌ Not Supported |
| `FootnoteContent` | Not generated | N/A | ❌ Not Supported |
| `EndnoteContent` | Not generated | N/A | ❌ Not Supported |
| `CommentContent` | Not generated | N/A | ❌ Not Supported |
| `BookmarkContent` | Not generated | N/A | ❌ Not Supported |
| `TOCContent` | Not generated | N/A | ❌ Not Supported |

### Inline Formatting

| USDM Field | Markdown Output | Notes | Status |
|------------|----------------|-------|--------|
| `RichTextSpan.bold` | `**text**` | Via `character_style` containing "bold" | ⚠️ Partial |
| `RichTextSpan.italic` | `*text*` | Via `character_style` containing "italic" | ⚠️ Partial |
| `RichTextSpan.code` | `` `text` `` | Takes precedence over bold/italic | ⚠️ Partial |
| `RichTextSpan.href` | `[text](url)` | Wraps styled text | ⚠️ Partial |
| `RichTextSpan.math` | `$${latex}$$` | Both display and inline use `$$` | ⚠️ Partial |
| `RichTextSpan.underline` | `<u>text</u>` | Raw HTML — not valid CommonMark | ⚠️ Partial |
| `RichTextSpan.strikethrough` | `<u>text</u>` | **Bug**: should be `~~text~~` | ❌ Not Supported |
| `RichTextSpan.color` | Not generated | No native Markdown color syntax | ❌ Not Supported |
| `RichTextSpan.font` | Not generated | No native Markdown font syntax | ❌ Not Supported |
| `RichTextSpan.background` | Not generated | Not supported | ❌ Not Supported |

---

## Parser Behavior

The parser uses a `MarkdownTreeProcessor` (registered at priority 20) that walks the HTML element tree produced by the `markdown` library:

1. **AST Traversal** — `_process_node()` recursively visits all HTML elements
2. **Section Creation** – Headings (`h1`–`h6`) create new `Section` objects with `HeadingContent` titles
3. **Text Extraction** – `_extract_text()` recursively collects text from leaf elements
4. **Block Detection** – Paragraphs, lists, code blocks, block quotes, images, and links are identified by tag name
5. **List Processing** – `ul`/`ol` create `ListContent`; each `li` becomes a `ListItemContent`
6. **No Inline Parsing** – Rich text inline elements (`<strong>`, `<em>`, `<code>`, `<a>`) are flattened to plain text; only character_style metadata is preserved for bold/italic

---

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `WriteOptions.code_block_style` | Fenced code delimiter: `` ``` `` or `~~~` | `` ``` `` |
| `WriteOptions.bullet_style` | Unordered list marker | `-` |
| `WriteOptions.encoding` | Output encoding | `utf-8` |

---

## Known Gaps

1. **Inline formatting loss** — Parser extracts plain text from HTML AST; `<strong>`, `<em>`, `<code>`, `<a>` inline semantics are lost (only text content preserved)
2. **GFM table parsing** — Markdown tables are not parsed; the HTML `<table>` AST is not handled
3. **Strikethrough output bug** — Writer outputs `<u>` instead of `~~text~~` for strikethrough style
4. **Underline not Markdown-native** — Uses raw `<u>` HTML tag, violating CommonMark output conformance
5. **Thematic breaks** — Writer does not generate `---` thematic breaks
6. **Setext headings** — Neither generated nor parsed
7. **Task lists** — Neither generated nor parsed
8. **Autolinks** — Neither generated nor parsed
9. **Reference-style links** — Neither generated nor parsed
10. **Link reference definitions** — Not generated or parsed
11. **HTML blocks** — Raw HTML blocks not generated or parsed
12. **Nested lists** — Flattened to single level in both writer and parser
13. **Loose lists** — Writer always produces tight lists (no blank lines between items)
14. **Multi-paragraph list items** — Parser only captures first `<p>` in `<li>`
15. **Definition lists** — Not supported
16. **Attributes** —pandoc-style `{#id .class}` not supported
17. **Front matter** — YAML/TOML front matter not parsed or generated
18. **Footnotes** — GFM footnotes not supported
19. **Table caption** — `TableContent.caption` not rendered in Markdown output
20. **Table alignment** — Column alignment (`:---:`, `---:---`, `---:`) not generated
21. **Image dimensions** — `ImageContent.width` / `height` not rendered (not supported in standard Markdown)
22. **Hard line breaks** — Neither generated nor parsed
23. **Color/font output** — No Markdown-native syntax for color or font family; silently dropped
24. **List start number** — Ordered lists always start at 1; custom start numbers not supported
25. **GFM autolinks** — Bare URLs not auto-linked in output or recognized in input
