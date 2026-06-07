from __future__ import annotations



def latex_to_omml(latex: str) -> str:
    """
    Convert a LaTeX math expression to OMML (Office Math Markup Language).

    Supports fractions, subscripts, superscripts, radicals, integrals,
    sums, products, matrices, delimiters, functions, limits, grouping,
    equation arrays, and phantom elements.

    Args:
        latex: A LaTeX math string (without $ delimiters).

    Returns:
        OMML XML string wrapped in <m:oMath> element.
    """
    latex = latex.strip()
    if not latex:
        return "<m:oMath xmlns:m='http://schemas.openxmlformats.org/officeDocument/2006/math'/>"

    omml_body = _parse_latex_expr(latex)
    return f"<m:oMath>{omml_body}</m:oMath>"


def _parse_latex_expr(expr: str) -> str:
    """Parse a LaTeX expression into OMML XML."""
    expr = expr.strip()

    if not expr:
        return ""

    # Handle display-style environments
    if expr.startswith("\\[") and expr.endswith("\\]"):
        inner = expr[2:-2].strip()
        return _parse_latex_expr(inner)

    if expr.startswith("\\begin{align}") or expr.startswith("\\begin{align*}"):
        return _parse_eqarray(expr)

    if expr.startswith("\\begin{matrix}") or expr.startswith("\\begin{pmatrix}"):
        return _parse_matrix(expr)

    # Handle \left ... \right delimiters
    if expr.startswith("\\left"):
        return _parse_delimited(expr)

    # Handle \frac{num}{den}
    if expr.startswith("\\frac"):
        return _parse_frac(expr)

    # Handle \sqrt[deg]{base} or \sqrt{base}
    if expr.startswith("\\sqrt"):
        return _parse_sqrt(expr)

    # Handle \sum, \int, \prod, \lim with sub/sup
    if any(expr.startswith(cmd) for cmd in ["\\sum", "\\int", "\\prod", "\\bigcup", "\\bigcap", "\\oint"]):
        return _parse_nary(expr)

    if expr.startswith("\\lim"):
        return _parse_limit(expr)

    # Handle \hat, \bar, \vec, \dot, \tilde, \acute, \grave
    accent_map = {
        "\\hat": "0302", "\\bar": "0304", "\\vec": "0307",
        "\\dot": "0307", "\\tilde": "0303", "\\acute": "0301",
        "\\grave": "0300", "\\ddot": "0308", "\\breve": "0306",
        "\\check": "030C",
    }
    for cmd, chr_val in accent_map.items():
        if expr.startswith(cmd):
            return _parse_accent(expr, cmd, chr_val)

    # Handle \mathrm, \mathit, \mathbf, \mathbb, \mathcal, \mathfrak
    text_style_map = {
        "\\mathrm": "normal", "\\mathit": "italic",
        "\\mathbf": "bold", "\\mathbb": "double-struck",
        "\\mathcal": "script", "\\mathfrak": "fraktur",
        "\\mathtt": "monospace", "\\mathsf": "sans-serif",
    }
    for cmd, omml_type in text_style_map.items():
        if expr.startswith(cmd):
            return _parse_text_style(expr, cmd, omml_type)

    # Handle \text{...}
    if expr.startswith("\\text"):
        return _parse_text(expr)

    # Handle \substack{...}
    if expr.startswith("\\substack"):
        return _parse_substack(expr)

    # Handle \phantom{...}
    if expr.startswith("\\phantom"):
        return _parse_phantom(expr)

    # Handle \underbrace{...}_{...} and \overbrace{...}^{...}
    if expr.startswith("\\underbrace") or expr.startswith("\\overbrace"):
        return _parse_group_chr(expr)

    # Handle subscripts and superscripts
    result = _parse_scripts(expr)
    if result:
        return result

    # Handle grouped content { ... }
    if expr.startswith("{") and expr.endswith("}"):
        inner = expr[1:-1].strip()
        return _parse_latex_expr(inner)

    # Plain text / identifier
    return _make_run(expr)


def _parse_frac(expr: str) -> str:
    """Parse \\frac{num}{den} into OMML."""
    num, den, _ = _extract_two_braces(expr, 5)
    num_omml = _parse_latex_expr(num) if num else ""
    den_omml = _parse_latex_expr(den) if den else ""
    return f"<m:f><m:num>{num_omml}</m:num><m:den>{den_omml}</m:den></m:f>"


