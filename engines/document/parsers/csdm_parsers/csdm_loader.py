# engines/document/parsers/csdm_parsers/csdm_loader.py
from __future__ import annotations
import traceback
from typing import Any, Dict, List, Optional, Tuple, Iterable
from .oda_bridge import (
    ODADocumentHandle,
    ODAObjectProxy,
    ODAHandle,
)
from ...models.csdm_core import (
    CSDMDocument,
    CSDMObject,
    CSDMHandle,
    XDataContainer,
    ReactorLink,
)
from ...models.media_types import MEDIA_TYPES
from ...models.csdm_tables import (
    LayerEntry,
    LinetypeEntry,
    TextStyleEntry,
    DimStyleEntry,
    UCSRecord,
    ViewRecord,
    VPortRecord,
    BlockRecord,
    AppIDEntry,
)
from ...models.csdm_entities import (
    BaseEntity,
    LineEntity,
    CircleEntity,
    ArcEntity,
    LWPolylineEntity,
    PolylineEntity,
    TextEntity,
    MTextEntity,
    BlockReference,
    DimensionEntity,
    HatchEntity,
    Solid3DEntity,
    SplineEntity,
    LeaderEntity,
    MLeaderEntity,
    TableEntity,
    ImageEntity,
    UnderlayEntity,
)

