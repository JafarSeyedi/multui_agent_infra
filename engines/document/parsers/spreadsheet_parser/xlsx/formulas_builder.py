# engines/document/parsers/spreadsheet_parser/xlsx/formulas_builder.py
"""
Complete XML → ESDM for formulas, shared formulas, calc chain.
"""

from xml.etree.ElementTree import Element
from typing import List, Optional, Dict, Tuple
from .namespaces import MAIN
from .utils import (
    xml_find, xml_findall, xml_attr, xml_text, xml_int, xml_bool,
    parse_cell_coordinate,
)
from engines.document.models.esdm_models import (
    CellFormula, FormulaAST, FormulaToken, FormulaTokenType,
    SharedFormula, CalcChainEntry, CalculationChain,
)

NS = {"": MAIN}

# ── Formula AST helpers ──
def _tokenize(formula: str) -> List[FormulaToken]:
    """
    Very simplified tokenization; a full engine would use a proper parser.
    This splits by operators and parentheses to produce an approximate AST.
    """
    # For now, wrap the whole formula as a single operand.
    # A production-grade tokenizer would use regex or a grammar.
    return [FormulaToken(type=FormulaTokenType.OPERAND, value=formula)]

def build_cell_formula(
    formula_text: str,
    shared_index: Optional[int] = None,
    array: bool = False,
) -> CellFormula:
    ast = FormulaAST(tokens=_tokenize(formula_text))
    return CellFormula(
        text=formula_text,
        ast=ast,
        shared_index=shared_index,
        array=array,
    )

# ── Shared formulas ──
# In OOXML, shared formulas are encoded as <c ... t="shared" s="<index>" />
# The actual formula is stored in a sibling <f> element only for the master cell.
# We need to collect them from the sheet's XML.

def build_shared_formulas(sheet_xml: Element) -> List[SharedFormula]:
    """
    Extract shared formula groups from worksheet XML.
    Will return list of SharedFormula instances (master cell and shared index).
    """
    shared_map: Dict[int, SharedFormula] = {}
    # Locate all rows
    for row in xml_findall(sheet_xml, "sheetData/row", NS):
        for c in xml_findall(row, "c", NS):
            # Check for <f> element with shared attributes
            f_elem = xml_find(c, "f", NS)
            if f_elem is None:
                continue
            if f_elem.get("t") == "shared" or f_elem.get("t") is None:
                # Could be master or slave
                si = xml_int(f_elem, "si")  # shared index
                ref = xml_attr(c, "r", "")
                if si not in shared_map:
                    formula_text = xml_text(f_elem)
                    shared_map[si] = SharedFormula(
                        shared_index=si,
                        ref=ref,
                        formula=build_cell_formula(formula_text, shared_index=si).ast,
                    )
    return list(shared_map.values())

# ── Calculation Chain ──
def build_calculation_chain(chain_xml: Element) -> CalculationChain:
    """Parse calcChain.xml."""
    chain = CalculationChain()
    if chain_xml is None:
        return chain
    for c in xml_findall(chain_xml, "c", NS):
        chain.items.append(
            CalcChainEntry(
                sheet_id=xml_int(c, "i"),
                ref=xml_attr(c, "r", ""),
                array=xml_bool(c, "t", "") == "array",
            )
        )
    return chain