def _parse_sqrt(expr: str) -> str:
    """Parse \\sqrt[deg]{base} or \\sqrt{base} into OMML."""
    pos = 5
    degree = ""
    base = ""

    if pos < len(expr) and expr[pos] == "[":
        depth = 0
        end = pos
        for i in range(pos, len(expr)):
            if expr[i] == "[":
                depth += 1
            elif expr[i] == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        degree = expr[pos + 1:end]
        pos = end + 1

    if pos < len(expr) and expr[pos] == "{":
        base, _, _ = _extract_braces(expr, pos)

    base_omml = _parse_latex_expr(base) if base else ""
    if degree:
        deg_omml = _parse_latex_expr(degree) if degree else ""
        return f"<m:rad><m:deg>{deg_omml}</m:deg><m:e>{base_omml}</m:e></m:rad>"
    return f"<m:rad><m:deg/><m:e>{base_omml}</m:e></m:rad>"


def _parse_nary(expr: str) -> str:
    """Parse \\sum, \\int, \\prod etc. with optional sub/sup into OMML."""
    cmd_end = expr.find("_")
    if cmd_end == -1:
        cmd_end = expr.find("^")
    if cmd_end == -1:
        cmd_end = len(expr)

    cmd = expr[:cmd_end].strip()
    rest = expr[cmd_end:].strip()

    sub_omml = ""
    sup_omml = ""
    body_omml = ""

    if rest:
        if rest.startswith("_"):
            sub_text, rest_after = _extract_script_arg(rest[1:])
            sub_omml = _parse_latex_expr(sub_text) if sub_text else ""
            rest = rest_after
    if rest.startswith("^"):
        sup_text, rest = _extract_script_arg(rest[1:])
        sup_omml = _parse_latex_expr(sup_text) if sup_text else ""
    if rest:
        body_omml = _parse_latex_expr(rest)

    nary_char = _cmd_to_nary_char(cmd)
    return (
        f"<m:nary>"
        f"<m:naryPr><m:chr m:val='{nary_char}'/><m:limLoc m:val='subSup'/><m:subHide m:val='0'/><m:supHide m:val='0'/></m:naryPr>"
        f"<m:sub>{sub_omml}</m:sub>"
        f"<m:sup>{sup_omml}</m:sup>"
        f"<m:e>{body_omml}</m:e>"
        f"</m:nary>"
    )


def _parse_limit(expr: str) -> str:
    """Parse \\lim_{x \\to a} body into OMML."""
    rest = expr[4:].strip()
    sub_omml = ""
    body_omml = ""

    if rest.startswith("_"):
        sub_text, rest_after = _extract_script_arg(rest[1:])
        sub_omml = _parse_latex_expr(sub_text) if sub_text else ""
        rest = rest_after

    if rest:
        body_omml = _parse_latex_expr(rest)

    return (
        f"<m:func>"
        f"<m:fName><m:limLow><m:e><m:r><m:t>lim</m:t></m:r></m:e><m:lim>{sub_omml}</m:lim></m:limLow></m:fName>"
        f"<m:e>{body_omml}</m:e>"
        f"</m:func>"
    )


def _parse_accent(expr: str, cmd: str, chr_val: str) -> str:
    """Parse \\hat{base} etc. into OMML."""
    base_start = len(cmd)
    if base_start < len(expr) and expr[base_start] == "{":
        base, _, _ = _extract_braces(expr, base_start)
    else:
        base = expr[base_start:]

    base_omml = _parse_latex_expr(base) if base else ""
    return (
        f"<m:acc>"
        f"<m:accPr><m:chr m:val='{chr_val}'/></m:accPr>"
        f"<m:e>{base_omml}</m:e>"
        f"</m:acc>"
    )


def _parse_text_style(expr: str, cmd: str, omml_type: str) -> str:
    """Parse \\mathrm{...} etc. into OMML."""
    text_start = len(cmd)
    if text_start < len(expr) and expr[text_start] == "{":
        text, _, _ = _extract_braces(expr, text_start)
    else:
        text = expr[text_start:]

    return f"<m:r><m:rPr><m:sty m:val='{omml_type}'/></m:rPr><m:t>{_esc_xml(text)}</m:t></m:r>"


def _parse_text(expr: str) -> str:
    """Parse \\text{...} into OMML."""
    text, _, _ = _extract_braces(expr, 5)
    return f"<m:r><m:t>{_esc_xml(text)}</m:t></m:r>"


def _parse_substack(expr: str) -> str:
    """Parse \\substack{...} into OMML equation array."""
    content, _, _ = _extract_braces(expr, 10)
    rows = content.split("\\\\")
    parts: list[str] = ["<m:eqArr>"]
    for row in rows:
        row = row.strip()
        if row:
            parts.append(f"<m:e>{_parse_latex_expr(row)}</m:e>")
    parts.append("</m:eqArr>")
    return "".join(parts)


def _parse_phantom(expr: str) -> str:
    """Parse \\phantom{...} into OMML."""
    content, _, _ = _extract_braces(expr, 9)
    content_omml = _parse_latex_expr(content) if content else ""
    return f"<m:phant><m:phantPr><m:show m:val='0'/></m:phantPr><m:e>{content_omml}</m:e></m:phant>"


