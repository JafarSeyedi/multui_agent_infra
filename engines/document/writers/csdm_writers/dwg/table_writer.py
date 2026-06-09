"""
TableWriter for CSDM v2.0 Ultra
Responsible for populating all DWG tables using ODA API.
Tables Covered:
    - LAYER
    - LTYPE
    - STYLE (TextStyle)
    - DIMSTYLE (incl. overrides)
    - MLINESTYLE
    - TABLESTYLE
    - MLEADERSTYLE
    - APPID
    - UCS
    - VIEW
    - VPORT
    - LIGHTLIST
    - BLOCK_RECORD (only non-graphical block records)
"""
from __future__ import annotations
from typing import Any
from .base_context import WriterContext
from ....models.csdm_tables import (
    LayerTable,
    LinetypeEntry,
    LinetypeTable,
    TextStyleEntry,
    TextStyleTable,
    DimStyleEntry,
    DimStyleTable,
    MLineStyleTable,
    TableStyleTable,
    MLeaderStyleTable,
    AppIDEntry,
    AppIDTable,
    UCSTable,
    ViewTable,
    VPortTable,
    LightTable,
)
from ....models.csdm_core import CSDMDocument
class TableWriter:
    """
    Writes all DWG tables from CSDMDocument.
    This runs BEFORE entities, blocks, xdata, reactors, layouts.
    """
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
    def write(self):
        self.ctx.log("Writing DWG tables...")
        tables = self.ctx.csdm_doc.tables
        self._write_layers(tables.layer)
        self._write_linetypes(tables.linetype)
        self._write_text_styles(tables.textstyle)
        self._write_dimstyles(tables.dimstyle)
        self._write_mline_styles(tables.mlinestyle)
        self._write_table_styles(tables.tablestyle)
        self._write_mleader_styles(tables.mleaderstyle)
        self._write_appids(tables.appid)
        self._write_ucs(tables.ucs)
        self._write_view(tables.view)
        self._write_vports(tables.vport)
        self._write_lightlist(tables.light)
        self.ctx.log("DWG tables written.")
    def _write_layers(self, table: LayerTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing LayerTable")
        lt = self.dwg.getTable("LAYER")
        if lt is None:
            return
        for entry in table.entries.values():
            rec = lt.create(entry.name)
            rec.setColor(entry.color)
            rec.setLinetype(entry.linetype)
            rec.setLineweight(entry.lineweight)
            rec.setFrozen(entry.frozen)
            rec.setLocked(entry.locked)
            rec.setPlot(entry.plot)
            # transparency not in LayerEntry
            self.ctx.register(entry.handle.value, rec)
    def _write_linetypes(self, table: LinetypeTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing LinetypeTable")
        lt = self.dwg.getTable("LTYPE")
        if lt is None:
            return
        for entry in table.entries.values():
            rec = lt.create(entry.name)
            # description not used
            rec.setPattern([(s.length, s.shape_index) for s in entry.segments], entry.pattern_length)
            self.ctx.register(entry.handle.value, rec)
    def _write_text_styles(self, table: TextStyleTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing TextStyleTable")
        st = self.dwg.getTable("STYLE")
        if st is None:
            return
        for entry in table.entries.values():
            rec = st.create(entry.name)
            rec.setFont(entry.font, entry.bigfont)
            rec.setWidthFactor(entry.width_factor)
            rec.setObliquing(entry.oblique)
            rec.setTextHeight(entry.height)
            rec.setFlag(entry.flags)
            self.ctx.register(entry.handle.value, rec)
    def _write_dimstyles(self, table: DimStyleTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing DimStyleTable")
        ds = self.dwg.getTable("DIMSTYLE")
        if ds is None:
            return
        for entry in table.entries.values():
            rec = ds.create(entry.name)
            rec.setDimensionScale(entry.scale)
            rec.setTextHeight(entry.text_height)
            rec.setArrowSize(entry.arrow_size)
            rec.setExtLineOffset(entry.ext_line_offset)
            rec.setPrecision(entry.decimal_precision)
            rec.setLinearUnit(entry.linear_unit.value if entry.linear_unit else 0)
            self.ctx.register(entry.handle.value, rec)

    def _write_mline_styles(self, table: MLineStyleTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing MLineStyleTable")
        root_dict = self.dwg.getRootDictionary()
        if root_dict is None:
            return
        ms = root_dict.get("ACAD_MLINESTYLE")
        if ms is None:
            return
        for entry in table.entries.values():
            rec = ms.create(entry.name)
            for element in entry.elements:
                rec.addElement(
                    offset=element.offset,
                    color=element.color,
                    linetype=element.linetype
                )
            self.ctx.register(entry.handle.value, rec)
    def _write_table_styles(self, table: TableStyleTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing TableStyleTable")
        root_dict = self.dwg.getRootDictionary()
        if root_dict is None:
            return
        ts = root_dict.get("ACAD_TABLESTYLE")
        if ts is None:
            return
        for entry in table.entries.values():
            rec = ts.create(entry.name)
            rec.setFlowDirection(entry.flow_direction)
            rec.setHorzCellMargin(entry.horz_cell_margin)
            rec.setVertCellMargin(entry.vert_cell_margin)
            self.ctx.register(entry.handle.value, rec)

    def _write_mleader_styles(self, table: MLeaderStyleTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing MLeaderStyleTable")
        root_dict = self.dwg.getRootDictionary()
        if root_dict is None:
            return
        ml = root_dict.get("ACAD_MLEADERSTYLE")
        if ml is None:
            return
        for entry in table.entries.values():
            rec = ml.create(entry.name)
            rec.setArrowSize(entry.arrow_size)
            rec.setTextStyle(entry.text_style)
            rec.setLeaderType(entry.leader_type)
            rec.setLandingGap(entry.landing_gap)
            self.ctx.register(entry.handle.value, rec)

    def _write_appids(self, table: AppIDTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing AppIdTable")
        ap = self.dwg.getTable("APPID")
        if ap is None:
            return
        for entry in table.entries.values():
            rec = ap.create(entry.name)
            rec.setFlag(entry.flags)
            self.ctx.register(entry.handle.value, rec)

    def _write_ucs(self, table: UCSTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing UcsTable")
        ucs = self.dwg.getTable("UCS")
        if ucs is None:
            return
        for entry in table.entries.values():
            rec = ucs.create(entry.name)
            rec.setOrigin(*entry.origin)
            rec.setXAxis(*entry.x_axis)
            rec.setYAxis(*entry.y_axis)
            self.ctx.register(entry.handle.value, rec)

    def _write_view(self, table: ViewTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing ViewTable")
        vw = self.dwg.getTable("VIEW")
        if vw is None:
            return
        for entry in table.entries.values():
            rec = vw.create(entry.name)
            rec.setCenter(*entry.center)
            rec.setWidth(entry.width)
            rec.setHeight(entry.height)
            rec.setDirection(*entry.direction)
            rec.setTarget(*entry.target)
            self.ctx.register(entry.handle.value, rec)

    def _write_vports(self, table: VPortTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing VPortTable")
        vp = self.dwg.getTable("VPORT")
        if vp is None:
            return
        for entry in table.entries.values():
            rec = vp.create(entry.name)
            rec.setCenter(*entry.view_center)
            rec.setHeight(entry.view_height)
            rec.setAspectRatio(entry.aspect if hasattr(entry, "aspect") else 1.0)
            rec.setViewDirection(entry.direction if hasattr(entry, 'direction') else (0, 0, 1))
            rec.setViewTarget(entry.target if hasattr(entry, 'target') else (0, 0, 0))
            # twist not in VPortRecord
            self.ctx.register(entry.handle.value, rec)

    def _write_lightlist(self, table: LightTable | None):
        if table is None or self.dwg is None:
            return
        self.ctx.log("  Writing LightList")
        ll = self.dwg.getTable("LIGHTLIST")
        if ll is None:
            return
        for entry in table.entries.values():
            rec = ll.create(entry.name)
            rec.setType(entry.light_type.value if hasattr(entry, 'light_type') else 0)
            rec.setIntensity(entry.intensity)
            rec.setPosition(*entry.position)
            rec.setTarget(*entry.target)
            rec.setColor(*entry.color)
            self.ctx.register(entry.handle.value, rec)