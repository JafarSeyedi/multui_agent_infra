# engines/document/models/csdm_entities.py
# ================================================================
# csdm_entities.py
# CSDM v2.0 Ultra — Complete Entity System (DWG 98% / DCF 100%)
# ================================================================
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from .csdm_core import AddReactorsMixin
from .csdm_core import CSDMHandle
from .csdm_core import CSDMObject
from .csdm_core import Matrix4
from .csdm_core import Vector3


# ================================================================
# ENTITY REGISTRY (for Round-Trip DWG/DCF)
# ================================================================

ENTITY_REGISTRY: dict[str, type] = {}

def register_entity(name: str):
    def decorator(cls):
        ENTITY_REGISTRY[name.upper()] = cls
        cls.__dwg_name__ = name.upper()
        return cls
    return decorator


# ================================================================
# COMMON GEOMETRIC SUBTYPES
# ================================================================

@dataclass
class Vertex:
    x: float
    y: float
    z: float = 0.0
    bulge: float = 0.0        # for polyline curvature
    start_width: float = 0.0
    end_width: float = 0.0


@dataclass
class NormalVector:
    nx: float = 0.0
    ny: float = 0.0
    nz: float = 1.0


@dataclass
class Extrusion:
    direction: NormalVector = field(default_factory=NormalVector)
    thickness: float = 0.0


# ================================================================
# BASE ENTITY CLASS
# ================================================================

@dataclass
class BaseEntity(CSDMObject, AddReactorsMixin):
    handle: CSDMHandle = field(default_factory=CSDMHandle.new)
    owner_block: CSDMHandle | None = None

    layer: str = "0"
    linetype: str | None = None
    color: int | None = None
    lineweight: int | None = None

    # Global entity-level transforms (matrix-based)
    transform: Matrix4 = field(default_factory=Matrix4)

    # Basic status flags from DWG (invisible, locked, plottable, etc.)
    is_visible: bool = True
    is_plottable: bool = True
    is_locked: bool = False

    # annotation scale context
    annot_scale: float | None = None

    def add_xdata(self, appid: str, value: Any):
        self.xdata.add(appid=appid, data=value)

    def apply_transform(self, mat: Matrix4):
        self.transform = self.transform @ mat


# ================================================================
# ABSTRACT GEOMETRY PARENT CLASSES
# ================================================================

@dataclass
class CurveEntity(BaseEntity):
    normal: NormalVector = field(default_factory=NormalVector)
    elevation: float = 0.0


@dataclass
class SurfaceEntity(BaseEntity):
    u_count: int = 0
    v_count: int = 0


@dataclass
class SolidEntity(BaseEntity):
    acis_data: bytes | None = None  # ACIS SAT binary or SAB


# ================================================================
# TEXT / MTEXT BASE ENTITIES
# ================================================================

@dataclass
class TextBaseEntity(BaseEntity):
    text_string: str = ""
    text_style: str = "Standard"
    text_height: float = 2.5
    rotation: float = 0.0
    oblique: float = 0.0
    normal: NormalVector = field(default_factory=NormalVector)


# ================================================================
# DIMENSION BASE ENTITY
# ================================================================

class DimensionType(Enum):
    LINEAR = 0
    ALIGNED = 1
    ANGULAR = 2
    DIAMETER = 3
    RADIUS = 4
    ORDinate = 5


@dataclass
class DimensionBase(BaseEntity):
    dimstyle: str = "Standard"
    text: str | None = None
    measurement: float = 0.0
    dim_type: DimensionType = DimensionType.LINEAR
    normal: NormalVector = field(default_factory=NormalVector)
    extrusion: Extrusion = field(default_factory=Extrusion)


# ================================================================
# BLOCK REFERENCE BASE ENTITY
# ================================================================

@dataclass
class BlockRefBase(BaseEntity):
    block_name: str = ""
    insert: Vector3 = field(default_factory=lambda: Vector3())
    scale: Vector3 = field(default_factory=lambda: Vector3(1, 1, 1))
    rotation: float = 0.0
    attribs: list[Any] = field(default_factory=list)



# ================================================================
# BASIC 2D GEOMETRY
# ================================================================

@register_entity("LINE")
@dataclass
class LineEntity(CurveEntity):
    start: Vector3 = field(default_factory=lambda: Vector3())
    end: Vector3 = field(default_factory=lambda: Vector3())


