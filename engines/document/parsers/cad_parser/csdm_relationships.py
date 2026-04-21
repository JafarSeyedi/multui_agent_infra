# # engines/document/parsers/cad_parser/csdm_relationships.py

# from __future__ import annotations

# import traceback
# from typing import Dict, List, Optional

# from engines.document.models.csdm_core import (
#     CSDMDocument,
#     CSDMHandle,
#     CSDMObjectBase,
#     CSDMXData,
#     CSDMReactorLink,
# )

# from engines.document.models.csdm_entities import (
#     CSDMEntityBase,
#     CSDMInsert,
#     CSDMViewportEntity,
# )

# from engines.document.models.csdm_tables import (
#     CSDMLayer,
#     CSDMLinetype,
#     CSDMTextStyle,
#     CSDMDimStyle,
#     CSDMBlockRecord,
#     CSDMViewport,
#     CSDMAppID,
# )


# # ------------------------------------------------------------------------------
# #   CSDM Relationship Resolver
# # ------------------------------------------------------------------------------
# class CSDMRelationshipResolver:
#     """
#     مسؤولیت:
#     - resolve تمام Handleها
#     - owner resolution
#     - block reference resolution
#     - nested transforms
#     - table reference linking
#     - xref linking
#     - reactor graph linking
#     - annotation context linking
#     """

#     def __init__(self, doc: CSDMDocument):
#         self.doc = doc

#         # lookup tables
#         self.all_objects: Dict[str, object] = {}

#     # ======================================================================
#     #   PUBLIC API
#     # ======================================================================
#     def resolve_all(self):
#         self._build_lookup()
#         self._resolve_entity_layer_links()
#         self._resolve_table_links()
#         self._resolve_block_owners()
#         self._resolve_insert_block_links()
#         self._propagate_insert_transforms()
#         self._resolve_xdata_links()
#         self._resolve_reactor_links()
#         self._resolve_viewport_links()

#     # ======================================================================
#     #   Build handle → object map
#     # ======================================================================
#     def _build_lookup(self):
#         # tables
#         for t in self.doc.tables.layers:
#             self.all_objects[t.handle] = t
#         for t in self.doc.tables.linetypes:
#             self.all_objects[t.handle] = t
#         for t in self.doc.tables.text_styles:
#             self.all_objects[t.handle] = t
#         for t in self.doc.tables.dim_styles:
#             self.all_objects[t.handle] = t
#         for t in self.doc.tables.block_records:
#             self.all_objects[t.handle] = t
#         for t in self.doc.tables.viewports:
#             self.all_objects[t.handle] = t
#         for t in self.doc.tables.appids:
#             self.all_objects[t.handle] = t

#         # entities
#         for e in self.doc.entities:
#             self.all_objects[e.handle] = e

#         # dictionary objects
#         for o in self.doc.objects:
#             self.all_objects[o.handle] = o

#     # ======================================================================
#     #   Resolve Layer for each entity
#     # ======================================================================
#     def _resolve_entity_layer_links(self):
#         layers = {l.handle: l for l in self.doc.tables.layers}

#         for ent in self.doc.entities:
#             try:
#                 if ent.layer in layers:
#                     ent.layer_obj = layers[ent.layer]
#                 else:
#                     ent.layer_obj = None
#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Resolve other table references
#     # ======================================================================
#     def _resolve_table_links(self):
#         lt_map = {l.handle: l for l in self.doc.tables.linetypes}
#         ts_map = {t.handle: t for t in self.doc.tables.text_styles}
#         ds_map = {d.handle: d for d in self.doc.tables.dim_styles}

#         for ent in self.doc.entities:
#             try:
#                 # link text styles
#                 if hasattr(ent, "style_handle"):
#                     h = ent.style_handle
#                     ent.style_obj = ts_map.get(h)

#                 # link dimension styles
#                 if hasattr(ent, "dimstyle"):
#                     ent.dimstyle_obj = ds_map.get(ent.dimstyle, None)

#                 # link linetype (if entity supports it)
#                 # optional, many entities do
#                 if hasattr(ent, "linetype_handle"):
#                     ent.linetype_obj = lt_map.get(ent.linetype_handle, None)

