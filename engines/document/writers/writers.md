# HTMLWriter features
## 1) Semantic HTML 5
<article>, <section>, <h1>, <p>, <code>, <table>, <caption>, <img>
بدون تداخل CSS
بدون inline style
تمام خروجی‌ها deterministic

## 2) Minimal Template Engine
بدون وابستگی خارجی، با سینتکس:

```
{{ title }}
{{ content }}
```
اما اگر خواستی می‌توانم نسخه Jinja2 کامل را هم بدهم.

# 3) Component Override System
برای هر نوع عنصر:


```
HTMLWriter(component_overrides={
    ElementType.PARAGRAPH: lambda el: "<p class='x'>" + el.text + "</p>"
})
```
یعنی مثل React components → قابل hook و override.

# 4) Safe HTML Escaping
همهٔ مقادیر → html.escape

هیچ HTML injection ممکن نیست.

# 5) Pre/Post Hooks (در صورت تمایل می‌تونم اضافه کنم)
on_before_render
on_after_render
on_element_render

# 6) Themeable CSS
CSS در یک block مشخص در template است و می‌توان آن را جدا کرد.

# 7) آماده For:
تبدیل به PDF
تبدیل به EPUB
Render در WebView
اتصال به CMS


# ویژگی های latex_writer

1) LaTeX‑Safe Escaping کامل
دیگه هیچ &, %, {, }, _, $, ^, ~ سند رو نمی‌ترکونه.

2) Component System
برای override کردن رندر هر عنصر:

python
LaTeXWriter(component_overrides={
    ElementType.PARAGRAPH: lambda el: "\\textit{" + latex_escape(el.text) + "}"
})
قدرت مشابه React Components ولی برای LaTeX.

3) Template Engine
سینتکس:

text
{{ title }}
{{ content }}
کاملاً بدون وابستگی و سریع.

می‌تونی templateهای اختصاصی بنویسی:

book class
IEEE article
ACM conference
thesis
4) Table Rendering استاندارد
با:

tabular
\hline
deterministic formatting
و قابل ارتقا به longtable، booktabs اگر بخواهی.

5) Image Rendering
با figure و includegraphics

سازگار با pdflatex و xelatex.

6) Formula Rendering
سلطه کامل بر LaTeX math:

text
\[
   E = mc^2
\]

7) خروجی ۱۰۰٪ قابل کامپایل
بدون نیاز به بسته‌های عجیب. فقط پکیج‌های استاندارد.


1) پشتیبانی از minted برای Code Highlighting
کدی مثل:

text
python
def hello():
    print("hi")
به صورت حرفه‌ای با رنگ در PDF رندر می‌شود.

2) Auto‑TOC
به طور خودکار فهرست می‌سازد:

text
\tableofcontents
3) Auto‑Numbering
Figures → Figure 1, Figure 2
Tables → Table 1, Table 2
4) longtable + booktabs
For PDFهای خیلی سنگین و حرفه‌ای.

5) TikZ Support
فقط کافی است بگویی:

«سیدجعفر TikZ رو هم فعال کن»

و من preamble لازم را اضافه می‌کنم.

6) XeLaTeX UTF‑8 Perfect
برای فارسی، عربی، عبری → کاملاً بدون مشکل.

7) Multi‑file LaTeX Project
می‌توانم نسخه‌ای بسازم که در اجرای write:

یک main.tex بسازد
یک chapters/
یک figures/
یک tables/
و کامل همه را include کند
تقریباً مثل ساختار Overleaf حرفه‌ای.

8) Theme System
با انتخاب:

basic
xelatex
book
thesis
9) Component Override
در حد component frameworkهای واقعی.


معماری LaTeXWriter God‑Mode Edition
شخصیت‌سازی Writer:

هر DocumentElement به یک Chunk LaTeX تبدیل می‌شود.
اسناد خروجی از preamble غنی + body ساخته می‌شوند.
همهٔ فرمت‌ها به semantic LaTeX تبدیل می‌شوند:
RichText → macros
Inline Math → $...$
Display Math → $$...$$ یا محیط amsmath
Tables → tabularx / longtable (داخل config قابل انتخاب)
Images → figure + includegraphics
Code → minted (fallback: listings)
Sections → \section, \subsection, …, \paragraph
Quotes → quote / blockquote
Lists → enumerate / itemize
CAD/Binary/Data/Spreadsheet → environmentهای سفارشی
🚀 ویژگی‌های Mode God (فوق پیشرفته)
انتخاب هوشمندانهٔ محیط مناسب برای هر content
مدیریت خودکار escaping
تبدیل RichTextSpan به ترکیب ماکروهای LaTeX (bold, italic, underline, color, strike از طریق ulem)
مدیریت multi‑language (UTF‑8 کامل) و Right‑to‑Left برای زبان‌هایی مثل فارسی
تولید preamble پیش‌فرض + امکان override
قرار دادن پکیج‌های لازم بر اساس عناصر موجود
مدیریت cross‑package conflicts
📦 پکیج‌های استفاده‌شده در Writer
text
geometry
fontspec
xcolor
amsmath
amssymb
graphicx
hyperref
ulem
tabularx
longtable
minted
float
caption
booktabs
Minted نیاز به اجرای LaTeX با -shell-escape دارد




