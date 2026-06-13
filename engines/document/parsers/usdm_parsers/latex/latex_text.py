# mypy: disable-error-code="attr-defined"

from __future__ import annotations


def _parse_keyval(s: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in s.split(","):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def _parse_length(s: str) -> float | str:
    try:
        return float(s)
    except ValueError:
        return s


class LatexText:
    """Mixin providing LaTeX text processing methods."""

    def _strip_comments(self, line: str) -> str:
        result: list[str] = []
        i = 0
        while i < len(line):
            if line[i] == '\\' and i + 1 < len(line):
                result.append(line[i:i + 2])
                i += 2
                continue
            if line[i] == '%':
                break
            result.append(line[i])
            i += 1
        return ''.join(result)

    def _process_escape_sequences(self, text: str) -> str:
        replacements = [
            (r'\textbackslash', '\\'),
            (r'\textasciitilde', '~'),
            (r'\textasciicircum', '^'),
            (r'\textbullet', '\u2022'),
            (r'\textendash', '\u2013'),
            (r'\textemdash', '\u2014'),
            (r'\textexclamdown', '\u00a1'),
            (r'\textquestiondown', '\u00bf'),
            (r'\textquotedblleft', '"'),
            (r'\textquotedblright', '"'),
            (r'\textquoteleft', '\u2018'),
            (r'\textquoteright', '\u2019'),
            (r'\textregistered', '\u00ae'),
            (r'\texttrademark', '\u2122'),
            (r'\textcopyright', '\u00a9'),
            (r'\texteuro', '\u20ac'),
            (r'\textsterling', '\u00a3'),
            (r'\textyen', '\u00a5'),
            (r'\textcent', '\u00a2'),
            (r'\textellipsis', '\u2026'),
            (r'\textperiodcentered', '\u00b7'),
            (r'\textcompwordmark', ''),
            (r'\%', '%'),
            (r'\&', '&'),
            (r'\_', '_'),
            (r'\#', '#'),
            (r'\$', '$'),
            (r'\{', '{'),
            (r'\}', '}'),
            (r'\char"', ''),
            (r'\symbol{', ''),
        ]
        result = text
        for seq, repl in replacements:
            result = result.replace(seq, repl)
        for simple in ['~', "'", '"', '`', '^', '=', '.', '|', '<', '>']:
            result = result.replace('\\' + simple, simple)
        result = result.replace('\\,', '')
        result = result.replace('\\;', '')
        result = result.replace('\\:', '')
        result = result.replace('\\!', '')
        result = result.replace('\\ ', ' ')
        result = result.replace('~', ' ')
        result = result.replace('---', '\u2014')
        result = result.replace('--', '\u2013')
        result = result.replace('``', '\u201c')
        result = result.replace("''", '\u201d')
        return result
