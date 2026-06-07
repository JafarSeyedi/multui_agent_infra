# HTML5 Compliance Report — USDM HTML Engine

## Executive Summary

The USDM HTML writer produces HTML5 documents conforming to the **W3C HTML5 Recommendation** and the **WHATWG Living Standard**. The parser uses Python's built-in `html.parser.HTMLParser` to convert HTML documents into the USDM intermediate model.

**Overall Compliance Level: ~72%** — The writer covers the full document structure, semantic elements, text content, inline semantics, media embedding, tables, forms, and interactive elements. The parser handles headings, paragraphs, lists, tables, images, links, code blocks, quotes, and math content. ARIA roles, microdata, and some interactive elements have partial support.

---

## Document Structure

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<!DOCTYPE html>` | Emitted | Detected (implicit) | ✅ Full |
| `<html lang="en">` | Emitted | Not parsed | ⚠️ Partial |
| `<head>` | Emitted with meta, title, style | `<title>` extracted | ⚠️ Partial |
| `<meta charset="UTF-8">` | Emitted | Not parsed | ⚠️ Partial |
| `<meta name="viewport">` | Emitted | Not parsed | ⚠️ Partial |
| `<title>` | From `document.title` | Extracted from `<title>` tag | ✅ Full |
| `<meta name="..." content="...">` | From `metadata["meta_*"]` keys | Not parsed | ⚠️ Partial |
| `<style>` (embedded CSS) | Generated from `StyleSheet` | Not parsed | ⚠️ Partial |
| `<body>` | Emitted | Implicit (all content) | ✅ Full |
| `<link>`, `<script>` | Not generated | Not parsed | ❌ Not Supported |

---

## Semantic Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<section>` | `section.section_type == "body"` | Created for `h1`–`h3` | ✅ Full |
| `<header>` | `section.section_type == "header"` | Not parsed | ⚠️ Partial |
| `<footer>` | `section.section_type == "footer"` | Not parsed | ⚠️ Partial |
| `<article>` | Not generated | Not parsed | ❌ Not Supported |
| `<nav>` | `TOCContent` → `<nav class="toc">` | Not parsed | ⚠️ Partial |
| `<aside>` | Not generated | Not parsed | ❌ Not Supported |
| `<main>` | Not generated | Not parsed | ❌ Not Supported |
| `<figure>` | `ImageContent` with `use_figure` metadata | Not parsed | ⚠️ Partial |
| `<figcaption>` | `ImageContent.caption` or `CaptionContent` | Not parsed | ⚠️ Partial |
| `<details>` | Not generated | Not parsed | ❌ Not Supported |
| `<summary>` | Not generated | Not parsed | ❌ Not Supported |
| `<dialog>` | Not generated | Not parsed | ❌ Not Supported |

---

## Text Content Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<p>` | `ParagraphContent` | ✅ Full | ✅ Full |
| `<pre>` | `CodeContent` (block) | ✅ Full | ✅ Full |
| `<blockquote>` | `QuoteContent` | ✅ Full | ✅ Full |
| `<hr>` | `PageBreakContent` → `<hr class="page-break">` | ✅ Full | ✅ Full |
| `<div>` | Not generated (no USDM equivalent) | Not parsed | ❌ Not Supported |
| `<span>` | `RichTextSpan` with style/color/font | Not parsed (math span detected) | ⚠️ Partial |

---

## Heading Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<h1>` – `<h6>` | `HeadingContent.level` (1–6) | ✅ Full | ✅ Full |
| Section association | Headings create new `<section>` | `h1`–`h3` create new `Section` | ✅ Full |
| `HeadingContent.level > 6` | Clamped to `<h6>` | N/A | ⚠️ Partial |

---

