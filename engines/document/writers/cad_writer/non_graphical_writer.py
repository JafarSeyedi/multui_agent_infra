# """
# NonGraphicalWriter
# Responsible for writing all NON-graphical DWG objects to the database.
# Covers:
#     - Dictionaries (root + nested)
#     - XRecords
#     - Groups
#     - Layers filters / layer states
#     - PlotSettings
#     - Materials
#     - Lights
#     - Render settings
#     - CADTableStyle, MLeaderStyle, DimStyle overrides (already declared in table_writer)
#     - Underlay Definitions (PDF, DGN, DWF)
#     - RasterImageDefs
#     - Layouts (non-viewport part)
#     - Named UCS / Views
#     - VisualStyles
#     - RegApp records (non-xdata)
#     - All non-entity DB objects referenced by handles
# This writer:
#     - Runs BEFORE EntityWriter and BEFORE BlockWriter.
#     - Ensures that all DB-objects exist and are registered for dependency resolution.
# """
# from __future__ import annotations
# from typing import Dict, Callable
# from .base_context import WriterContext
# from engines.document import csdm_core as C
# from engines.document import csdm_entities as E
# from engines.document import csdm_tables as T
# class NonGraphicalWriter:
#     """
#     Writes all NON-entity objects in DWG.
#     """
#     def __init__(self, ctx: WriterContext):
#         self.ctx = ctx
#         self.oda = ctx.oda
#         self.dwg = ctx.dwg
#         # Dispatch registry (CSDM type → writer method)
#         self._handlers: Dict[str, Callable] = {
#             "XRECORD": self._write_xrecord,
#             "DICTIONARY": self._write_dictionary,
#             "GROUP": self._write_group,
#             "MATERIAL": self._write_material,
#             "RASTER_IMAGE_DEF": self._write_raster_def,
#             "UNDERLAY_DEF": self._write_underlay_def,
#             "LAYOUT": self._write_layout,
#             "VIEW": self._write_view,
#             "UCS": self._write_ucs,
#             "VISUALSTYLE": self._write_visual_style,
#             "REGAPP": self._write_regapp,
#             "PLOTSETTINGS": self._write_plot_settings,
#             "LIGHT": self._write_light,
#         }
#     # =====================================================================
#     # Public API
#     # =====================================================================
#     def write(self):
#         self.ctx.log("Writing non-graphical DWG objects...")
#         for obj in self.ctx.csdm_doc.non_graphical_objects:
#             handler = self._handlers.get(obj.type)
#             if not handler:
#                 self.ctx.log(f"  WARNING: Unsupported non-graphical object: {obj.type}")
#                 continue
#             oda_obj = handler(obj)
#             if oda_obj:
#                 self.ctx.register(obj.handle, oda_obj)
#         self.ctx.log("Non-graphical objects written.")
#     # =====================================================================
#     # XRecords
#     # =====================================================================
#     def _write_xrecord(self, o: T.XRecord):
#         rec = self.dwg.newObject("XRECORD")
#         for dxf_code, value in o.data:
#             rec.addData(dxf_code, value)
#         return rec
#     # =====================================================================
#     # Dictionaries
#     # =====================================================================
#     def _write_dictionary(self, o: T.Dictionary):
#         """
#         Dictionaries can be nested. They get created BEFORE contents are added.
#         """
#         d = self.dwg.newObject("DICTIONARY")
#         for key, value_handle in o.items.items():
#             target = self.ctx.resolve(value_handle)
#             if target:
#                 d.setAt(key, target)
#         d.setHardOwnership(o.hard_ownership)
#         return d
#     # =====================================================================
#     # Groups
#     # =====================================================================
#     def _write_group(self, o: T.Group):
#         g = self.dwg.newObject("GROUP")
#         g.setName(o.name)
#         g.setSelectable(o.selectable)
#         for h in o.members:
#             ent = self.ctx.resolve(h)
#             if ent:
#                 g.append(ent)
#         return g
#     # =====================================================================
#     # Materials
#     # =====================================================================
#     def _write_material(self, o: T.Material):
#         m = self.dwg.newObject("MATERIAL")
#         m.setName(o.name)
#         m.setDiffuse(o.diffuse)
#         m.setAmbient(o.ambient)
#         m.setSpecular(o.specular)
#         m.setOpacity(o.opacity)
#         m.setMaps(o.texture_maps)
#         return m
#     # =====================================================================
#     # Raster Definitions
#     # =====================================================================
#     def _write_raster_def(self, o: T.RasterImageDef):
#         r = self.dwg.newObject("RASTERIMAGEDEF")
#         r.setSource(o.path)
#         r.setResolution(o.width, o.height)
#         r.setUnits(o.units)
#         return r
#     # =====================================================================
#     # Underlay Definitions (PDF/DWF/DGN)
#     # =====================================================================
#     def _write_underlay_def(self, o: T.UnderlayDef):
#         u = self.dwg.newObject("UNDERLAYDEFINITION")
#         u.setFileName(o.path)
#         u.setLoaded(True)
#         u.setType(o.underlay_type)   # PDF / DGN / DWF
#         return u
#     # =====================================================================
#     # Layout (non-viewport)
#     # =====================================================================
#     def _write_layout(self, o: T.Layout):
#         layout = self.dwg.newObject("LAYOUT")
#         layout.setName(o.name)
#         layout.setLimits(o.limits_min, o.limits_max)
#         layout.setInsertionBase(o.insert_base)
#         if o.paper_size:
#             layout.setPlotPaperSize(o.paper_size)
#         layout.setTabSelected(o.tab_selected)
#         # Visual properties
#         layout.setShadePlotMode(o.shade_plot_mode)
#         layout.setShadePlotResLevel(o.shade_plot_res)
#         return layout
#     # =====================================================================
#     # View definitions
#     # =====================================================================
#     def _write_view(self, o: T.View):
#         v = self.dwg.newObject("VIEW")
#         v.setName(o.name)
#         v.setTarget(o.target)
#         v.setDirection(o.direction)
#         v.setLensLength(o.lens_length)
#         v.setFrontClip(o.front_clip)
#         v.setBackClip(o.back_clip)
#         v.setFieldWidth(o.width)
#         v.setFieldHeight(o.height)
#         return v
#     # =====================================================================
#     # UCS
#     # =====================================================================
#     def _write_ucs(self, o: T.UCS):
#         u = self.dwg.newObject("UCS")
#         u.setName(o.name)
#         u.setOrigin(o.origin)
#         u.setXAxis(o.x_axis)
#         u.setYAxis(o.y_axis)
#         return u
#     # =====================================================================
#     # Visual Styles
#     # =====================================================================
#     def _write_visual_style(self, o: T.VisualStyle):
#         vs = self.dwg.newObject("VISUALSTYLE")
#         vs.setName(o.name)
#         vs.setType(o.style_type)
#         vs.setFaceStyle(o.face_style)
#         vs.setDisplayStyle(o.display_style)
#         vs.setEdgeStyle(o.edge_style)
#         return vs
#     # =====================================================================
#     # RegApp (Registered Applications)
#     # =====================================================================
#     def _write_regapp(self, o: T.RegApp):
#         app = self.dwg.newTableRecord("APPID")
#         app.setName(o.name)
#         return app
#     # =====================================================================
#     # Plot Settings
#     # =====================================================================
#     def _write_plot_settings(self, o: T.PlotSettings):
#         ps = self.dwg.newObject("PLOTSETTINGS")
#         ps.setPlotWindow(o.window_min, o.window_max)
#         ps.setPaperSize(o.paper_size)
#         ps.setPlotCentered(o.plot_centered)
#         ps.setScale(o.plot_scale)
#         ps.setPlotRotation(o.rotation)
#         return ps
#     # =====================================================================
#     # Light
#     # =====================================================================
#     def _write_light(self, o: T.Light):
#         l = self.dwg.newObject("LIGHT")
#         l.setLightType(o.light_type)
#         l.setIntensity(o.intensity)
#         l.setColor(o.color)
#         l.setPosition(o.position)
#         l.setTarget(o.target)
#         l.setAttenuation(o.atten_start, o.atten_end)
#         return l