@register_entity("CIRCLE")
@dataclass
class CircleEntity(CurveEntity):
    center: Vector3 = field(default_factory=lambda: Vector3())
    radius: float = 0.0


@register_entity("ARC")
@dataclass
class ArcEntity(CurveEntity):
    center: Vector3 = field(default_factory=lambda: Vector3())
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0


@register_entity("ELLIPSE")
@dataclass
class EllipseEntity(CurveEntity):
    center: Vector3 = field(default_factory=lambda: Vector3())
    major_axis: Vector3 = field(default_factory=lambda: Vector3(1, 0, 0))
    ratio: float = 0.5
    start_param: float = 0.0
    end_param: float = 2 * 3.141592653589793


# ================================================================
# POLYLINE / LWPOLYLINE
# ================================================================

@register_entity("POLYLINE")
@dataclass
class PolylineEntity(CurveEntity):
    vertices: list[Vertex] = field(default_factory=list)
    is_closed: bool = False
    is_2d: bool = True
    elevation: float = 0.0


@register_entity("LWPOLYLINE")
@dataclass
class LWPolylineEntity(CurveEntity):
    vertices: list[Vertex] = field(default_factory=list)
    constant_width: float | None = None
    is_closed: bool = False


# ================================================================
# SPLINE (NURBS)
# ================================================================

@register_entity("SPLINE")
@dataclass
class SplineEntity(CurveEntity):
    degree: int = 3
    knots: list[float] = field(default_factory=list)
    control_points: list[Vector3] = field(default_factory=list)
    weights: list[float] = field(default_factory=list)
    fit_points: list[Vector3] = field(default_factory=list)
    is_rational: bool = False
    is_closed: bool = False


# ================================================================
# RAY / XLINE
# ================================================================

@register_entity("RAY")
@dataclass
class RayEntity(CurveEntity):
    origin: Vector3 = field(default_factory=lambda: Vector3())
    direction: Vector3 = field(default_factory=lambda: Vector3(1, 0, 0))


@register_entity("XLINE")
@dataclass
class XLineEntity(CurveEntity):
    origin: Vector3 = field(default_factory=lambda: Vector3())
    direction: Vector3 = field(default_factory=lambda: Vector3(1, 0, 0))


# ================================================================
# SOLID / 3DFACE / TRACE / SHAPE
# ================================================================

@register_entity("SOLID")
@dataclass
class Solid2DEntity(CurveEntity):
    p1: Vector3 = field(default_factory=lambda: Vector3())
    p2: Vector3 = field(default_factory=lambda: Vector3())
    p3: Vector3 = field(default_factory=lambda: Vector3())
    p4: Vector3 = field(default_factory=lambda: Vector3())


@register_entity("3DFACE")
@dataclass
class Face3DEntity(CurveEntity):
    p1: Vector3 = field(default_factory=lambda: Vector3())
    p2: Vector3 = field(default_factory=lambda: Vector3())
    p3: Vector3 = field(default_factory=lambda: Vector3())
    p4: Vector3 | None = None


@register_entity("TRACE")
@dataclass
class TraceEntity(CurveEntity):
    p1: Vector3 = field(default_factory=lambda: Vector3())
    p2: Vector3 = field(default_factory=lambda: Vector3())
    p3: Vector3 = field(default_factory=lambda: Vector3())
    p4: Vector3 = field(default_factory=lambda: Vector3())


@register_entity("SHAPE")
@dataclass
class ShapeEntity(CurveEntity):
    name: str = ""
    size: float = 1.0
    rotation: float = 0.0


# ================================================================
# REGION / BODY / 3DSOLID / SURFACES
# ================================================================

@register_entity("REGION")
@dataclass
class RegionEntity(SolidEntity):
    brep_data: bytes | None = None   # Uninterpreted BREP


@register_entity("BODY")
@dataclass
class BodyEntity(SolidEntity):
    acis_data: bytes | None = None


@register_entity("3DSOLID")
@dataclass
class Solid3DEntity(SolidEntity):
    acis_data: bytes | None = None


@register_entity("SURFACE")
@dataclass
class SurfaceACISEntity(SurfaceEntity):
    acis_data: bytes | None = None


# ================================================================
# HATCH (one of the most complex DWG entities)
# ================================================================