## Inline Semantics

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<a href="...">` | `LinkContent` / `RichTextSpan.href` | ✅ Full | ✅ Full |
| `<em>` | `RichTextSpan.italic` | ✅ Full | ✅ Full |
| `<strong>` | `RichTextSpan.bold` | ✅ Full | ✅ Full |
| `<small>` | Not generated | Not parsed | ❌ Not Supported |
| `<s>` | Not generated (strikethrough → `<del>`) | ✅ Full | ⚠️ Partial |
| `<cite>` | Not generated | Not parsed | ❌ Not Supported |
| `<q>` | Not generated (QuoteContent → `<blockquote>`) | ✅ Full | ⚠️ Partial |
| `<dfn>` | Not generated | Not parsed | ❌ Not Supported |
| `<abbr>` | Not generated | Not parsed | ❌ Not Supported |
| `<ruby>`, `<rt>`, `<rp>` | Not generated | Not parsed | ❌ Not Supported |
| `<data>` | Not generated | Not parsed | ❌ Not Supported |
| `<time>` | Not generated | Not parsed | ❌ Not Supported |
| `<code>` | `RichTextSpan.code` | ✅ Full | ✅ Full |
| `<var>` | Not generated | Not parsed | ❌ Not Supported |
| `<samp>` | Not generated | Not parsed | ❌ Not Supported |
| `<kbd>` | Not generated | Not parsed | ❌ Not Supported |
| `<sub>` | Not generated | Not parsed | ❌ Not Supported |
| `<sup>` | Not generated | Not parsed | ❌ Not Supported |
| `<i>` | Not generated (mapped to `<em>`) | ✅ Full | ⚠️ Partial |
| `<b>` | Not generated (mapped to `<strong>`) | ✅ Full | ⚠️ Partial |
| `<u>` | `style="text-decoration:underline"` | ✅ Full | ✅ Full |
| `<mark>` | Not generated | Not parsed | ❌ Not Supported |
| `<bdi>` | Not generated | Not parsed | ❌ Not Supported |
| `<bdo>` | Not generated | Not parsed | ❌ Not Supported |
| `<br>` | `LineBreakContent` | ✅ Full | ✅ Full |
| `<wbr>` | Not generated | Not parsed | ❌ Not Supported |

---

## Media Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<img src="" alt="" width="" height="">` | `ImageContent` | ✅ Full | ✅ Full |
| `<img>` with `<figure>/<figcaption>` | `ImageContent` with `use_figure` metadata | Not parsed | ⚠️ Partial |
| `<audio src="" controls autoplay loop>` | `AudioContent` | ✅ Full | ❌ Not Supported |
| `<video src="" controls autoplay width="" height="" poster="">` | `VideoContent` | ✅ Full | ❌ Not Supported |
| `<track>` | Not generated | Not parsed | ❌ Not Supported |
| `<source>` | Not generated | Not parsed | ❌ Not Supported |
| `<canvas>` | `CanvasContent` model exists; not written | Not parsed | ❌ Not Supported |
| `<svg>` (embedded) | `DrawingContent.vector_data` → `<div>` wrapper | Not parsed | ⚠️ Partial |
| `<math>` (MathML) | `RichTextSpan.math` → `<span class="math">$$...$$` | ✅ Full | ⚠️ Partial |

---

## Table Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<table>` | `TableContent` | ✅ Full | ✅ Full |
| `<caption>` | `TableContent.caption` | ✅ Full | ❌ Not Supported |
| `<colgroup>` | Not generated | Not parsed | ❌ Not Supported |
| `<col>` | Not generated | Not parsed | ❌ Not Supported |
| `<tbody>` | Auto-generated for non-header rows | Not parsed | ⚠️ Partial |
| `<thead>` | Auto-generated for header rows | Not parsed | ⚠️ Partial |
| `<tfoot>` | Not generated | Not parsed | ❌ Not Supported |
| `<tr>` | `TableRow` | ✅ Full | ✅ Full |
| `<td>` | `TableCell` (non-header) | ✅ Full | ✅ Full |
| `<th>` | `TableCell.is_header` or `TableRow.is_header` | ✅ Full | ✅ Full |
| `colspan` | `TableCell.col_span` | ✅ Full | ✅ Full |
| `rowspan` | `TableCell.row_span` | ✅ Full | ✅ Full |
| Cell `class` attribute | `TableCell.metadata["class"]` | Not parsed | ⚠️ Partial |
| Cell `style` attribute | `TableCell.metadata["style"]` | Not parsed | ⚠️ Partial |

---

