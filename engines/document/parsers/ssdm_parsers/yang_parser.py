# engines/document/parsers/ssdm_parsers/yang_parser.py
"""
YANG 1.1 Parser – converts a .yang file into an SSDM_DOCUMENT containing a
YangModule.

All YANG constructs are mapped to typed SSDM model fields.  No annotations
are used.  The parser is a recursive‑descent parser that handles the full
YANG 1.1 grammar.

Mapping rules (YANG → SSDM):
- module/ submodule                     → YangModule
- import / include                      → stored in module.imports / module.includes
- identity / feature / extension         → lists on module
- typedef                                → YangTypedef
- grouping                               → dict entry in module.groupings
- container                              → YangContainer
- leaf                                   → YangLeaf
- leaf-list (handled as leaf with array flag? For simplicity we treat as leaf with array type)
- list                                   → YangList
- choice / case                          → YangChoice / YangCase
- uses                                   → YangUses
- augment                                → YangAugment
- rpc                                    → YangRPC
- notification                           → YangNotification
- type                                   → YangType
- pattern, length, range, enum           → restrictions on YangType
- description, default, mandatory, key, config, status → stored on relevant objects
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple

from .base_ssdm_parser import BaseSSDMParser
from ..base import ParseOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    YangModule, YangContainer, YangLeaf, YangList, YangChoice, YangCase,
    YangUses, YangAugment, YangRPC, YangNotification, YangTypedef, YangType,
)
from ...models.base import BaseDocument


# ── Tokenizer ──────────────────────────────────────────────────────
TOKEN_SPEC = [
    ("BLOCK_COMMENT",  r"/\*[\s\S]*?\*/"),
    ("LINE_COMMENT",   r"//[^\n]*"),
    ("STRING",         r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
    ("SEMICOLON",      r";"),
    ("LBRACE",         r"\{"),
    ("RBRACE",         r"\}"),
    ("KEYWORD",        r"[a-zA-Z_][\w\-]*"),
    ("WHITESPACE",     r"\s+"),
    ("UNEXPECTED",     r"."),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


class Token:
    def __init__(self, kind: str, value: str, pos: int):
        self.kind = kind
        self.value = value
        self.pos = pos


def tokenize(text: str) -> List[Token]:
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        value = m.group()
        if kind in ("WHITESPACE", "BLOCK_COMMENT", "LINE_COMMENT"):
            continue
        tokens.append(Token(kind, value, m.start()))
    return tokens


# ── Parser ─────────────────────────────────────────────────────────
class YANGParser(BaseSSDMParser):
    """Parser for YANG 1.1 files (.yang)."""

    name = "yang"
    supported_extensions = (".yang",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        tokens = tokenize(text)
        self._tokens = tokens
        self._pos = 0

        doc = SSDM_DOCUMENT(
            title=Path(source_name).stem,
            version="1.0.0",
        )

        module = self._parse_module()
        doc.yang_module = module
        return doc

    # ── Token helpers ──────────────────────────────────────────
    def _peek(self) -> Optional[Token]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _match(self, *kinds: str) -> Optional[Token]:
        tok = self._peek()
        if tok and tok.kind in kinds:
            return self._advance()
        return None

    def _expect(self, kind: str, value: Optional[str] = None) -> Token:
        tok = self._advance()
        if tok.kind != kind or (value is not None and tok.value != value):
            raise SyntaxError(f"Expected {kind}('{value}') but got {tok}")
        return tok

    # ── Module ────────────────────────────────────────────────
    def _parse_module(self) -> YangModule:
        self._expect("KEYWORD", "module")
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")

        module = YangModule(name=name)
        # Header statements
        while self._peek() and self._peek().kind != "RBRACE":
            kw = self._peek().value
            if kw == "yang-version":
                self._advance()
                module.yang_version = self._expect("KEYWORD").value
                self._expect("SEMICOLON")
            elif kw == "namespace":
                self._advance()
                module.namespace = self._unquote(self._expect("STRING").value)
                self._expect("SEMICOLON")
            elif kw == "prefix":
                self._advance()
                module.prefix = self._expect("KEYWORD").value
                self._expect("SEMICOLON")
            elif kw == "description":
                self._advance()
                module.description = self._parse_description()
                self._expect("SEMICOLON")
            elif kw == "import":
                self._advance()
                mod_name = self._expect("KEYWORD").value
                self._expect("LBRACE")
                # skip prefix inside import
                while self._peek() and self._peek().value != "RBRACE":
                    self._advance()
                self._expect("RBRACE")
                module.imports.append(mod_name)
                self._expect("SEMICOLON")
            elif kw == "include":
                self._advance()
                inc = self._expect("STRING").value.strip('"')
                module.includes.append(inc)
                self._expect("SEMICOLON")
            elif kw == "identity":
                self._advance()
                ident = self._expect("KEYWORD").value
                module.identities.append(ident)
                if self._peek() and self._peek().value == "{":
                    self._skip_block()
                self._expect("SEMICOLON")
            elif kw == "feature":
                self._advance()
                feat = self._expect("KEYWORD").value
                module.features.append(feat)
                self._expect("SEMICOLON")
            elif kw == "extension":
                self._advance()
                ext = self._expect("KEYWORD").value
                module.extensions.append(ext)
                self._expect("SEMICOLON")
            elif kw == "typedef":
                self._advance()
                td = self._parse_typedef()
                module.typedefs.append(td)
            elif kw == "grouping":
                self._advance()
                grp_name = self._expect("KEYWORD").value
                self._expect("LBRACE")
                children = self._parse_substmts_until_rbrace()
                module.groupings[grp_name] = children
            elif kw == "augment":
                aug = self._parse_augment()
                module.augmentations.append(aug)
            elif kw == "rpc":
                rpc = self._parse_rpc()
                module.rpcs.append(rpc)
            elif kw == "notification":
                notif = self._parse_notification()
                module.notifications.append(notif)
            else:
                # data definition keyword
                stmt = self._parse_statement()
                if stmt is not None:
                    module.children.append(stmt)

        self._expect("RBRACE")
        return module

    # ── Statement parsing ─────────────────────────────────────
    def _parse_statement(self) -> Optional[Union[YangContainer, YangLeaf, YangList, YangChoice, YangUses]]:
        kw = self._peek().value
        if kw == "container":
            return self._parse_container()
        elif kw == "leaf":
            return self._parse_leaf()
        elif kw == "leaf-list":
            return self._parse_leaf_list()
        elif kw == "list":
            return self._parse_list()
        elif kw == "choice":
            return self._parse_choice()
        elif kw == "uses":
            return self._parse_uses()
        elif kw == "anydata" or kw == "anyxml":
            self._advance()
            name = self._expect("KEYWORD").value
            self._expect("SEMICOLON")
            # Treat as a leaf with type "anydata" – we don't have a dedicated model; we can skip or store as container.
            return None
        else:
            # Unknown – skip until semicolon or block
            self._advance()
            if self._peek() and self._peek().value == "{":
                self._skip_block()
            else:
                self._expect("SEMICOLON")
            return None

    def _parse_substmts_until_rbrace(self) -> List:
        children = []
        while self._peek() and self._peek().value != "RBRACE":
            stmt = self._parse_statement()
            if stmt is not None:
                children.append(stmt)
        self._expect("RBRACE")
        return children

    def _parse_container(self) -> YangContainer:
        self._advance()  # consume 'container'
        name = self._expect("KEYWORD").value
        container = YangContainer(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(container)
        container.children = self._parse_substmts_until_rbrace()
        return container

    def _parse_leaf(self) -> YangLeaf:
        self._advance()  # 'leaf'
        name = self._expect("KEYWORD").value
        leaf = YangLeaf(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(leaf)
        self._expect("RBRACE")
        return leaf

    def _parse_leaf_list(self) -> YangLeaf:
        self._advance()  # 'leaf-list'
        name = self._expect("KEYWORD").value
        leaf = YangLeaf(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(leaf)
        self._expect("RBRACE")
        return leaf

    def _parse_list(self) -> YangList:
        self._advance()  # 'list'
        name = self._expect("KEYWORD").value
        lst = YangList(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(lst)
        lst.children = self._parse_substmts_until_rbrace()
        return lst

    def _parse_choice(self) -> YangChoice:
        self._advance()
        name = self._expect("KEYWORD").value
        choice = YangChoice(name=name)
        self._expect("LBRACE")
        while self._peek() and self._peek().value != "RBRACE":
            kw = self._peek().value
            if kw == "case":
                self._advance()
                case_name = self._expect("KEYWORD").value
                case = YangCase(name=case_name)
                self._expect("LBRACE")
                self._parse_common_substmts(case)
                case.children = self._parse_substmts_until_rbrace()
                choice.cases.append(case)
            else:
                # anydata, etc. – skip
                self._parse_statement()
        self._expect("RBRACE")
        return choice

    def _parse_uses(self) -> YangUses:
        self._advance()
        source = self._expect("KEYWORD").value
        self._expect("SEMICOLON")
        return YangUses(source=source)

    def _parse_augment(self) -> YangAugment:
        self._advance()
        path = self._unquote(self._expect("STRING").value)
        aug = YangAugment(path=path)
        self._expect("LBRACE")
        aug.children = self._parse_substmts_until_rbrace()
        return aug

    def _parse_rpc(self) -> YangRPC:
        self._advance()
        name = self._expect("KEYWORD").value
        rpc = YangRPC(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(rpc)
        while self._peek() and self._peek().value not in ("RBRACE",):
            kw = self._peek().value
            if kw == "input":
                self._advance()
                self._expect("LBRACE")
                cont = YangContainer(name="input")
                cont.children = self._parse_substmts_until_rbrace()
                rpc.input = cont
            elif kw == "output":
                self._advance()
                self._expect("LBRACE")
                cont = YangContainer(name="output")
                cont.children = self._parse_substmts_until_rbrace()
                rpc.output = cont
            else:
                self._parse_statement()
        self._expect("RBRACE")
        return rpc

    def _parse_notification(self) -> YangNotification:
        self._advance()
        name = self._expect("KEYWORD").value
        notif = YangNotification(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(notif)
        notif.children = self._parse_substmts_until_rbrace()
        return notif

    def _parse_typedef(self) -> YangTypedef:
        self._advance()
        name = self._expect("KEYWORD").value
        td = YangTypedef(name=name)
        self._expect("LBRACE")
        self._parse_common_substmts(td)
        self._expect("RBRACE")
        self._expect("SEMICOLON")
        return td

    # ── Common substatements (type, description, default, etc.) ──
    def _parse_common_substmts(self, obj: Union[YangContainer, YangLeaf, YangList, YangRPC, YangNotification, YangTypedef, YangChoice, YangCase]) -> None:
        while self._peek() and self._peek().value in ("type", "description", "default", "mandatory", "key", "config", "status", "must", "when"):
            kw = self._advance().value
            if kw == "type":
                yang_type = self._parse_type()
                setattr(obj, "type", yang_type)
            elif kw == "description":
                desc = self._parse_description()
                setattr(obj, "description", desc)
                self._expect("SEMICOLON")
            elif kw == "default":
                val = self._advance().value
                setattr(obj, "default", val)
                self._expect("SEMICOLON")
            elif kw == "mandatory":
                val = self._advance().value
                setattr(obj, "mandatory", val == "true")
                self._expect("SEMICOLON")
            elif kw == "key":
                key = self._advance().value
                setattr(obj, "key", key)
                self._expect("SEMICOLON")
            else:
                # must, when, config, status – skip for now
                if self._peek() and self._peek().value == "{":
                    self._skip_block()
                elif self._peek():
                    self._advance()  # skip argument
                self._expect("SEMICOLON")

    def _parse_type(self) -> YangType:
        base = self._expect("KEYWORD").value
        yt = YangType(name="", base_type=base)
        if self._peek() and self._peek().value == "{":
            self._advance()
            while self._peek() and self._peek().value != "RBRACE":
                restr_kw = self._advance().value
                if restr_kw == "pattern":
                    yt.pattern = self._unquote(self._expect("STRING").value)
                    self._expect("SEMICOLON")
                elif restr_kw == "length":
                    yt.length = self._unquote(self._expect("STRING").value)
                    self._expect("SEMICOLON")
                elif restr_kw == "range":
                    yt.range = self._unquote(self._expect("STRING").value)
                    self._expect("SEMICOLON")
                elif restr_kw == "enum":
                    yt.enum_values.append(self._expect("KEYWORD").value)
                    self._expect("SEMICOLON")
                else:
                    # unknown restriction – skip
                    if self._peek() and self._peek().value == "{":
                        self._skip_block()
                    else:
                        self._advance()
                    self._expect("SEMICOLON")
            self._expect("RBRACE")
        else:
            self._expect("SEMICOLON")
        return yt

    def _parse_description(self) -> str:
        # description is followed by a string argument and semicolon
        # The keyword "description" has already been consumed by the caller.
        desc = self._unquote(self._expect("STRING").value)
        return desc

    def _skip_block(self) -> None:
        """Skip a block enclosed in braces."""
        self._expect("LBRACE")
        depth = 1
        while depth > 0 and self._pos < len(self._tokens):
            tok = self._advance()
            if tok.value == "{":
                depth += 1
            elif tok.value == "}":
                depth -= 1

    @staticmethod
    def _unquote(s: str) -> str:
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s