def _parse_group_chr(expr: str) -> str:
    """Parse \\underbrace{...}_{label} or \\overbrace{...}^{label}."""
    if expr.startswith("\\underbrace"):
        cmd_len = 12
        chr_val = "23DF"
    else:
        cmd_len = 11
        chr_val = "23DE"

    content, after, _ = _extract_braces(expr, cmd_len)
    content_omml = _parse_latex_expr(content) if content else ""

    if after.strip().startswith("_"):
        label_text, _ = _extract_script_arg(after.strip()[1:])
        _parse_latex_expr(label_text) if label_text else ""
        return (
            f"<m:groupChr>"
            f"<m:groupChrPr><m:chr m:val='{chr_val}'/><m:loc m:val='bot'/></m:groupChrPr>"
            f"<m:e>{content_omml}</m:e>"
            f"</m:groupChr>"
        )
    elif after.strip().startswith("^"):
        label_text, _ = _extract_script_arg(after.strip()[1:])
        _parse_latex_expr(label_text) if label_text else ""
        return (
            f"<m:groupChr>"
            f"<m:groupChrPr><m:chr m:val='{chr_val}'/><m:loc m:val='top'/></m:groupChrPr>"
            f"<m:e>{content_omml}</m:e>"
            f"</m:groupChr>"
        )

    return (
        f"<m:groupChr>"
        f"<m:groupChrPr><m:chr m:val='{chr_val}'/><m:loc m:val='bot'/></m:groupChrPr>"
        f"<m:e>{content_omml}</m:e>"
        f"</m:groupChr>"
    )


def _parse_delimited(expr: str) -> str:
    """Parse \\left ... \\right delimiters into OMML."""
    left_delim, rest = _extract_delim(expr[5:])
    if rest.strip().startswith("\\right"):
        rest = rest.strip()[6:]
        right_delim, body = _extract_delim(rest)
    else:
        right_delim = "."
        body = rest

    body_omml = _parse_latex_expr(body.strip()) if body.strip() else ""
    return (
        f"<m:d>"
        f"<m:dPr>"
        f"<m:begChr m:val='{_map_delim(left_delim)}'/>"
        f"<m:endChr m:val='{_map_delim(right_delim)}'/>"
        f"</m:dPr>"
        f"<m:e>{body_omml}</m:e>"
        f"</m:d>"
    )


def _parse_eqarray(expr: str) -> str:
    """Parse align environment into OMML eqArr."""
    inner = expr
    for prefix in ["\\begin{align}", "\\begin{align*}"]:
        if inner.startswith(prefix):
            inner = inner[len(prefix):]
            break
    for suffix in ["\\end{align}", "\\end{align*}"]:
        if inner.endswith(suffix):
            inner = inner[:-len(suffix)]
            break

    rows = inner.split("\\\\")
    parts: list[str] = ["<m:eqArr>"]
    for row in rows:
        row = row.strip()
        if row:
            parts.append(f"<m:e>{_parse_latex_expr(row)}</m:e>")
    parts.append("</m:eqArr>")
    return "".join(parts)


def _parse_matrix(expr: str) -> str:
    """Parse matrix environment into OMML m."""
    inner = expr
    for prefix in ["\\begin{matrix}", "\\begin{pmatrix}", "\\begin{bmatrix}", "\\begin{vmatrix}", "\\begin{Vmatrix}"]:
        if inner.startswith(prefix):
            inner = inner[len(prefix):]
            break
    for suffix in ["\\end{matrix}", "\\end{pmatrix}", "\\end{bmatrix}", "\\end{vmatrix}", "\\end{Vmatrix}"]:
        if inner.endswith(suffix):
            inner = inner[:-len(suffix)]
            break

    rows = inner.split("\\\\")
    parts: list[str] = ["<m:m>"]
    for row in rows:
        row = row.strip()
        if row:
            cells = row.split("&")
            row_parts: list[str] = ["<m:mr>"]
            for cell in cells:
                cell = cell.strip()
                row_parts.append(f"<m:e>{_parse_latex_expr(cell)}</m:e>")
            row_parts.append("</m:mr>")
            parts.append("".join(row_parts))
    parts.append("</m:m>")
    return "".join(parts)


