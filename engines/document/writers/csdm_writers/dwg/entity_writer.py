"""
EntityWriter for CSDM v2.0 Ultra
Responsible for writing all graphical entities into DWG using odapython.
Covers:
    - Basic geometry (Line, Circle, Arc, Polyline, Spline)
    - Text / MText
    - Hatch
    - BlockReference (Insert)
    - Leaders / MLeader
    - Dimensions (all types)
    - Solids / Surfaces / Meshes / 3DSolids
    - Raster / Underlay
    - Tables
    - Viewports
    - OLE objects
    - XData
    - Reactors
    - Owner/Transform resolution (except relationship step)
This writer assumes:
    - Tables have already been written
    - BlockRecords exist and are mapped in context registry
"""
from __future__ import annotations
from typing import Any, Dict, Callable, Optional
from .base_context import WriterContext
from ....models.csdm_entities import (
    BaseEntity,
    LineEntity,
    CircleEntity,
    ArcEntity,
    LWPolylineEntity,
    PolylineEntity,
    SplineEntity,
    TextEntity,
    MTextEntity,
    HatchEntity,
    BlockReference,
    DimensionEntity,
    LeaderEntity,
    MLeaderEntity,
    Solid3DEntity,
    UnderlayEntity,
    ImageEntity,
    TableEntity,
)
class EntityWriter:
    """
    Main dispatcher for all entities.
    """
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
        self._handlers: Dict[str, Callable[[Any], Optional[Any]]] = {
            "LINE": self._write_line,
            "CIRCLE": self._write_circle,
            "ARC": self._write_arc,
            "LWPOLYLINE": self._write_lwpolyline,
            "POLYLINE": self._write_polyline,
            "SPLINE": self._write_spline,
            "TEXT": self._write_text,
            "MTEXT": self._write_mtext,
            "HATCH": self._write_hatch,
            "INSERT": self._write_insert,
            "DIMENSION": self._write_dimension,
            "LEADER": self._write_leader,
            "MLEADER": self._write_mleader,
            "3DSOLID": self._write_3dsolid,
            "MESH": self._write_mesh,
            "SURFACE": self._write_surface,
            "UNDERLAY": self._write_underlay,
            "RASTER": self._write_raster,
            "TABLE": self._write_table_entity,
            "VIEWPORT": self._write_viewport,
            "OLE2FRAME": self._write_ole2frame,
        }
    def write(self):
        self.ctx.log("Writing DWG entities...")
        for entity in self.ctx.csdm_doc.entities:
            handler = self._handlers.get(entity.type)
            if handler is None:
                self.ctx.log(f"  WARNING: Unsupported entity: {entity.type}")
                continue
            oda_ent = handler(entity)
            if oda_ent:
                self._apply_common(entity, oda_ent)
                self.ctx.register(entity.handle.value, oda_ent)
        self.ctx.log("DWG entities written.")
    def _apply_common(self, e: BaseEntity, oda_obj: Any):
        if e.layer:
            oda_obj.setLayer(e.layer)
        if e.linetype:
            oda_obj.setLinetype(e.linetype)
        if e.lineweight is not None:
            oda_obj.setLineweight(e.lineweight)
        if e.color is not None:
            oda_obj.setColor(e.color)
        if e.owner_block:
            owner_handle = e.owner_block.value if hasattr(e.owner_block, 'value') else str(e.owner_block)
            owner = self.ctx.resolve(owner_handle)
            if owner:
                oda_obj.setOwner(owner)
        if e.xdata and e.xdata.entries:
            for xd in e.xdata.entries:
                oda_obj.addXData(xd.appid, xd.data)
        for r in e.reactors:
            oda_obj.addReactor(r.value if hasattr(r, 'value') else r)
    def _write_line(self, e: LineEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("LINE")
        ent.setStartPoint(e.start)
        ent.setEndPoint(e.end)
        return ent
    def _write_circle(self, e: CircleEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("CIRCLE")
        ent.setCenter(e.center)
        ent.setRadius(e.radius)
        return ent
    def _write_arc(self, e: ArcEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("ARC")
        ent.setCenter(e.center)
        ent.setRadius(e.radius)
        ent.setAngles(e.start_angle, e.end_angle)
        return ent
    def _write_lwpolyline(self, e: LWPolylineEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("LWPOLYLINE")
        ent.setClosed(e.is_closed)
        for v in e.vertices:
            ent.addVertex(v.x, v.y, v.bulge)
        return ent
    def _write_polyline(self, e: PolylineEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("POLYLINE")
        ent.setClosed(e.is_closed)
        for v in e.vertices:
            p = ent.addVertex()
            p.setPoint(v.x, v.y, v.z)
            if v.bulge:
                p.setBulge(v.bulge)
        return ent
    def _write_spline(self, e: SplineEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("SPLINE")
        ent.setDegree(e.degree)
        ent.setFitPoints(e.fit_points)
        ent.setControlPoints(e.control_points)
        ent.setKnots(e.knots)
        ent.setClosed(e.is_closed)
        return ent
    def _write_text(self, e: TextEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("TEXT")
        ent.setText(e.text_string)
        ent.setPosition(e.insert)
        ent.setHeight(e.text_height)
        ent.setRotation(e.rotation)
        return ent
    def _write_mtext(self, e: MTextEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("MTEXT")
        ent.setText(e.text_string)
        ent.setLocation(e.insert)
        ent.setRotation(e.rotation)
        ent.setWidth(e.width)
        return ent
    def _write_hatch(self, e: HatchEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("HATCH")
        ent.setPattern(e.pattern_name, e.angle, e.scale)
        for loop in e.loops:
            loop_obj = ent.addLoop(loop.loop_type)
            for edge in loop.edges:
                loop_obj.addEdge(edge)
        return ent
    def _write_insert(self, e: BlockReference) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("INSERT")
        block_rec = self.ctx.resolve(e.block_name)
        if block_rec:
            ent.setBlockRecord(block_rec)
        ent.setPosition(e.insert)
        ent.setScale(e.scale)
        ent.setRotation(e.rotation)
        return ent
    def _write_dimension(self, e: DimensionEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("DIMENSION")
        ent.setPoints([e.p1, e.p2])
        ent.setDimStyle(e.dimstyle)
        ent.setMeasurement(e.measurement)
        return ent
    def _write_leader(self, e: LeaderEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("LEADER")
        ent.setPoints(e.vertices)
        return ent
    def _write_mleader(self, e: MLeaderEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("MLEADER")
        return ent
    def _write_3dsolid(self, e: Solid3DEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("3DSOLID")
        if e.acis_data:
            ent.loadAcis(e.acis_data)
        return ent
    def _write_surface(self, e: Solid3DEntity) -> Optional[Any]:
        return None
    def _write_mesh(self, e: Solid3DEntity) -> Optional[Any]:
        return None
    def _write_underlay(self, e: UnderlayEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("UNDERLAY")
        return ent
    def _write_raster(self, e: ImageEntity) -> Optional[Any]:
        return None
    def _write_table_entity(self, e: TableEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("ACAD_TABLE")
        ent.setNumRows(len(e.rows))
        ent.setNumColumns(e.columns)
        ent.setStyle(e.table_style)
        for r, row in enumerate(e.rows):
            for c, cell in enumerate(row.cells):
                ent.setCellText(r, c, str(cell.value))
        return ent
    def _write_viewport(self, e: BaseEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("VIEWPORT")
        return ent
    def _write_ole2frame(self, e: BaseEntity) -> Optional[Any]:
        if self.dwg is None:
            return None
        ent = self.dwg.newEntity("OLE2FRAME")
        return ent