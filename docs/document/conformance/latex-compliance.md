# LaTeX Compliance Report — USDM LaTeX Engine

## Executive Summary

The USDM LaTeX writer produces LaTeX2e documents using standard packages. The parser uses regex-based tokenization and environment detection to convert `.tex` files into the USDM intermediate model.

**Overall Compliance Level: ~55%** — The writer covers sectioning commands, standard environments (document, lists, figures, tables, math), font selection, cross-referencing, graphics, and code listings. The parser handles section commands, math environments, lists, tables, images, code, quotes, and paragraphs. Advanced packages, bibliography, custom commands, and complex document classes have limited support.

---

## LaTeX Command/Environment Coverage

### Sectioning Commands

| Command | USDM Equivalent | Writer | Parser | Status |
|---------|----------------|--------|--------|--------|
| `\part{}` | `HeadingContent(level=1)` | ✅ Full | ✅ Full | ✅ Full |
| `\chapter{}` | `HeadingContent(level=1)` | ✅ Full | ✅ Full | ✅ Full |
| `\section{}` | `HeadingContent(level=2)` | ✅ Full | ✅ Full | ✅ Full |
| `\subsection{}` | `HeadingContent(level=3)` | ✅ Full | ✅ Full | ✅ Full |
| `\subsubsection{}` | `HeadingContent(level=4)` | ✅ Full | ✅ Full | ✅ Full |
| `\paragraph{}` | `HeadingContent(level=5)` | ✅ Full | ✅ Full | ✅ Full |
| `\subparagraph{}` | `HeadingContent(level=6)` | ✅ Full | ✅ Full | ✅ Full |
| `\section*{}` | `HeadingContent(level=2)` (unnumbered) | ✅ Full | N/A | ⚠️ Partial |
| `\chapter*{}` | Not generated | N/A | N/A | ❌ Not Supported |

### Document Classes

| Class | Writer Default | Configurable | Status |
|-------|---------------|-------------|--------|
| `article` | Default (`\documentclass{article}`) | No | ⚠️ Partial |
| `report` | Not generated | No | ❌ Not Supported |
| `book` | Not generated | No | ❌ Not Supported |
| `letter` | Not generated | No | ❌ Not Supported |
| `memoir` | Not generated | No | ❌ Not Supported |

### Standard Environments

| Environment | USDM Type | Writer | Parser | Status |
|------------|-----------|--------|--------|--------|
| `document` | Document wrapper | ✅ Full | ✅ Full | ✅ Full |
| `itemize` | `ListContent(ordered=False)` | ✅ Full | ✅ Full | ✅ Full |
| `enumerate` | `ListContent(ordered=True)` | ✅ Full | ✅ Full | ✅ Full |
| `description` | `ListContent` (with labels) | ✅ Full | ✅ Full | ✅ Full |
| `figure` | `ImageContent` wrapper | ✅ Full | ❌ Not Supported | ⚠️ Partial |
| `table` | `TableContent` wrapper | ✅ Full | ❌ Not Supported | ⚠️ Partial |
| `equation` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `equation*` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `align` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `align*` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `gather` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `gather*` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `multline` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `multline*` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |
| `split` | Not generated | N/A | N/A | ❌ Not Supported |
| `array` | Not generated | N/A | N/A | ❌ Not Supported |
| `matrix` | Not generated | N/A | N/A | ❌ Not Supported |
| `pmatrix` | Not generated | N/A | N/A | ❌ Not Supported |
| `bmatrix` | Not generated | N/A | N/A | ❌ Not Supported |
| `vmatrix` | Not generated | N/A | N/A | ❌ Not Supported |
| `Vmatrix` | Not generated | N/A | N/A | ❌ Not Supported |
| `cases` | Not generated | N/A | N/A | ❌ Not Supported |
| `verbatim` | `CodeContent` | ✅ Full | ✅ Full | ✅ Full |
| `lstlisting` | `CodeContent(language=...)` | ✅ Full | ✅ Full | ✅ Full |
| `minted` | Not generated | N/A | ✅ Full | ⚠️ Partial |
| `quote` | `QuoteContent` | ✅ Full | ✅ Full | ✅ Full |
| `quotation` | `QuoteContent` | ✅ Full | ✅ Full | ✅ Full |
| `center` | Not generated | N/A | N/A | ❌ Not Supported |
| `flushleft` | Not generated | N/A | N/A | ❌ Not Supported |
| `flushright` | Not generated | N/A | N/A | ❌ Not Supported |
| `tabular` | `TableContent` | ✅ Full | ✅ Full | ✅ Full |
| `longtable` | Not generated | N/A | N/A | ❌ Not Supported |
| `tabulary` | Not generated | N/A | N/A | ❌ Not Supported |
| `tabularx` | Not generated | N/A | N/A | ❌ Not Supported |
| `math` | `MathContent(display=False)` | ✅ Full | ✅ Full | ✅ Full |
| `displaymath` | `MathContent(display=True)` | ✅ Full | ✅ Full | ✅ Full |