1️⃣ Raw Extraction Layer (Poppler/PyMuPDF/Custom C++)
وظیفه:

خواندن تمام text spans:
position (x, y)
font family + size
color
weight/bold/italic
char/word bbox
استخراج تمام تصاویر
استخراج بردارهای گرافیکی (paths، curves، shapes)
ترتیب اصلی objects در stream
خروجی این لایه:

text
[
  Page {
    width, height,
    objects: [
      TextSpan, ImageObj, VectorObj, PathCmd
    ]
  }
]
2️⃣ Layout Engine (Critical: Reading Order Recovery)
وظیفه:

تشخیص reading order صفحه
حل مشکل ستون‌های متعدد
حل out‑of‑order spans
کلاستر کردن متن‌هایی که باید کنار هم باشند
تبدیل spans به “LineBlocks”
تبدیل lines به “ParagraphCandidates”
Output:

text
PageBlockTree
  Blocks:
    - ParagraphBlocks
    - ImageBlocks
    - TableBlocks (still unrecognized)
    - VectorBlocks
این لایه یکی از سخت‌ترین‌هاست:

text با ترتیب گرافیکی ذخیره می‌شود، نه reading order.

3️⃣ High‑Level Semantic Detection Engine
در این لایه:

Table Detector
List Detector
Heading Classifier
Quote Detector
Code Block Detector
Equation Detector
Paragraph Merger
با استفاده از:

فاصله‌های عمودی/افقی
line alignment
bullet shapes detection
font size clustering
indentation geometry
word/char density analysis
bounding box grouping
heuristics + ML lightweight
Output:

text
LogicalPage {
  elements: [Paragraph, List, Table, Image, Code, Quote, Section, Formula, ...]
}
4️⃣ USDM Mapper
تبدیل:

Paragraph → TextContent
Multi-style Paragraph → RichText
TableBlock → TableContent
ListBlock → ListContent
HeadingBlock → SectionContent
ImageBlock → ImageContent
FormulaBlock → FormulaContent
VectorBlock → DrawingContent
TextBlock JSON/Snippets → DataContent
نتیجه:

text
BaseDocument(
  title=auto_detected_title,
  elements=[...]
)
5️⃣ Ultra-Level PostProcessor
merge بخش‌هایی که split شده‌اند
normalize text
reorder false positives
table cell normalization
rich text reconstruction
detect abstract, header, footer
detect duplicated page numbers




⭐ CSDM – CAD Structured Document Model v1.0
(CAD Structured Document Model)

این استاندارد دقیقاً نقش USDM برای اکسل را دارد،

اما این بار برای دنیای CAD، و مخصوص نیاز تو.

1) فلسفه CSDM
CSDM بر سه اصل استوار است:

1) Object‑Level Fidelity
Everything in DWG/DXF/DCF must be modeled as entity or object.

2) Geometry‑Safe
No geometric data should be corrupted during conversion (especially arcs/ellipses/splines).

3) Hierarchy‑Preserving
Layers, blocks, groups, XRefs, annotations, viewports must all be preserved with actual DWG structure.

2) ساختار اصلی CSDM
ساختار پایه این‌گونه است:

text
CSDMDocument
    ├── header: CSDMHeader
    ├── metadata: dict
    ├── layers: List[CSDMLayer]
    ├── blocks: List[CSDMBlock]
    ├── entities: List[CSDMEntity]        ← Free entities
    ├── views: List[CSDMView]
    ├── materials: List[CSDMMaterial]
    ├── dimension_styles: List[CSDMDimStyle]
    ├── text_styles: List[CSDMTextStyle]
    ├── xrefs: List[CSDMXRef]
3) تعریف اجزای مدل
✔ 3.1 Header
text
CSDMHeader:
    version               # AC1018 ، AC1024 ...
    units                 # meters, millimeters, inches
    extents               # bounding box
    limits                # drawing limits
✔ 3.2 Layers
text
CSDMLayer:
    name
    color
    linetype
    plot_style
    is_frozen
    is_locked
✔ 3.3 Block Definitions
text
CSDMBlock:
    name
    base_point
    entities: List[CSDMEntity]
    attributes: List[CSDMAttributeDefinition]
✔ 3.4 XRef
text
CSDMXRef:
    path
    type         # attach / overlay
    insertion_point
    scale
    rotation
✔ 3.5 Entities (Core Section)
text
CSDMEntity:
    type            # line, arc, circle, lwpolyline, spline, hatch, text, mtext, blockref ...
    layer
    color
    linetype
    geometry: dict  # payload هندسه واقعی
    data: dict      # metadata اختصاصی AutoCAD