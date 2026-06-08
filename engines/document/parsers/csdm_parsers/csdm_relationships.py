# engines/document/parsers/csdm_parsers/csdm_relationships.py
from __future__ import annotations
import traceback
from typing import Dict, List, Optional
from ...models.csdm_core import (
    CSDMDocument,
    CSDMHandle,
    CSDMObject,
    XDataContainer,
    ReactorLink,
)
from ...models.csdm_entities import (
    BaseEntity,
    BlockReference,
)
from ...models.csdm_tables import (
    LayerEntry,
    LinetypeEntry,
    TextStyleEntry,
    DimStyleEntry,
    BlockRecord,
    VPortRecord,
    AppIDEntry,
)

class CSDMRelationshipResolver:
    def __init__(self, doc: CSDMDocument):
        self.doc = doc
        self.all_objects: Dict[str, object] = {}

    def resolve_all(self):
        self._build_lookup()
        self._resolve_entity_layer_links()
        self._resolve_table_links()
        self._resolve_block_owners()
        self._resolve_insert_block_links()
        self._propagate_insert_transforms()
        self._resolve_xdata_links()
        self._resolve_reactor_links()
        self._resolve_viewport_links()

    def _build_lookup(self):
        for t in self.doc.tables.layers:
            self.all_objects[t.handle] = t
        for t in self.doc.tables.linetypes:
            self.all_objects[t.handle] = t
        for t in self.doc.tables.text_styles:
            self.all_objects[t.handle] = t
        for t in self.doc.tables.dim_styles:
            self.all_objects[t.handle] = t
        for t in self.doc.tables.block_records:
            self.all_objects[t.handle] = t
        for t in self.doc.tables.viewports:
            self.all_objects[t.handle] = t
        for t in self.doc.tables.appids:
            self.all_objects[t.handle] = t
        for e in self.doc.entities:
            self.all_objects[e.handle] = e
        for o in self.doc.objects:
            self.all_objects[o.handle] = o

    def _resolve_entity_layer_links(self):
        layers = {layer.handle: layer for layer in self.doc.tables.layers}
        for ent in self.doc.entities:
            try:
                if ent.layer in layers:
                    ent.layer_obj = layers[ent.layer]
                else:
                    ent.layer_obj = None
            except Exception:
                traceback.print_exc()

    def _resolve_table_links(self):
        lt_map = {lt_entry.handle: lt_entry for lt_entry in self.doc.tables.linetypes}
        ts_map = {t.handle: t for t in self.doc.tables.text_styles}
        ds_map = {d.handle: d for d in self.doc.tables.dim_styles}
        for ent in self.doc.entities:
            try:
                if hasattr(ent, "style_handle"):
                    h = ent.style_handle
                    ent.style_obj = ts_map.get(h)
                if hasattr(ent, "dimstyle"):
                    ent.dimstyle_obj = ds_map.get(ent.dimstyle, None)
                if hasattr(ent, "linetype_handle"):
                    ent.linetype_obj = lt_map.get(ent.linetype_handle, None)
            except Exception:
                traceback.print_exc()

    def _resolve_block_owners(self):
        blocks = {b.handle: b for b in self.doc.tables.block_records}
        for e in self.doc.entities:
            try:
                blk = blocks.get(e.block)
                e.owner_block = blk
                if blk:
                    blk.entities.append(e)
            except Exception:
                traceback.print_exc()

    def _resolve_insert_block_links(self):
        blocks = {b.handle: b for b in self.doc.tables.block_records}
        for e in self.doc.entities:
            if isinstance(e, BlockReference):
                try:
                    e.block_obj = blocks.get(e.block_ref)
                except Exception:
                    traceback.print_exc()

    def _propagate_insert_transforms(self):
        def accumulate(parent_transform, child_transform):
            px, py, pz = parent_transform["position"]
            sx, sy, sz = parent_transform["scale"]
            pr = parent_transform["rotation"]
            cx, cy, cz = child_transform["position"]
            csx, csy, csz = child_transform["scale"]
            cr = child_transform["rotation"]
            return {
                "position": (px + cx * sx, py + cy * sy, pz + cz * sz),
                "scale": (sx * csx, sy * csy, sz * csz),
                "rotation": pr + cr,
            }
        for e in self.doc.entities:
            if not isinstance(e, BlockReference):
                continue
            base = {
                "position": e.position,
                "scale": e.scale,
                "rotation": e.rotation,
            }
            if e.owner_block and hasattr(e.owner_block, "parent_insert"):
                parent_tf = e.owner_block.parent_insert
                e.world_transform = accumulate(parent_tf, base)
            else:
                e.world_transform = base
            if e.block_obj:
                e.block_obj.parent_insert = e.world_transform

    def _resolve_xdata_links(self):
        appid_map = {a.name: a for a in self.doc.tables.appids}
        for obj in self.doc.entities + self.doc.objects:
            try:
                if obj.raw_xdata:
                    xd = XDataContainer()
                    for item in obj.raw_xdata:
                        app = item.get("app")
                        data = item.get("data")
                        if app in appid_map:
                            xd.entries.append({
                                "appid_obj": appid_map[app],
                                "data": data,
                            })
                        else:
                            xd.entries.append({
                                "appid_obj": None,
                                "data": data,
                            })
                    obj.xdata = xd
            except Exception:
                traceback.print_exc()

    def _resolve_reactor_links(self):
        for obj in self.doc.entities + self.doc.objects:
            try:
                new_links = []
                for r in obj.reactors:
                    target = self.all_objects.get(r.target)
                    if target:
                        new_links.append({"target": r.target, "target_obj": target})
                    else:
                        new_links.append(r)
                obj.reactors = new_links
            except Exception:
                traceback.print_exc()

    def _resolve_viewport_links(self):
        vport_map = {v.handle: v for v in self.doc.tables.viewports}
        for e in self.doc.entities:
            # FIXME: actual viewport entity type check
            if isinstance(e, dict):
                try:
                    e.table_viewport_obj = vport_map.get(e.handle)
                except Exception:
                    traceback.print_exc()