#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Block owner → Entity linking
#     # ======================================================================
#     def _resolve_block_owners(self):
#         """
#         هر Entity یک field block دارد که handle block record را نگه می‌دارد.
#         اینجا owner_obj را resolve می‌کنیم.
#         """
#         blocks = {b.handle: b for b in self.doc.tables.block_records}

#         for e in self.doc.entities:
#             try:
#                 blk = blocks.get(e.block)
#                 e.owner_block = blk
#                 if blk:
#                     blk.entities.append(e)
#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Insert block reference linking
#     # ======================================================================
#     def _resolve_insert_block_links(self):
#         """
#         Insert → BlockRecord linking
#         """
#         blocks = {b.handle: b for b in self.doc.tables.block_records}

#         for e in self.doc.entities:
#             if isinstance(e, CSDMInsert):
#                 try:
#                     e.block_obj = blocks.get(e.block_ref)
#                 except Exception:
#                     traceback.print_exc()

#     # ======================================================================
#     #   Nested Insert transform propagation
#     # ======================================================================
#     def _propagate_insert_transforms(self):
#         """
#         Insertهای تودرتو: تبدیل نهایی هر instance.
#         کاملاً صنعتی و براساس استاندارد DWG.
#         """

#         def accumulate(parent_transform, child_transform):
#             # ترکیب ماتریس‌ها (مقیاس، چرخش، انتقال)
#             px, py, pz = parent_transform["position"]
#             sx, sy, sz = parent_transform["scale"]
#             pr = parent_transform["rotation"]

#             cx, cy, cz = child_transform["position"]
#             csx, csy, csz = child_transform["scale"]
#             cr = child_transform["rotation"]

#             return {
#                 "position": (px + cx * sx, py + cy * sy, pz + cz * sz),
#                 "scale": (sx * csx, sy * csy, sz * csz),
#                 "rotation": pr + cr,
#             }

#         # یک بار کل مدل را traverse می‌کنیم
#         for e in self.doc.entities:
#             if not isinstance(e, CSDMInsert):
#                 continue

#             # transform خود entity
#             base = {
#                 "position": e.position,
#                 "scale": e.scale,
#                 "rotation": e.rotation,
#             }

#             # اگر parent insert دارد (nested block)
#             if e.owner_block and hasattr(e.owner_block, "parent_insert"):
#                 parent_tf = e.owner_block.parent_insert
#                 e.world_transform = accumulate(parent_tf, base)
#             else:
#                 e.world_transform = base

#             # own transform را در block record ذخیره می‌کنیم
#             if e.block_obj:
#                 e.block_obj.parent_insert = e.world_transform

#     # ======================================================================
#     #   XData linking
#     # ======================================================================
#     def _resolve_xdata_links(self):
#         appid_map = {a.name: a for a in self.doc.tables.appids}

#         for obj in self.doc.entities + self.doc.objects:
#             try:
#                 if obj.raw_xdata:
#                     xd = CSDMXData()

#                     for item in obj.raw_xdata:
#                         app = item.get("app")
#                         data = item.get("data")

#                         if app in appid_map:
#                             xd.entries.append({
#                                 "appid_obj": appid_map[app],
#                                 "data": data,
#                             })
#                         else:
#                             xd.entries.append({
#                                 "appid_obj": None,
#                                 "data": data,
#                             })

#                     obj.xdata = xd

#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Reactor Linking
#     # ======================================================================
#     def _resolve_reactor_links(self):
#         for obj in self.doc.entities + self.doc.objects:
#             try:
#                 new_links = []
#                 for r in obj.reactors:
#                     target = self.all_objects.get(r.target)
#                     if target:
#                         new_links.append(CSDMReactorLink(target=r.target, target_obj=target))
#                     else:
#                         new_links.append(r)
#                 obj.reactors = new_links
#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Viewport linking (Layout → Entity / Table Viewport)
#     # ======================================================================
#     def _resolve_viewport_links(self):
#         vport_map = {v.handle: v for v in self.doc.tables.viewports}

#         for e in self.doc.entities:
#             if isinstance(e, CSDMViewportEntity):
#                 try:
#                     e.table_viewport_obj = vport_map.get(e.handle)
#                 except Exception:
#                     traceback.print_exc()