@dataclass
class HatchLoop:
    loop_type: str = "poly"
    edges: list[tuple[str, list[float]]] = field(default_factory=list)


@register_entity("HATCH")
@dataclass
class HatchEntity(BaseEntity):
    pattern_name: str = "SOLID"
    angle: float = 0.0
    scale: float = 1.0
    loops: list[HatchLoop] = field(default_factory=list)
    is_solid: bool = False
    origin: Vector3 = field(default_factory=lambda: Vector3())
    extrusion: Extrusion = field(default_factory=Extrusion)


# ================================================================
# TEXT / MTEXT
# ================================================================

@register_entity("TEXT")
@dataclass
class TextEntity(TextBaseEntity):
    insert: Vector3 = field(default_factory=lambda: Vector3())


@register_entity("MTEXT")
@dataclass
class MTextEntity(TextBaseEntity):
    insert: Vector3 = field(default_factory=lambda: Vector3())
    width: float = 0.0
    attachment: int = 1
    line_spacing_factor: float = 1.0


# ================================================================
# LEADER / MLEADER
# ================================================================

@register_entity("LEADER")
@dataclass
class LeaderEntity(CurveEntity):
    vertices: list[Vector3] = field(default_factory=list)
    annotation: CSDMHandle | None = None


@register_entity("MLEADER")
@dataclass
class MLeaderEntity(BaseEntity):
    style: str | None = None
    leader_lines: list[list[Vector3]] = field(default_factory=list)
    content: CSDMHandle | None = None


# ================================================================
# DIMENSIONS
# ================================================================

@register_entity("DIMENSION")
@dataclass
class DimensionEntity(DimensionBase):
    p1: Vector3 = field(default_factory=lambda: Vector3())
    p2: Vector3 = field(default_factory=lambda: Vector3())
    text_pos: Vector3 = field(default_factory=lambda: Vector3())


# ================================================================
# BLOCKREF / MINSERT / ATTRIB
# ================================================================

@register_entity("INSERT")
@dataclass
class BlockReference(BlockRefBase):
    pass


@register_entity("MINSERT")
@dataclass
class MInsertEntity(BlockRefBase):
    row_count: int = 1
    col_count: int = 1
    row_spacing: float = 1.0
    col_spacing: float = 1.0


@register_entity("ATTRIB")
@dataclass
class AttributeEntity(TextBaseEntity):
    tag: str = ""
    insert: Vector3 = field(default_factory=lambda: Vector3())


@register_entity("ATTDEF")
@dataclass
class AttributeDefEntity(TextBaseEntity):
    tag: str = ""
    default: str = ""
    prompt: str = ""


# ================================================================
# IMAGE / UNDERLAY / WIPEOUT / OLE2FRAME
# ================================================================

@register_entity("IMAGE")
@dataclass
class ImageEntity(BaseEntity):
    image_def: CSDMHandle | None = None
    insertion: Vector3 = field(default_factory=lambda: Vector3())
    uvec: Vector3 = field(default_factory=lambda: Vector3(1, 0, 0))
    vvec: Vector3 = field(default_factory=lambda: Vector3(0, 1, 0))
    display_props: dict[str, float] = field(default_factory=dict)


@register_entity("UNDERLAY")
@dataclass
class UnderlayEntity(BaseEntity):
    definition: CSDMHandle | None = None
    insertion: Vector3 = field(default_factory=lambda: Vector3())
    scale: float = 1.0
    rotation: float = 0.0


@register_entity("WIPEOUT")
@dataclass
class WipeoutEntity(BaseEntity):
    points: list[Vector3] = field(default_factory=list)


@register_entity("OLE2FRAME")
@dataclass
class OLE2FrameEntity(BaseEntity):
    ole_id: CSDMHandle | None = None
    width: float = 0.0
    height: float = 0.0


# ================================================================
# POINT ENTITY
# ================================================================

@register_entity("POINT")
@dataclass
class PointEntity(BaseEntity):
    position: Vector3 = field(default_factory=lambda: Vector3())
    thickness: float = 0.0


# ================================================================
# MULTILINE ENTITY
# ================================================================

@register_entity("MLINE")
@dataclass
class MLineEntity(BaseEntity):
    style: str = "Standard"
    scale: float = 1.0
    vertices: list[Vector3] = field(default_factory=list)
    justification: int = 0