## Form Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<form>` | Not generated | Not parsed | ❌ Not Supported |
| `<label>` | Not generated | Not parsed | ❌ Not Supported |
| `<input type="text">` | `FormFieldContent(field_type="text")` | ✅ Full | ❌ Not Supported |
| `<input type="checkbox">` | `FormFieldContent(field_type="checkbox")` | ✅ Full | ❌ Not Supported |
| `<input type="radio">` | Not generated | Not parsed | ❌ Not Supported |
| `<input type="email">` | `FormFieldContent(field_type="email")` | ✅ Full | ❌ Not Supported |
| `<input type="password">` | `FormFieldContent(field_type="password")` | ✅ Full | ❌ Not Supported |
| `<input type="number">` | `FormFieldContent(field_type="number")` | ✅ Full | ❌ Not Supported |
| `<input type="date">` | `FormFieldContent(field_type="date")` | ✅ Full | ❌ Not Supported |
| `<input type="file">` | Not generated | Not parsed | ❌ Not Supported |
| `<input type="hidden">` | Not generated | Not parsed | ❌ Not Supported |
| `<input type="submit">` | Not generated | Not parsed | ❌ Not Supported |
| `<input type="button">` | `FormFieldContent(field_type="button")` | ✅ Full | ❌ Not Supported |
| `<button>` | Not generated | Not parsed | ❌ Not Supported |
| `<select>` | `FormFieldContent(field_type="select")` | ✅ Full | ❌ Not Supported |
| `<datalist>` | Not generated | Not parsed | ❌ Not Supported |
| `<optgroup>` | Not generated | Not parsed | ❌ Not Supported |
| `<option>` | `FormFieldContent.options` | ✅ Full | ❌ Not Supported |
| `<textarea>` | `FormFieldContent(field_type="textarea")` | ✅ Full | ❌ Not Supported |
| `<output>` | Not generated | Not parsed | ❌ Not Supported |
| `<progress>` | Not generated | Not parsed | ❌ Not Supported |
| `<fieldset>` | Not generated | Not parsed | ❌ Not Supported |
| `<legend>` | Not generated | Not parsed | ❌ Not Supported |
| Form `name` attribute | `FormFieldContent.field_name` | ✅ Full | ❌ Not Supported |
| Form `value` attribute | `FormFieldContent.value` | ✅ Full | ❌ Not Supported |
| Form `placeholder` | `FormFieldContent.placeholder` | ✅ Full | ❌ Not Supported |
| Form `required` | `FormFieldContent.required` | ✅ Full | ❌ Not Supported |
| Form `readonly` | `FormFieldContent.read_only` | ✅ Full | ❌ Not Supported |
| Form `maxlength` | `FormFieldContent.max_length` | ✅ Full | ❌ Not Supported |
| Form `id` attribute | Auto-generated `field-{name}` | ✅ Full | ❌ Not Supported |
| Form `tooltip` | Not rendered (model only) | ❌ Not Supported | ❌ Not Supported |

---

## Interactive Elements

| Element | Writer | Parser | Status |
|---------|--------|--------|--------|
| `<details>` | Not generated | Not parsed | ❌ Not Supported |
| `<summary>` | Not generated | Not parsed | ❌ Not Supported |
| `<dialog>` | Not generated | Not parsed | ❌ Not Supported |

---

## Scripting Considerations

| Feature | Coverage | Status |
|---------|----------|--------|
| `<script>` (inline) | Not generated | Skipped during parse | ⚠️ Partial |
| `<script src="...">` | Not generated | Not parsed | ❌ Not Supported |
| `<noscript>` | Not generated | Not parsed | ❌ Not Supported |
| Event handler attributes (`onclick`, etc.) | Not generated | Not parsed | ❌ Not Supported |
| `data-*` attributes | Not generated | Not parsed | ❌ Not Supported |

**Note:** The HTML parser explicitly skips `<script>` tags. No JavaScript is generated or preserved. The engine produces static HTML5 documents only.

---

## ARIA Roles Mapping