### Cross-Referencing

| Command | USDM Type | Writer | Parser | Status |
|---------|-----------|--------|--------|--------|
| `\label{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\ref{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\pageref{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\cite{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\footnote{}` | `FootnoteContent` | Not generated | N/A | ❌ Not Supported |
| `\href{}{}` | `LinkContent` | ✅ Full | N/A | ⚠️ Partial |
| `\url{}` | `LinkContent` (no text) | ✅ Full | N/A | ⚠️ Partial |

### Graphics

| Command | USDM Type | Writer | Parser | Status |
|---------|-----------|--------|--------|--------|
| `\includegraphics[options]{file}` | `ImageContent` | ✅ Full | ✅ Full | ✅ Full |
| `\graphicspath{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\rotatebox{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\scalebox{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\resizebox{}` | Not generated | N/A | N/A | ❌ Not Supported |

### Font Selection

| Command | USDM Field | Writer | Parser | Status |
|---------|-----------|--------|--------|--------|
| `\rmfamily` | `CharacterStyle.font` | Not generated | N/A | ❌ Not Supported |
| `\sffamily` | `CharacterStyle.font` | Not generated | N/A | ❌ Not Supported |
| `\ttfamily` | `CharacterStyle.font = "monospace"` | ✅ Full | N/A | ⚠️ Partial |
| `\textbf{}` | `RichTextSpan.bold` | ✅ Full | N/A | ⚠️ Partial |
| `\textit{}` | `RichTextSpan.italic` | ✅ Full | N/A | ⚠️ Partial |
| `\textsl{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\textsc{}` | `CharacterStyle.small_caps` | Not generated | N/A | ❌ Not Supported |
| `\textup{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\textnormal{}` | Not generated | N/A | N/A | ❌ Not Supported |
| `\emph{}` | `RichTextSpan.italic` | ✅ Full | N/A | ⚠️ Partial |
| `\underline{}` | `RichTextSpan.underline` | ✅ Full | N/A | ⚠️ Partial |
| `\texttt{}` | `RichTextSpan.code` | ✅ Full | N/A | ⚠️ Partial |
| `\textbackslash{}` | Escaped `\` | ✅ Full | N/A | ⚠️ Partial |

### Page Layout

| Feature | Writer | Parser | Status |
|---------|--------|--------|--------|
| `\documentclass` options | Hardcoded `article` | Not parsed | ❌ Not Supported |
| `\usepackage` | Hardcoded list | Not parsed | ❌ Not Supported |
| `\geometry` settings | Not generated | N/A | ❌ Not Supported |
| `\setlength{\parindent}` | Not generated | N/A | ❌ Not Supported |
| `\setlength{\parskip}` | Not generated | N/A | ❌ Not Supported |
| `\pagestyle` | Not generated | N/A | ❌ Not Supported |
| `\thispagestyle` | Not generated | N/A | ❌ Not Supported |
| `\fancyhdr` | Not generated | N/A | ❌ Not Supported |
| `\titlesec` | Not generated | N/A | ❌ Not Supported |

### Bibliography

| Feature | Writer | Parser | Status |
|---------|--------|--------|--------|
| `\bibliography{}` | Not generated | N/A | ❌ Not Supported |
| `\bibliographystyle{}` | Not generated | N/A | ❌ Not Supported |
| `thebibliography` env | Not generated | N/A | ❌ Not Supported |
| `biblatex` commands | Not generated | N/A | ❌ Not Supported |
| `natbib` commands | Not generated | N/A | ❌ Not Supported |
| `biber`/`bibtex` integration | Not supported | N/A | ❌ Not Supported |

---

## Standard Packages Supported

| Package | Purpose | Writer | Parser | Status |
|---------|---------|--------|--------|--------|
| `inputenc` | UTF-8 input | `\usepackage[utf8]{inputenc}` | N/A | ✅ Full |
| `graphicx` | Image inclusion | `\usepackage{graphicx}` | N/A | ✅ Full |
| `amsmath` | Math environments | `\usepackage{amsmath}` | N/A | ✅ Full |
| `amssymb` | Math symbols | `\usepackage{amssymb}` | N/A | ✅ Full |
| `hyperref` | Hyperlinks | `\usepackage{hyperref}` | N/A | ✅ Full |
| `listings` | Code listings | `\usepackage{listings}` | N/A | ✅ Full |
| `xcolor` | Colors | `\usepackage{xcolor}` | N/A | ✅ Full |
| `booktabs` | Professional tables | `\usepackage{booktabs}` | N/A | ✅ Full |
| `multirow` | Merged table cells | `\usepackage{multirow}` | N/A | ✅ Full |
| `fontenc` | Font encoding | Not included | N/A | ❌ Not Supported |
| `babel` | Language support | Not included | N/A | ❌ Not Supported |
| `geometry` | Page layout | Not included | N/A | ❌ Not Supported |
| `fancyhdr` | Headers/footers | Not included | N/A | ❌ Not Supported |
| `titlesec` | Section formatting | Not included | N/A | ❌ Not Supported |
| `enumitem` | List customization | Not included | N/A | ❌ Not Supported |
| `caption` | Caption formatting | Not included | N/A | ❌ Not Supported |
| `subcaption` | Sub-figures | Not included | N/A | ❌ Not Supported |
| `float` | Float control | Not included | N/A | ❌ Not Supported |
| `wrapfig` | Wrap-around figures | Not included | N/A | ❌ Not Supported |
| `multicol` | Multi-column | Not included | N/A | ❌ Not Supported |
| `longtable` | Multi-page tables | Not included | N/A | ❌ Not Supported |
| `tabularx` | Auto-width tables | Not included | N/A | ❌ Not Supported |
| `natbib` | Bibliography | Not included | N/A | ❌ Not Supported |
| `biblatex` | Bibliography | Not included | N/A | ❌ Not Supported |

---

## Element-by-Element Mapping

### Text and Paragraphs

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `ParagraphContent` | `{text}\n\n` | Blank-line separated text | ✅ Full |
| `HeadingContent(level=1)` | `\chapter{text}` or `\section*{text}` | `\chapter{}` / `\section{}` | ✅ Full |
| `HeadingContent(level=2)` | `\section{text}` | `\section{}` | ✅ Full |
| `HeadingContent(level=3)` | `\subsection{text}` | `\subsection{}` | ✅ Full |
| `HeadingContent(level=4)` | `\subsubsection{text}` | `\subsubsection{}` | ✅ Full |
| `HeadingContent(level=5)` | `\paragraph{text}` | `\paragraph{}` | ✅ Full |
| `HeadingContent(level=6)` | `\subparagraph{text}` | `\subparagraph{}` | ✅ Full |

### Rich Text Spans

| USDM Field | LaTeX Output | Parser Input | Status |
|------------|-------------|-------------|--------|
| `RichTextSpan.bold` | `\textbf{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.italic` | `\textit{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.underline` | `\underline{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.code` | `\texttt{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.href` | `\href{url}{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.math` (inline) | `$latex$` | `$...$`, `\(...\)` | ✅ Full |
| `RichTextSpan.math` (display) | `\[latex\]` | `\[...\]`, `$$...$$`, `\begin{equation}...` | ✅ Full |
| `RichTextSpan.color` | Not generated | N/A | ❌ Not Supported |
| `RichTextSpan.font` | Not generated | N/A | ❌ Not Supported |
| `RichTextSpan.character_style` (bold) | `\textbf{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.character_style` (italic) | `\textit{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.character_style` (emph) | `\textit{text}` | Not parsed | ⚠️ Partial |
| `RichTextSpan.character_style` (monospace) | `\texttt{text}` | Not parsed | ⚠️ Partial |

### Lists

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `ListContent(ordered=True)` | `\begin{enumerate}\item ...\end{enumerate}` | `\begin{enumerate}` | ✅ Full |
| `ListContent(ordered=False)` | `\begin{itemize}\item ...\end{itemize}` | `\begin{itemize}` | ✅ Full |
| `ListItemContent` with label | `\item[label] text` | `\item[label]` | ✅ Full |
| Nested lists | Flattened (single level) | Flattened | ⚠️ Partial |

### Tables

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `TableContent` | `\begin{table}[htbp]\centering\begin{tabular}{spec}...\end{table}` | `\begin{tabular}` | ✅ Full |
| `TableRow.is_header` | `\toprule` / `\midrule` separator | Not detected | ⚠️ Partial |
| `TableCell.col_span` | Not generated (requires `\multicolumn`) | N/A | ❌ Not Supported |
| `TableCell.row_span` | Not generated (requires `\multirow`) | N/A | ❌ Not Supported |
| `TableCell.is_header` | Not distinguished in output | N/A | ❌ Not Supported |
| `TableContent.caption` | `\caption{text}` | Not parsed | ⚠️ Partial |
| `TableContent.metadata["column_specification"]` | `{lcr...}` tabular spec | Extracted from `\begin{tabular}{...}` | ✅ Full |
| `TableContent.grid` | Not generated | N/A | ❌ Not Supported |

### Images

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `ImageContent` | `\begin{figure}[htbp]\centering\includegraphics[width=Xcm]{file}\caption{alt}\end{figure}` | `\includegraphics[options]{file}` | ✅ Full |
| `ImageContent.width` | `width=Xcm` option | `width=Xcm|in|pt|mm` extracted | ✅ Full |
| `ImageContent.height` | `height=Xcm` option | `height=Xcm|in|pt|mm` extracted | ✅ Full |
| `ImageContent.alt` | `\caption{alt}` | Filename-derived alt | ⚠️ Partial |
| `ImageContent.caption` | `\caption{text}` | Not parsed | ⚠️ Partial |

### Code

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `CodeContent` (with language) | `\begin{lstlisting}[language=X]...\end{lstlisting}` | `\begin{lstlisting}` | ✅ Full |
| `CodeContent` (no language) | `\begin{verbatim}...\end{verbatim}` | `\begin{verbatim}` | ✅ Full |
| `CodeContent` (minted) | Not generated | `\begin{minted}` | ⚠️ Partial |

### Math

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `MathContent(display=True)` | `\[latex\]` | `\[...\]`, `$$...$$`, `\begin{equation}...`, `\begin{align}...`, etc. | ✅ Full |
| `MathContent(display=False)` | `$latex$` | `$...$`, `\(...\)` | ✅ Full |
| `RichTextSpan.math` (display) | `\[latex\]` | Detected in inline context | ✅ Full |
| `RichTextSpan.math` (inline) | `$latex$` | Detected in inline context | ✅ Full |

### Quotes

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `QuoteContent` | `\begin{quote}...\end{quote}` | `\begin{quote}` / `\begin{quotation}` | ✅ Full |

---

## Parser Behavior

The parser uses a line-by-line regex-based approach:

1. **Comment Removal** — Lines with `%` (outside math mode) are stripped
2. **Environment Detection** — `\begin{env}` / `\end{env}` boundaries tracked via `_check_environment_boundaries()`
3. **Section Commands** — Regex patterns for `\part`, `\chapter`, `\section`, etc. via `_process_section_commands()`
4. **Math Extraction** — Multiple regex patterns for `$...$`, `$$...$$`, `\[...\]`, `\begin{equation}...`, etc. via `_extract_math_content()`
5. **List Items** — `\item` commands detected via `_process_list_commands()`
6. **Table Rows** — `&`-separated cells within `tabular` environment via `_process_table_row()`
7. **Images** — `\includegraphics[options]{file}` via `_process_image_commands()`
8. **Paragraph Assembly** — Non-empty, non-command lines accumulated into paragraphs
9. **Verbatim Handling** — Content inside `verbatim`/`lstlisting`/`minted` captured verbatim

---

## Special Content Types

| USDM Type | LaTeX Output | Parser Input | Status |
|-----------|-------------|-------------|--------|
| `FootnoteContent` | Not generated | N/A | ❌ Not Supported |
| `EndnoteContent` | Not generated | N/A | ❌ Not Supported |
| `CommentContent` | Not generated | N/A | ❌ Not Supported |
| `BookmarkContent` | Not generated | N/A | ❌ Not Supported |
| `TOCContent` | Not generated | N/A | ❌ Not Supported |
| `IndexContent` | Not generated | N/A | ❌ Not Supported |
| `PageBreakContent` | Not generated | N/A | ❌ Not Supported |
| `LineBreakContent` | Not generated | N/A | ❌ Not Supported |
| `ColumnBreakContent` | Not generated | N/A | ❌ Not Supported |
| `SectionBreakContent` | Not generated | N/A | ❌ Not Supported |
| `ShapeContent` | Not generated | N/A | ❌ Not Supported |
| `DrawingContent` | Not generated | N/A | ❌ Not Supported |
| `ChartContent` | Not generated | N/A | ❌ Not Supported |
| `CaptionContent` | Not generated | N/A | ❌ Not Supported |
| `HeaderContent` | Not generated | N/A | ❌ Not Supported |
| `FooterContent` | Not generated | N/A | ❌ Not Supported |
| `FormFieldContent` | Not generated | N/A | ❌ Not Supported |
| `WatermarkContent` | Not generated | N/A | ❌ Not Supported |
| `MacroContent` | Not generated | N/A | ❌ Not Supported |
| `OLEObjectContent` | Not generated | N/A | ❌ Not Supported |
| `EmbeddedObjectContent` | Not generated | N/A | ❌ Not Supported |
| `VideoContent` | Not generated | N/A | ❌ Not Supported |
| `AudioContent` | Not generated | N/A | ❌ Not Supported |
| `DataContent` | Not generated | N/A | ❌ Not Supported |
| `SpreadsheetContent` | Not generated | N/A | ❌ Not Supported |
| `SemanticHTMLContent` | Not generated | N/A | ❌ Not Supported |
| `LaTeXCommandContent` | Not generated | N/A | ❌ Not Supported |
| `LaTeXEnvironmentContent` | Not generated | N/A | ❌ Not Supported |

---

## Known Gaps

1. **Document class configurability** — Writer always emits `\documentclass{article}`; no way to specify `report`, `book`, etc.
2. **Package configurability** — Package list is hardcoded; no mechanism to add custom `\usepackage` declarations
3. **Cross-referencing** — `\label`, `\ref`, `\pageref`, `\cite` not generated or parsed
4. **Bibliography** — No BibTeX/biblatex support
5. **Footnotes** — `FootnoteContent` model exists but writer does not generate `\footnote{}`
6. **Headers/footers** — `HeaderContent`/`FooterContent` models exist but writer does not generate `\pagestyle` or header/footer content
7. **Page layout** — No `geometry` package configuration; margins, paper size hardcoded
8. **Color support** — `RichTextSpan.color` not rendered (xcolor package included but not used)
9. **Font family** — `RichTextSpan.font` not rendered
10. **Table cell merging** — `\multicolumn` and `\multirow` not generated
11. **Table caption parsing** — `\caption` inside `table` environment not extracted
12. **Nested lists** — Flattened to single level
13. **Inline formatting parsing** — `\textbf{}`, `\textit{}`, etc. not parsed (text extracted but formatting lost)
14. **Custom commands** — User-defined `\newcommand` / `\renewcommand` not supported
15. **Include/input** — `\include{}` / `\input{}` not supported
16. **Float placement** — Figure/table float specifiers hardcoded to `[htbp]`
17. **Sub-figures** — `subcaption` package not used
18. **Multi-column** — `multicol` package not used
19. **Language support** — `babel` package not included
20. **Font encoding** — `fontenc` package not included (T1 encoding recommended for Western languages)
21. **Index generation** — `IndexContent` model exists but `\makeindex` / `\printindex` not generated
22. **TOC generation** — `TOCContent` model exists but `\tableofcontents` not generated
23. **Verbatim line processing** — Parser captures verbatim lines but does not associate them with the correct code block element
24. **Math environment fidelity** — Display math always output as `\[...\]`; does not preserve original environment type (equation, align, gather, etc.)
25. **Image path** — `\graphicspath` not supported; image paths used as-is
26. **Escape character handling** — Parser's `_escape_latex()` handles common special characters but may not cover all edge cases
27. **Paragraph indentation** — No `\setlength{\parindent}` or `\noindent` control
28. **Line spacing** — No `\linespread` or `setspace` package support
29. **Title page** — `\maketitle` generated but `\author{}` and `\date{}` are empty
30. **Abstract environment** — Not supported