class CSDMLoader:
    def __init__(self, oda_doc: ODADocumentHandle, title="Untitled", document_id="untitled", media_type=None):
        self.oda = oda_doc
        self.doc = CSDMDocument(
            title=title,
            document_id=document_id,
            media_type=media_type or MEDIA_TYPES["dwg"],
        )
        self.entity_map: Dict[str, BaseEntity] = {}
        self.object_map: Dict[str, CSDMObject] = {}

    def load_all(self) -> CSDMDocument:
        self._load_tables()
        self._load_block_records()
        self._load_dictionary()
        self._load_xrefs()
        self._resolve_references()
        return self.doc

    def _load_tables(self) -> None:
        tables = self.oda.list_tables()
        self._load_layer_table(tables.get("layers", []))
        self._load_linetype_table(tables.get("linetypes", []))
        self._load_textstyle_table(tables.get("text_styles", []))
        self._load_dimstyle_table(tables.get("dim_styles", []))
        self._load_ucs_table(tables.get("ucs", []))
        self._load_view_table(tables.get("views", []))
        self._load_vport_table(tables.get("vports", []))
        self._load_appid_table(tables.get("appids", []))

    def _load_layer_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = LayerEntry(
                    handle=str(rec.handle),
                    name=o.getName(),
                    color=o.color().rgb() if hasattr(o.color(), "rgb") else 0xFFFFFF,
                    linetype=o.linetype().getHandle().ascii() if hasattr(o, "linetype") else "0",
                    frozen=o.isFrozen() if hasattr(o, "isFrozen") else False,
                    lineweight=o.lineWeight() if hasattr(o, "lineWeight") else 0,
                    flags=o.getFlags() if hasattr(o, "getFlags") else 0,
                )
                self.doc.tables.layers.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_linetype_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = LinetypeEntry(
                    handle=str(rec.handle),
                    name=o.getName(),
                    pattern_length=o.patternLength() if hasattr(o, "patternLength") else 0.0,
                )
                self.doc.tables.linetypes.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_textstyle_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = TextStyleEntry(
                    handle=str(rec.handle),
                    name=o.getName(),
                    font=o.fileName() if hasattr(o, "fileName") else "",
                    height=o.textSize() if hasattr(o, "textSize") else 1.0,
                    width_factor=o.xScale() if hasattr(o, "xScale") else 1.0,
                )
                self.doc.tables.text_styles.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_dimstyle_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = DimStyleEntry(
                    handle=str(rec.handle),
                    name=o.getName(),
                    dimscale=o.dimscale() if hasattr(o, "dimscale") else 1.0,
                )
                self.doc.tables.dim_styles.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_ucs_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = UCSRecord(
                    handle=str(rec.handle),
                    name=o.getName(),
                )
                self.doc.tables.ucs.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_view_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = ViewRecord(handle=str(rec.handle), name=o.getName())
                self.doc.tables.views.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_vport_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = VPortRecord(
                    handle=str(rec.handle),
                    name=o.getName(),
                    center=(o.centerPoint().x, o.centerPoint().y)
                    if hasattr(o, "centerPoint")
                    else (0, 0),
                )
                self.doc.tables.viewports.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_appid_table(self, records: List[ODAObjectProxy]):
        for rec in records:
            try:
                o = rec._obj
                cs = AppIDEntry(handle=str(rec.handle), name=o.getName())
                self.doc.tables.appids.append(cs)
                self.object_map[str(rec.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_block_records(self):
        block_records = self.oda.list_block_records()
        for blk in block_records:
            try:
                o = blk._obj
                cs = BlockRecord(
                    handle=str(blk.handle),
                    name=o.getName(),
                    is_model_space=o.isModelSpace() if hasattr(o, "isModelSpace") else False,
                )
                self.doc.tables.block_records.append(cs)
                self.object_map[str(blk.handle)] = cs
                ents = self.oda.list_entities_in_block(blk)
                self._load_entities(blk_handle=str(blk.handle), entities=ents)
            except Exception:
                traceback.print_exc()

    def _load_entities(self, blk_handle: str, entities: List[ODAObjectProxy]):
        for ent in entities:
            try:
                cs_ent = self._map_entity(ent)
                if cs_ent:
                    cs_ent.block = blk_handle
                    self.doc.entities.append(cs_ent)
                    self.entity_map[str(ent.handle)] = cs_ent
            except Exception:
                traceback.print_exc()

    def _map_entity(self, ent: ODAObjectProxy) -> Optional[BaseEntity]:
        cls = ent.object_class.lower()
        if "line" in cls:
            return self._map_line(ent)
        if "circle" in cls:
            return self._map_circle(ent)
        if "arc" in cls:
            return self._map_arc(ent)
        if "polyline" in cls and "3d" not in cls:
            return self._map_polyline2d(ent)
        if "polyline3d" in cls:
            return self._map_polyline3d(ent)
        if "text" == cls:
            return self._map_text(ent)
        if "mtext" in cls:
            return self._map_mtext(ent)
        if "insert" in cls:
            return self._map_insert(ent)
        if "dimension" in cls:
            return self._map_dimension(ent)
        if "hatch" in cls:
            return self._map_hatch(ent)
        if "3dsolid" in cls:
            return self._map_3dsolid(ent)
        if "mesh" in cls:
            return self._map_mesh(ent)
        if "spline" in cls:
            return self._map_spline(ent)
        if "leader" in cls:
            return self._map_leader(ent)
        if "mleader" in cls:
            return self._map_mleader(ent)
        if "image" in cls:
            return self._map_raster(ent)
        if "underlay" in cls:
            return self._map_underlay(ent)
        if "viewport" in cls:
            return self._map_viewportent(ent)
        return BaseEntity(
            handle=str(ent.handle),
            entity_type=ent.object_class,
            layer=self._safe_layer(ent),
        )

    def _map_line(self, ent: ODAObjectProxy) -> LineEntity:
        return LineEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_circle(self, ent: ODAObjectProxy) -> CircleEntity:
        return CircleEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_arc(self, ent: ODAObjectProxy) -> ArcEntity:
        return ArcEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_polyline2d(self, ent: ODAObjectProxy) -> LWPolylineEntity:
        return LWPolylineEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_polyline3d(self, ent: ODAObjectProxy) -> PolylineEntity:
        return PolylineEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_text(self, ent: ODAObjectProxy) -> TextEntity:
        o = ent._obj
        p = o.position()
        return TextEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            text=o.textString(),
            position=(p.x, p.y, p.z),
            height=o.height(),
            rotation=o.rotation(),
            style_handle=o.textStyle().getHandle().ascii() if hasattr(o, "textStyle") else "0",
        )

    def _map_mtext(self, ent: ODAObjectProxy) -> MTextEntity:
        o = ent._obj
        p = o.location()
        return MTextEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            text=o.contents(),
            position=(p.x, p.y, p.z),
            width=o.width(),
            height=o.textHeight(),
            rotation=o.rotation(),
            style_handle=o.textStyle().getHandle().ascii() if hasattr(o, "textStyle") else "0",
        )

    def _map_insert(self, ent: ODAObjectProxy) -> BlockReference:
        o = ent._obj
        p = o.position()
        return BlockReference(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            block_ref=o.blockTableRecord().getHandle().ascii(),
            position=(p.x, p.y, p.z),
            scale=(o.scaleFactors().x, o.scaleFactors().y, o.scaleFactors().z),
            rotation=o.rotation(),
        )

    def _map_dimension(self, ent: ODAObjectProxy) -> BaseEntity:
        return DimensionEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_hatch(self, ent: ODAObjectProxy) -> HatchEntity:
        o = ent._obj
        loops = []
        try:
            for i in range(o.numLoops()):
                lp = o.loopAt(i)
                pts = []
                for j in range(lp.numEdges()):
                    ed = lp.edgeAt(j)
                    if hasattr(ed, "vertex"):
                        p = ed.vertex()
                        pts.append((p.x, p.y))
                loops.append(pts)
        except Exception:
            pass
        return HatchEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            loops=loops,
            pattern=o.patternName(),
        )

    def _map_3dsolid(self, ent: ODAObjectProxy) -> Solid3DEntity:
        self.oda.extract_geometry(ent)
        return Solid3DEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_mesh(self, ent: ODAObjectProxy) -> BaseEntity:
        self.oda.extract_geometry(ent)
        return BaseEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            entity_type=ent.object_class,
        )

    def _map_spline(self, ent: ODAObjectProxy) -> SplineEntity:
        o = ent._obj
        pts = []
        try:
            for i in range(o.numControlPoints()):
                p = o.controlPointAt(i)
                pts.append((p.x, p.y, p.z))
        except Exception:
            pass
        return SplineEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            control_points=pts,
            degree=o.degree() if hasattr(o, "degree") else 3,
        )

    def _map_leader(self, ent: ODAObjectProxy) -> LeaderEntity:
        o = ent._obj
        try:
            o.numVertices()
        except Exception:
            pass
        return LeaderEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_mleader(self, ent: ODAObjectProxy) -> MLeaderEntity:
        return MLeaderEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_raster(self, ent: ODAObjectProxy) -> ImageEntity:
        return ImageEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_underlay(self, ent: ODAObjectProxy) -> UnderlayEntity:
        return UnderlayEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
        )

    def _map_viewportent(self, ent: ODAObjectProxy) -> BaseEntity:
        return BaseEntity(
            handle=str(ent.handle),
            layer=self._safe_layer(ent),
            entity_type=ent.object_class,
        )

    def _load_dictionary(self):
        root = self.oda.list_root_dictionary()
        for name, obj in root.items():
            try:
                cs = CSDMObject(
                    handle=str(obj.handle),
                )
                self.doc.objects.append(cs)
                self.object_map[str(obj.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _load_xrefs(self):
        xrefs = self.oda.list_xrefs()
        for obj in xrefs:
            try:
                cs = CSDMObject(
                    handle=str(obj.handle),
                )
                self.doc.objects.append(cs)
                self.object_map[str(obj.handle)] = cs
            except Exception:
                traceback.print_exc()

    def _resolve_references(self):
        for handle, ent in self.entity_map.items():
            try:
                self.oda.extract_reactors(ODAObjectProxy(ent))
            except Exception:
                pass

    def _safe_layer(self, ent: ODAObjectProxy) -> str:
        try:
            return ent._obj.layerId().getHandle().ascii()
        except Exception:
            return "0"