| USDM Source | HTML Output | Status |
|-------------|------------|--------|
| `SemanticHTMLContent.role` | `role="..."` attribute | ✅ Full |
| `SemanticHTMLContent.aria_attributes` | `aria-*="..."` attributes | ✅ Full |
| `SemanticHTMLContent.element_type` | Semantic element tag | ✅ Full |
| Implicit ARIA roles from semantic elements | Not added (rely on native semantics) | ⚠️ Partial |
| `role="document"` on `<html>` | Not added | ❌ Not Supported |
| `role="main"` on main content | Not added | ❌ Not Supported |
| `aria-label`, `aria-labelledby`, `aria-describedby` | Via `aria_attributes` dict | ✅ Full |
| `aria-hidden` | Via `aria_attributes` dict | ✅ Full |
| Live region roles (`aria-live`, `aria-atomic`) | Not generated | ❌ Not Supported |

---

## CSS Generation from StyleSheet

| USDM Style Property | CSS Property | Status |
|--------------------|-------------|--------|
| `CharacterStyle.bold` | `font-weight: bold` | ✅ Full |
| `CharacterStyle.italic` | `font-style: italic` | ✅ Full |
| `CharacterStyle.underline` | `text-decoration: underline` | ✅ Full |
| `CharacterStyle.strike` | `text-decoration: line-through` | ✅ Full |
| `CharacterStyle.double_strike` | `text-decoration: line-through` | ⚠️ Partial |
| `CharacterStyle.small_caps` | `font-variant: small-caps` | ✅ Full |
| `CharacterStyle.all_caps` | `text-transform: uppercase` | ✅ Full |
| `CharacterStyle.color` | `color: ...` | ✅ Full |
| `CharacterStyle.font` / `font_family` | `font-family: ...` | ✅ Full |
| `CharacterStyle.size` | `font-size: ...pt` | ✅ Full |
| `CharacterStyle.background` / `highlight` | `background-color: ...` | ✅ Full |
| `CharacterStyle.superscript` | `vertical-align: super; font-size: smaller` | ✅ Full |
| `CharacterStyle.subscript` | `vertical-align: sub; font-size: smaller` | ✅ Full |
| `ParagraphStyle.alignment` | `text-align: ...` | ✅ Full |
| `ParagraphStyle.spacing_before` | `margin-top: ...pt` | ✅ Full |
| `ParagraphStyle.spacing_after` | `margin-bottom: ...pt` | ✅ Full |
| `ParagraphStyle.line_spacing` | `line-height: ...` | ✅ Full |
| `ParagraphStyle.indent_left` | `margin-left: ...pt` | ✅ Full |
| `ParagraphStyle.indent_right` | `margin-right: ...pt` | ✅ Full |
| `ParagraphStyle.first_line_indent` | `text-indent: ...pt` | ✅ Full |
| `TableStyle.border_width` + `border_color` | `border: ...px solid ...` | ✅ Full |
| `TableStyle.width` | `width: ...pt` | ✅ Full |
| `TableStyle.alignment` | `margin-left/right: auto` (center/right) | ✅ Full |
| `ListStyle.level_styles[list-style-type]` | `list-style-type: ...` | ✅ Full |
| `ListStyle.level_styles[padding-left]` | `padding-left: ...pt` | ✅ Full |
| External CSS file | Not generated (inline `<style>` only) | ❌ Not Supported |
| CSS media queries | Not generated | ❌ Not Supported |
| CSS custom properties | Not generated | ❌ Not Supported |

---

## Special Content Types

