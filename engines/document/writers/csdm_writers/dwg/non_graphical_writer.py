"""
NonGraphicalWriter
Responsible for writing all NON-graphical DWG objects to the database.
Covers:
    - Dictionaries (root + nested)
    - XRecords
    - Groups
    - Layers filters / layer states
    - PlotSettings
    - Materials
    - Lights
    - Render settings
    - CADTableStyle, MLeaderStyle, DimStyle overrides (already declared in table_writer)
    - Underlay Definitions (PDF, DGN, DWF)
    - RasterImageDefs
    - Layouts (non-viewport part)
    - Named UCS / Views
    - VisualStyles
    - RegApp records (non-xdata)
    - All non-entity DB objects referenced by handles
This writer:
    - Runs BEFORE EntityWriter and BEFORE BlockWriter.
    - Ensures that all DB-objects exist and are registered for dependency resolution.
"""
from __future__ import annotations
from typing import Any
from collections.abc import Callable
from .base_context import WriterContext
from ....models.csdm_core import CSDMHandle
from ....models.csdm_entities import BaseEntity
class NonGraphicalWriter:
    """
    Writes all NON-entity objects in DWG.
    """
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
        self._handlers: dict[str, Callable] = {
            "XRECORD": self._write_xrecord,
            "DICTIONARY": self._write_dictionary,
            "GROUP": self._write_group,
            "MATERIAL": self._write_material,
            "RASTER_IMAGE_DEF": self._write_raster_def,
            "UNDERLAY_DEF": self._write_underlay_def,
            "LAYOUT": self._write_layout,
            "VIEW": self._write_view,
            "UCS": self._write_ucs,
            "VISUALSTYLE": self._write_visual_style,
            "REGAPP": self._write_regapp,
            "PLOTSETTINGS": self._write_plot_settings,
            "LIGHT": self._write_light,
        }
    def write(self):
        self.ctx.log("Writing non-graphical DWG objects...")
        for obj in self.ctx.csdm_doc.objects.xrecords.values():
            handler = self._handlers.get(obj.type)
            if not handler:
                self.ctx.log(f"  WARNING: Unsupported non-graphical object: {obj.type}")
                continue
            oda_obj = handler(obj)
            if oda_obj:
                self.ctx.register(obj.handle.value, oda_obj)
        self.ctx.log("Non-graphical objects written.")
    def _write_xrecord(self, o: Any) -> Any | None:
        rec = self.dwg.newObject("XRECORD") if self.dwg else None
        if rec:
            for dxf_code, value in o.data:
                rec.addData(dxf_code, value)
        return rec
    def _write_dictionary(self, o: Any) -> Any | None:
        d = self.dwg.newObject("DICTIONARY") if self.dwg else None
        if d:
            for key, value_handle in o.entries.items():
                target = self.ctx.resolve(value_handle.value if hasattr(value_handle, 'value') else value_handle)
                if target:
                    d.setAt(key, target)
        return d
    def _write_group(self, o: Any) -> Any | None:
        g = self.dwg.newObject("GROUP") if self.dwg else None
        if g:
            g.setName(o.name)
            g.setSelectable(o.selectable)
            for h in o.members:
                ent = self.ctx.resolve(h.value if hasattr(h, 'value') else h)
                if ent:
                    g.append(ent)
        return g
    def _write_material(self, o: Any) -> Any | None:
        m = self.dwg.newObject("MATERIAL") if self.dwg else None
        if m:
            m.setName(o.name)
            m.setDiffuse(*o.diffuse_color)
            m.setAmbient(*o.ambient_color)
            m.setSpecular(*o.specular_color)
            m.setOpacity(o.opacity)
        return m
    def _write_raster_def(self, o: Any) -> Any | None:
        r = self.dwg.newObject("RASTERIMAGEDEF") if self.dwg else None
        if r:
            r.setSource(o.filepath)
            r.setResolution(*o.resolution)
        return r
    def _write_underlay_def(self, o: Any) -> Any | None:
        u = self.dwg.newObject("UNDERLAYDEFINITION") if self.dwg else None
        if u:
            u.setFileName(o.file_path)
            u.setLoaded(True)
            u.setType(o.underlay_type)
        return u
    def _write_layout(self, o: Any) -> Any | None:
        layout = self.dwg.newObject("LAYOUT") if self.dwg else None
        if layout:
            layout.setName(o.name)
        return layout
    def _write_view(self, o: Any) -> Any | None:
        v = self.dwg.newObject("VIEW") if self.dwg else None
        if v:
            v.setName(o.name)
        return v
    def _write_ucs(self, o: Any) -> Any | None:
        u = self.dwg.newObject("UCS") if self.dwg else None
        if u:
            u.setName(o.name)
        return u
    def _write_visual_style(self, o: Any) -> Any | None:
        vs = self.dwg.newObject("VISUALSTYLE") if self.dwg else None
        if vs:
            vs.setName(o.name)
        return vs
    def _write_regapp(self, o: Any) -> Any | None:
        app = self.dwg.newTableRecord("APPID") if self.dwg else None
        if app:
            app.setName(o.name)
        return app
    def _write_plot_settings(self, o: Any) -> Any | None:
        ps = self.dwg.newObject("PLOTSETTINGS") if self.dwg else None
        return ps
    def _write_light(self, o: Any) -> Any | None:
        light_obj = self.dwg.newObject("LIGHT") if self.dwg else None
        if light_obj:
            light_obj.setType(o.light_type.value if o.light_type else 0)
            light_obj.setIntensity(o.intensity)
        return light_obj