def _parse_scripts(expr: str) -> str:
    """Parse subscripts and superscripts in an expression."""
    base_end = _find_script_start(expr)
    if base_end == -1:
        return ""

    base = expr[:base_end]
    rest = expr[base_end:]

    sub_omml = ""
    sup_omml = ""

    if rest.startswith("_"):
        sub_text, rest = _extract_script_arg(rest[1:])
        sub_omml = _parse_latex_expr(sub_text) if sub_text else ""
    elif rest.startswith("^"):
        sup_text, rest = _extract_script_arg(rest[1:])
        sup_omml = _parse_latex_expr(sup_text) if sup_text else ""

    if rest:
        rest_omml = _parse_latex_expr(rest)
    else:
        rest_omml = ""

    base_omml = _parse_latex_expr(base) if base else ""

    if sub_omml and sup_omml:
        result = f"<m:sSubSup><m:e>{base_omml}</m:e><m:sub>{sub_omml}</m:sub><m:sup>{sup_omml}</m:sup></m:sSubSup>"
    elif sub_omml:
        result = f"<m:sSub><m:e>{base_omml}</m:e><m:sub>{sub_omml}</m:sub></m:sSub>"
    elif sup_omml:
        result = f"<m:sSup><m:e>{base_omml}</m:e><m:sup>{sup_omml}</m:sup></m:sSup>"
    else:
        return ""

    if rest_omml:
        return f"<m:r><m:t>{result}{rest_omml}</m:t></m:r>"
    return result


def _find_script_start(expr: str) -> int:
    """Find the position where a script (_ or ^) starts, respecting braces."""
    depth = 0
    for i, ch in enumerate(expr):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0 and ch in ("_", "^"):
            return i
    return -1


def _extract_script_arg(s: str) -> tuple[str, str]:
    """Extract a script argument (single char or braced group)."""
    s = s.lstrip()
    if not s:
        return "", ""
    if s[0] == "{":
        content, after, _ = _extract_braces(s, 0)
        return content, after
    return s[0], s[1:]


def _extract_braces(s: str, start: int) -> tuple[str, str, int]:
    """Extract content from matching braces starting at position start."""
    if start >= len(s) or s[start] != "{":
        return "", s, start

    depth = 0
    end = start
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    content = s[start + 1:end]
    after = s[end + 1:]
    return content, after, end


def _extract_two_braces(s: str, start: int) -> tuple[str, str, str]:
    """Extract two consecutive braced groups."""
    first, after1, _ = _extract_braces(s, start)
    after1 = after1.lstrip()
    second, after2, _ = _extract_braces(after1, 0)
    return first, second, after2


def _extract_delim(s: str) -> tuple[str, str]:
    """Extract a delimiter token (single char, dot, or \\langle etc.)."""
    s = s.lstrip()
    if not s:
        return ".", ""
    if s[0] == "\\":
        if s.startswith("\\langle"):
            return "\\langle", s[8:]
        if s.startswith("\\rangle"):
            return "\\rangle", s[8:]
        if s.startswith("\\lfloor"):
            return "\\lfloor", s[8:]
        if s.startswith("\\rceil"):
            return "\\rceil", s[7:]
        if s.startswith("\\lceil"):
            return "\\lceil", s[7:]
        if s.startswith("\\rfloor"):
            return "\\rfloor", s[8:]
        if s.startswith("\\vert"):
            return "|", s[5:]
        if s.startswith("\\Vert"):
            return "\\|", s[5:]
        if s.startswith("\\{"):
            return "{", s[2:]
        if s.startswith("\\}"):
            return "}", s[2:]
        if s.startswith("\\backslash"):
            return "\\", s[10:]
        if s.startswith("\\|"):
            return "\\|", s[2:]
        return s[:2], s[2:]
    return s[0], s[1:]


def _map_delim(d: str) -> str:
    """Map LaTeX delimiter to OOXML delimiter character."""
    delim_map = {
        "(": "(", ")": ")",
        "[": "[", "]": "]",
        "{": "{", "}": "}",
        "\\{": "{", "\\}": "}",
        "|": "|", "\\|": "‖",
        ".": "",
        "\\langle": "⟨", "\\rangle": "⟩",
        "\\lfloor": "⌊", "\\rfloor": "⌋",
        "\\lceil": "⌈", "\\rceil": "⌉",
        "/": "/", "\\backslash": "\\",
    }
    return delim_map.get(d, d)


def _cmd_to_nary_char(cmd: str) -> str:
    """Map LaTeX n-ary command to OOXML character."""
    char_map = {
        "\\sum": "∑", "\\int": "∫", "\\prod": "∏",
        "\\bigcup": "∪", "\\bigcap": "∩", "\\oint": "∮",
        "\\coprod": "∐", "\\bigsqcup": "⊔",
        "\\bigvee": "⋁", "\\bigwedge": "⋀",
        "\\bigodot": "⊙", "\\bigotimes": "⊗",
        "\\bigoplus": "⊕", "\\biguplus": "⊎",
    }
    return char_map.get(cmd, "∑")


def _make_run(text: str) -> str:
    """Create an OMML run element."""
    return f"<m:r><m:t>{_esc_xml(text)}</m:t></m:r>"


def _esc_xml(val: str) -> str:
    """Escape XML special characters."""
    s = str(val)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s