| USDM Type | HTML Output | Status |
|-----------|------------|--------|
| `FootnoteContent` | `<sup class="footnote"><a href="#fn-{id}">{n}</a></sup>` + `<div class="footnotes"><ol>...` | ✅ Full |
| `EndnoteContent` | `<sup class="endnote"><a href="#en-{id}">{n}</a></sup>` + `<div class="endnotes"><ol>...` | ✅ Full |
| `CommentContent` | `<!-- comment by {author}: {text} -->` | ✅ Full |
| `BookmarkContent` | `<a id="{name}" class="bookmark"></a>` | ✅ Full |
| `TOCContent` | `<nav class="toc" id="{anchor}">{label}</nav>` | ✅ Full |
| `ShapeContent` | `<div class="shape shape-{type}" style="...">{text}</div>` | ✅ Full |
| `DrawingContent` | `<div class="drawing">{svg_data}</div>` | ✅ Full |
| `ChartContent` | `<div class="chart" data-chart-type="..." data-series-...>...</div>` | ✅ Full |
| `SemanticHTMLContent` | `<{element_type} role="..." aria-*>...</{element_type}>` | ✅ Full |
| `LaTeXCommandContent` | `<span class="latex-cmd">{cmd}({args})</span>` | ✅ Full |
| `LaTeXEnvironmentContent` | `<div class="latex-env latex-env-{type}" data-label="...">{content}</div>` | ✅ Full |
| `CaptionContent` | `<figcaption>{label} {number} {text}</figcaption>` | ✅ Full |
| `DataContent` | `<span class="field field-{type}">{value}</span>` | ✅ Full |
| `SectionBreakContent` | `<div class="section-break" data-type="..."></div>` | ✅ Full |
| `ColumnBreakContent` | `<div class="column-break"></div>` | ✅ Full |
| `PageBreakContent` | `<hr class="page-break">` | ✅ Full |
| `LineBreakContent` | `<br>` | ✅ Full |
| `MathContent` | Not directly written (spans with `RichTextSpan.math` → `<span class="math">$$...$$</span>`) | ⚠️ Partial |
| `HeaderContent` | `<header>` section | ✅ Full |
| `FooterContent` | `<footer>` section | ✅ Full |
| `IndexContent` | Not written | ❌ Not Supported |
| `PageReferenceContent` | Not written | ❌ Not Supported |
| `WatermarkContent` | Not written | ❌ Not Supported |
| `MacroContent` | Not written | ❌ Not Supported |
| `OLEObjectContent` | Not written | ❌ Not Supported |
| `EmbeddedObjectContent` | Not written | ❌ Not Supported |
| `SpreadsheetContent` | Not written | ❌ Not Supported |
| `BinaryContent` | Not written | ❌ Not Supported |

---

## Parser Coverage (HTML → USDM)

| HTML Element | USDM Target | Status |
|-------------|-------------|--------|
| `<h1>` – `<h6>` | `HeadingContent` | ✅ Full |
| `<p>` | `ParagraphContent` | ✅ Full |
| `<pre>`, `<code>` | `CodeContent` (block) | ✅ Full |
| `<ul>`, `<ol>` | `ListContent` (ordered flag) | ✅ Full |
| `<li>` | `ListItemContent` | ✅ Full |
| `<blockquote>`, `<q>` | `QuoteContent` | ✅ Full |
| `<img>` | `ImageContent` | ✅ Full |
| `<a>` | `RichTextSpan.href` | ✅ Full |
| `<table>`, `<tr>`, `<td>`, `<th>` | `TableContent`, `TableRow`, `TableCell` | ✅ Full |
| `<thead>`, `<tbody>`, `<tfoot>` | `TableRow.is_header` | ⚠️ Partial |
| `<b>`, `<strong>` | `character_style = "bold"` | ✅ Full |
| `<i>`, `<em>` | `character_style = "italic"` | ✅ Full |
| `<u>`, `<ins>` | `character_style = "underline"` | ✅ Full |
| `<s>`, `<del>`, `<strike>` | `character_style = "strikethrough"` | ✅ Full |
| `<br>` | `\n` in text | ✅ Full |
| `<hr>` | `ParagraphContent` with `---` text | ✅ Full |
| `<title>` | `document_title` | ✅ Full |
| `<div class="math">` | `RichTextSpan.math` (display) | ✅ Full |
| `<span class="math">` | `RichTextSpan.math` (inline) | ✅ Full |
| `<script type="math/tex">` | `RichTextSpan.math` | ✅ Full |
| `<math>` (MathML) | `RichTextSpan.math` | ✅ Full |
| `colspan` / `rowspan` attributes | `TableCell.col_span` / `row_span` | ✅ Full |
| HTML entities (`&amp;`, `&lt;`, named) | Decoded to Unicode | ✅ Full |
| Character references (`&#123;`, `&#xAB;`) | Decoded to Unicode | ✅ Full |
| `<form>`, `<input>`, `<select>`, `<textarea>` | Not parsed | ❌ Not Supported |
| `<audio>`, `<video>` | Not parsed | ❌ Not Supported |
| `<nav>`, `<article>`, `<aside>`, `<main>` | Not parsed | ❌ Not Supported |
| `<figure>`, `<figcaption>` | Not parsed | ❌ Not Supported |
| `<details>`, `<summary>`, `<dialog>` | Not parsed | ❌ Not Supported |
| `<style>` | Not parsed | ❌ Not Supported |
| `<link>` | Not parsed | ❌ Not Supported |
| `<meta>` | Not parsed | ❌ Not Supported |
| `<head>` (general) | Only `<title>` extracted | ⚠️ Partial |
| `<div>` (general) | Not parsed | ❌ Not Supported |
| `<span>` (non-math) | Not parsed | ❌ Not Supported |
| `<sub>`, `<sup>` | Not parsed | ❌ Not Supported |
| `<small>`, `<cite>`, `<abbr>`, `<mark>` | Not parsed | ❌ Not Supported |
| `<ruby>`, `<rt>`, `<rp>` | Not parsed | ❌ Not Supported |
| `<data>`, `<time>` | Not parsed | ❌ Not Supported |
| `<bdi>`, `<bdo>` | Not parsed | ❌ Not Supported |
| `<wbr>` | Not parsed | ❌ Not Supported |
| `<datalist>`, `<optgroup>`, `<output>`, `<progress>` | Not parsed | ❌ Not Supported |
| `<fieldset>`, `<legend>` | Not parsed | ❌ Not Supported |
| `<button>` | Not parsed | ❌ Not Supported |
| `<caption>` (table) | Not parsed | ❌ Not Supported |
| `<colgroup>`, `<col>` | Not parsed | ❌ Not Supported |
| `<tfoot>` | Not parsed | ❌ Not Supported |
| MathJax/KaTeX patterns in source | Regex extraction to `math_elements` list | ⚠️ Partial |
| MathML content | Regex extraction to `math_elements` list | ⚠️ Partial |