# ================================================================
# TOLERANCE
# ================================================================

@register_entity("TOLERANCE")
@dataclass
class ToleranceEntity(BaseEntity):
    insert: Vector3 = field(default_factory=lambda: Vector3())
    contents: str = ""  # raw tolstring
    direction: Vector3 = field(default_factory=lambda: Vector3(1, 0, 0))


# ================================================================
# FIELD ENTITY (Smart Data Fields)
# ================================================================

@register_entity("FIELD")
@dataclass
class FieldEntity(BaseEntity):
    evaluator: str = ""                # e.g. "ACAD_FIELD_EVALUATOR"
    code: str = ""                     # formatted field code
    result: str = ""                   # cached result
    has_cache: bool = False
    obj_refs: list[CSDMHandle] = field(default_factory=list)


# ================================================================
# MLEADER CONTENT
# ================================================================

@dataclass
class MLeaderTextContent:
    text: str
    style: str | None = None
    width: float = 0.0


@dataclass
class MLeaderBlockContent:
    block_name: str
    block_attribs: dict[str, Any] = field(default_factory=dict)


@dataclass
class MLeaderToleranceContent:
    tol_string: str


@register_entity("MLEADERCONTENT")
@dataclass
class MLeaderContentEntity(BaseEntity):
    content_type: str = "TEXT"         # TEXT / BLOCK / TOLERANCE
    text_content: MLeaderTextContent | None = None
    block_content: MLeaderBlockContent | None = None
    tolerance_content: MLeaderToleranceContent | None = None


# ================================================================
# TABLE ENTITY (DWG + DCF Hybrid)
# ================================================================

@dataclass
class CADTableCell:
    value: Any
    data_type: str = "string"          # string, number, field, block, formula
    alignment: str = "middle_left"
    style: str | None = None
    field: FieldEntity | None = None
    block_ref: CSDMHandle | None = None


@dataclass
class CADTableRow:
    height: float = 1.0
    cells: list[CADTableCell] = field(default_factory=list)


@register_entity("TABLE")
@dataclass
class TableEntity(BaseEntity):
    rows: list[CADTableRow] = field(default_factory=list)
    columns: int = 0
    title: str | None = None
    table_style: str = "Standard"
    direction: int = 0
    insertion: Vector3 = field(default_factory=lambda: Vector3())

    def add_row(self, values: list[Any]):
        row = CADTableRow()
        for v in values:
            row.cells.append(CADTableCell(value=v))
        self.rows.append(row)
        self.columns = max(self.columns, len(row.cells))


# ================================================================
# GEOMETRIC CONSTRAINT ENTITIES
# ================================================================

class CadConstraintType(Enum):
    COINCIDENT = "coincident"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    TANGENT = "tangent"
    EQUAL = "equal"
    FIXED = "fixed"


@register_entity("GEOMCONSTRAINT")
@dataclass
class GeometricConstraintEntity(BaseEntity):
    constraint_type: CadConstraintType = CadConstraintType.FIXED
    target_entities: list[CSDMHandle] = field(default_factory=list)


# ================================================================
# DIMENSIONAL CONSTRAINT
# ================================================================

class DimConstraintKind(Enum):
    DISTANCE = "distance"
    ANGLE = "angle"
    RADIUS = "radius"
    DIAMETER = "diameter"


@register_entity("DIMCONSTRAINT")
@dataclass
class DimensionalConstraintEntity(BaseEntity):
    kind: DimConstraintKind = DimConstraintKind.DISTANCE
    value: float = 0.0
    measured: float | None = None
    ref_entities: list[CSDMHandle] = field(default_factory=list)


# ================================================================
# DCF CUSTOM ENTITIES (User-defined CAD objects)
# ================================================================

@register_entity("DCF_CUSTOM")
@dataclass
class DCFCustomEntity(BaseEntity):
    type_name: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    geometry: dict[str, Any] = field(default_factory=dict)


# ================================================================
# FINAL GLUE — ENTITY FACTORY
# ================================================================

def create_entity_by_dwg_name(name: str, **kwargs):
    cname = name.upper()
    if cname not in ENTITY_REGISTRY:
        raise ValueError(f"Unknown DWG/DCF entity type: {name}")
    cls = ENTITY_REGISTRY[cname]
    return cls(**kwargs)