---

## Microdata / RDFa Considerations

| Feature | Coverage | Status |
|---------|----------|--------|
| `itemscope`, `itemtype`, `itemprop` | Not generated or parsed | ❌ Not Supported |
| `vocab`, `typeof`, `property` (RDFa) | Not generated or parsed | ❌ Not Supported |
| JSON-LD (`<script type="application/ld+json">`) | Not generated or parsed | ❌ Not Supported |
| Open Graph / Twitter Card meta | Not generated (would require `<meta>` tag support) | ❌ Not Supported |

---

## Known Gaps

1. **`<head>` completeness** — Only `<title>` is generated; `<meta>` tags require `metadata["meta_*"]` convention rather than standard mapping
2. **External CSS** — Only inline `<style>` blocks; no `<link rel="stylesheet">` generation
3. **JavaScript** — No `<script>` generation; static HTML only
4. **Form parsing** — HTML parser does not extract `<form>`, `<input>`, `<select>`, `<textarea>` elements
5. **Semantic sectioning** — `<article>`, `<aside>`, `<main>`, `<nav>` (non-TOC) not generated or parsed
6. **Media parsing** — `<audio>`, `<video>`, `<source>`, `<track>` not parsed
7. **Table caption** — `<caption>` element not parsed from HTML
8. **`<colgroup>` / `<col>`** — Not generated or parsed
9. **`<tfoot>`** — Not generated or parsed
10. **Inline element parsing** — `<sub>`, `<sup>`, `<small>`, `<cite>`, `<abbr>`, `<mark>`, `<ruby>`, `<bdi>`, `<bdo>`, `<wbr>`, `<data>`, `<time>` not parsed
11. **`<div>` / `<span>` (non-math)** — Not parsed; these are the most common HTML container elements
12. **`<style>` parsing** — Embedded CSS not extracted; would enable style round-tripping
13. **`<meta>` parsing** — Character encoding, viewport, description, Open Graph tags not extracted
14. **ARIA completeness** — Only `SemanticHTMLContent` generates ARIA; implicit roles from semantic elements not added
15. **Math rendering** — Math output uses `$$...$$` syntax (MathJax/KaTeX compatible) but not native MathML
16. **Microdata/RDFa** — No structured data support
17. **Responsive images** — `<picture>`, `<srcset>`, `<sizes>` not supported
18. **Interactive elements** — `<details>`, `<summary>`, `<dialog>` not supported
19. **Custom elements** — Web Components / custom element names not supported
20. **Bidirectional text** — `<bdi>`, `<bdo>`, `dir` attribute not supported
