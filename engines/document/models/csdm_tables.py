# engines/document/models/csdm_tables.py

# csdm_tables.py
# CSDM v2.0 Ultra — Full DWG/DCF Tables
# Requires: csdm_core.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from .csdm_core import (
    CSDMDocument, CSDMObject, CSDMHandle, CSDMEntity,
    CSDMDictionary, CSDMDictionaryEntry,
)

# ============================================
# COMMON BASE FOR ALL TABLE ENTRIES
# ============================================

@dataclass
class TableEntry(CSDMObject):
    name: str = ""
    flags: int = 0


# ============================================
# LAYER TABLE
# ============================================

@dataclass
class LayerEntry(TableEntry):
    color: int = 7
    linetype: str = "CONTINUOUS"
    lineweight: int = -3
    plot: bool = True
    frozen: bool = False
    locked: bool = False
    is_xref: bool = False
    xref_path: Optional[str] = None


@dataclass
class LayerTable(CSDMObject):
    entries: Dict[str, LayerEntry] = field(default_factory=dict)

    def add(self, layer: LayerEntry):
        self.entries[layer.name] = layer


# ============================================
# LINETYPE TABLE
# ============================================

@dataclass
class LinetypeSegment:
    length: float
    shape_index: Optional[int] = None
    text: Optional[str] = None
    style: Optional[str] = None


@dataclass
class LinetypeEntry(TableEntry):
    pattern_length: float = 0.0
    segments: List[LinetypeSegment] = field(default_factory=list)


@dataclass
class LinetypeTable(CSDMObject):
    entries: Dict[str, LinetypeEntry] = field(default_factory=dict)

    def add(self, item: LinetypeEntry):
        self.entries[item.name] = item


# ============================================
# TEXTSTYLE TABLE
# ============================================

@dataclass
class TextStyleEntry(TableEntry):
    font: str = "txt.shx"
    bigfont: Optional[str] = None
    height: float = 0.0
    width_factor: float = 1.0
    oblique: float = 0.0
    vertical: bool = False


@dataclass
class TextStyleTable(CSDMObject):
    entries: Dict[str, TextStyleEntry] = field(default_factory=dict)

    def add(self, style: TextStyleEntry):
        self.entries[style.name] = style


# ============================================
# DIMSTYLE TABLE
# ============================================

class DimLUnit(Enum):
    DECIMAL = 0
    FRACTIONAL = 1
    ARCHITECTURAL = 2
    ENGINEERING = 3


@dataclass
class DimStyleEntry(TableEntry):
    text_height: float = 2.5
    arrow_size: float = 2.5
    ext_line_offset: float = 0.625
    dim_line_gap: float = 0.625
    scale: float = 1.0
    decimal_precision: int = 2
    linear_unit: DimLUnit = DimLUnit.DECIMAL
    prefix: str = ""
    suffix: str = ""


@dataclass
class DimStyleTable(CSDMObject):
    entries: Dict[str, DimStyleEntry] = field(default_factory=dict)

    def add(self, dimstyle: DimStyleEntry):
        self.entries[dimstyle.name] = dimstyle


# ============================================
# UCS TABLE
# ============================================

@dataclass
class UCSRecord(TableEntry):
    origin: Tuple[float, float, float] = (0, 0, 0)
    x_axis: Tuple[float, float, float] = (1, 0, 0)
    y_axis: Tuple[float, float, float] = (0, 1, 0)


@dataclass
class UCSTable(CSDMObject):
    entries: Dict[str, UCSRecord] = field(default_factory=dict)

    def add(self, item: UCSRecord):
        self.entries[item.name] = item


# ============================================
# VIEW TABLE
# ============================================

@dataclass
class ViewRecord(TableEntry):
    center: Tuple[float, float] = (0, 0)
    height: float = 100
    width: float = 100
    direction: Tuple[float, float, float] = (0, 0, 1)
    target: Tuple[float, float, float] = (0, 0, 0)


@dataclass
class ViewTable(CSDMObject):
    entries: Dict[str, ViewRecord] = field(default_factory=dict)

    def add(self, item: ViewRecord):
        self.entries[item.name] = item


# ============================================
# VPORT TABLE
# ============================================

@dataclass
class VPortRecord(TableEntry):
    lower_left: Tuple[float, float] = (0, 0)
    upper_right: Tuple[float, float] = (1, 1)
    view_height: float = 100
    view_center: Tuple[float, float] = (0, 0)
    grid_on: bool = False
    snap_on: bool = False


@dataclass
class VPortTable(CSDMObject):
    entries: Dict[str, VPortRecord] = field(default_factory=dict)

    def add(self, item: VPortRecord):
        self.entries[item.name] = item


# ============================================
# APPID / REGAPP TABLES
# ============================================

@dataclass
class AppIDEntry(TableEntry):
    pass


@dataclass
class AppIDTable(CSDMObject):
    entries: Dict[str, AppIDEntry] = field(default_factory=dict)

    def add(self, item: AppIDEntry):
        self.entries[item.name] = item


# ============================================
# BLOCK RECORD TABLE (ROOT OF ALL BLOCK DEFINITIONS)
# ============================================

@dataclass
class BlockRecord(TableEntry):
    is_xref: bool = False
    xref_path: Optional[str] = None
    units: str = "none"
    allows_exploding: bool = True
    has_preview: bool = False
    layout_handle: Optional[CSDMHandle] = None


@dataclass
class BlockRecordTable(CSDMObject):
    entries: Dict[str, BlockRecord] = field(default_factory=dict)

    def add(self, item: BlockRecord):
        self.entries[item.name] = item


# ============================================
# PLOTSTYLE TABLE
# ============================================

@dataclass
class PlotStyleEntry(TableEntry):
    color: Tuple[int, int, int] = (0, 0, 0)
    lineweight: float = 0.25
    screening: int = 100


@dataclass
class PlotStyleTable(CSDMObject):
    entries: Dict[str, PlotStyleEntry] = field(default_factory=dict)

    def add(self, item: PlotStyleEntry):
        self.entries[item.name] = item


# ============================================
# MATERIAL TABLE (DWG-level — different from Object-level)
# ============================================

@dataclass
class MaterialEntry(TableEntry):
    diffuse: Tuple[float, float, float] = (1, 1, 1)
    specular: Tuple[float, float, float] = (1, 1, 1)
    reflection: float = 0.0
    transparency: float = 0.0
    texture: Optional[str] = None


@dataclass
class MaterialTableDWG(CSDMObject):
    entries: Dict[str, MaterialEntry] = field(default_factory=dict)

    def add(self, item: MaterialEntry):
        self.entries[item.name] = item

# ============================================================
# DIMSTYLE OVERRIDES
# ============================================================

@dataclass
class DimStyleOverride:
    key: str
    value: Any


@dataclass
class DimStyleOverrideTable(CSDMObject):
    overrides: Dict[str, DimStyleOverride] = field(default_factory=dict)

    def set(self, key: str, value):
        self.overrides[key] = DimStyleOverride(key, value)


# ============================================================
# MULTILINE STYLE TABLE (MLINESTYLE)
# ============================================================

@dataclass
class MLineElement:
    offset: float
    color: int
    linetype: str


@dataclass
class MLineStyle(TableEntry):
    elements: List[MLineElement] = field(default_factory=list)
    fill_color: Optional[int] = None
    show_miter_joint: bool = True


@dataclass
class MLineStyleTable(CSDMObject):
    entries: Dict[str, MLineStyle] = field(default_factory=dict)

    def add(self, item: MLineStyle):
        self.entries[item.name] = item


# ============================================================
# FULL TABLESTYLE (for ACAD TABLE object)
# ============================================================

@dataclass
class TableCellStyle:
    text_style: str = "Standard"
    text_height: float = 2.5
    alignment: str = "middle_left"
    fill_color: Optional[int] = None


@dataclass
class CADTableStyle(TableEntry):
    data_cell: TableCellStyle = field(default_factory=TableCellStyle)
    header_cell: TableCellStyle = field(default_factory=TableCellStyle)
    title_cell: TableCellStyle = field(default_factory=TableCellStyle)
    flow_direction: str = "down"
    horz_cell_margin: float = 0.1
    vert_cell_margin: float = 0.1


@dataclass
class TableStyleTable(CSDMObject):
    entries: Dict[str, CADTableStyle] = field(default_factory=dict)

    def add(self, item: CADTableStyle):
        self.entries[item.name] = item


# ============================================================
# FULL MLEADERSTYLE
# ============================================================

class MLeaderTextAlign(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2
    JUSTIFIED = 3


@dataclass
class MLeaderStyle(TableEntry):
    text_style: str = "Standard"
    text_height: float = 2.5
    arrow_size: float = 2.5
    landing_gap: float = 1.0
    leader_type: str = "straight"
    text_align: MLeaderTextAlign = MLeaderTextAlign.LEFT
    dogleg_length: float = 5.0
    max_leaders: int = 1


@dataclass
class MLeaderStyleTable(CSDMObject):
    entries: Dict[str, MLeaderStyle] = field(default_factory=dict)

    def add(self, item: MLeaderStyle):
        self.entries[item.name] = item


# ============================================================
# LIGHTS (for RENDERING)
# ============================================================

class LightType(Enum):
    DISTANT = 0
    POINT = 1
    SPOT = 2


@dataclass
class LightRecord(TableEntry):
    light_type: LightType = LightType.DISTANT
    position: Tuple[float, float, float] = (0, 0, 0)
    target: Tuple[float, float, float] = (0, 0, -1)
    intensity: float = 1.0
    color: Tuple[float, float, float] = (1, 1, 1)
    shadow: bool = False


@dataclass
class LightTable(CSDMObject):
    entries: Dict[str, LightRecord] = field(default_factory=dict)

    def add(self, item: LightRecord):
        self.entries[item.name] = item


# ============================================================
# RENDER ENVIRONMENT TABLE
# ============================================================

@dataclass
class RenderEnvironment(TableEntry):
    background_color: Tuple[float, float, float] = (0, 0, 0)
    enable_fog: bool = False
    fog_density: float = 0.0
    fog_color: Tuple[float, float, float] = (1, 1, 1)


@dataclass
class RenderEnvironmentTable(CSDMObject):
    entries: Dict[str, RenderEnvironment] = field(default_factory=dict)

    def add(self, item: RenderEnvironment):
        self.entries[item.name] = item


# ============================================================
# RENDER SETTINGS TABLE
# ============================================================

@dataclass
class RenderSettings(TableEntry):
    quality: str = "draft"
    exposure: float = 1.0
    indirect_bounce: int = 2
    shadows: bool = False
    output_resolution: Tuple[int, int] = (1920, 1080)


@dataclass
class RenderSettingsTable(CSDMObject):
    entries: Dict[str, RenderSettings] = field(default_factory=dict)

    def add(self, item: RenderSettings):
        self.entries[item.name] = item


# ============================================================
# UNDERLAY DEFINITIONS (PDF/DGN/DWF)
# ============================================================

class UnderlayType(Enum):
    PDF = "pdf"
    DGN = "dgn"
    DWF = "dwf"


@dataclass
class UnderlayDefinition(TableEntry):
    file_path: str = ""
    underlay_type: UnderlayType = UnderlayType.PDF
    contrast: int = 50
    fade: int = 0
    monochrome: bool = False


@dataclass
class UnderlayTable(CSDMObject):
    entries: Dict[str, UnderlayDefinition] = field(default_factory=dict)

    def add(self, item: UnderlayDefinition):
        self.entries[item.name] = item


# ============================================================
# RASTER IMAGE DEFINITIONS
# ============================================================

@dataclass
class RasterImageDef(TableEntry):
    file_path: str = ""
    resolution: Tuple[int, int] = (0, 0)
    units: str = "none"


@dataclass
class RasterImageTable(CSDMObject):
    entries: Dict[str, RasterImageDef] = field(default_factory=dict)

    def add(self, item: RasterImageDef):
        self.entries[item.name] = item


# ============================================================
# PLOT CONFIGURATION TABLE
# ============================================================

@dataclass
class PlotConfig(TableEntry):
    device_name: str = "None"
    paper_size: str = "A4"
    orientation: str = "portrait"
    scale: float = 1.0


@dataclass
class PlotConfigTable(CSDMObject):
    entries: Dict[str, PlotConfig] = field(default_factory=dict)

    def add(self, item: PlotConfig):
        self.entries[item.name] = item


# ============================================================
# OLE / EMBEDDED OBJECT TABLES
# ============================================================

@dataclass
class OLEObject(TableEntry):
    ole_data: bytes = b""
    format: str = ""
    linked_path: Optional[str] = None


@dataclass
class OLETable(CSDMObject):
    entries: Dict[str, OLEObject] = field(default_factory=dict)

    def add(self, item: OLEObject):
        self.entries[item.name] = item


# ============================================================
# DATALINK TABLE (Excel linking)
# ============================================================

@dataclass
class DataLink(TableEntry):
    source_path: str = ""
    range_name: Optional[str] = None
    update_policy: str = "manual"


@dataclass
class DataLinkTable(CSDMObject):
    entries: Dict[str, DataLink] = field(default_factory=dict)

    def add(self, item: DataLink):
        self.entries[item.name] = item


# ============================================================
# DCF EXTENDED TABLE SYSTEM (APPLICATION-LEVEL)
# ============================================================

@dataclass
class DCFTableEntry(TableEntry):
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DCFCustomTable(CSDMObject):
    entries: Dict[str, DCFTableEntry] = field(default_factory=dict)

    def add(self, item: DCFTableEntry):
        self.entries[item.name] = item

# ============================================================
# TABLE COLLECTION — ROOT FOR ALL DWG/DCF TABLE SETS
# ============================================================

@dataclass
class CSDMTableCollection:
    layer: Optional[LayerTable] = None
    linetype: Optional[LinetypeTable] = None
    textstyle: Optional[TextStyleTable] = None
    dimstyle: Optional[DimStyleTable] = None
    dimstyle_override: Optional[DimStyleOverrideTable] = None
    ucs: Optional[UCSTable] = None
    view: Optional[ViewTable] = None
    vport: Optional[VPortTable] = None
    appid: Optional[AppIDTable] = None
    regapp: Optional[AppIDTable] = None
    block_record: Optional[BlockRecordTable] = None
    plotstyle: Optional[PlotStyleTable] = None

    # DWG-level materials (different from CSDMObject.material)
    material: Optional[MaterialTableDWG] = None

    # Advanced DWG
    mlinestyle: Optional[MLineStyleTable] = None
    tablestyle: Optional[TableStyleTable] = None
    mleaderstyle: Optional[MLeaderStyleTable] = None
    light: Optional[LightTable] = None
    render_env: Optional[RenderEnvironmentTable] = None
    render_settings: Optional[RenderSettingsTable] = None
    underlay: Optional[UnderlayTable] = None
    raster: Optional[RasterImageTable] = None
    plotconfig: Optional[PlotConfigTable] = None
    ole: Optional[OLETable] = None
    datalink: Optional[DataLinkTable] = None

    # DCF Extensions
    dcf_tables: Optional[DCFCustomTable] = None

    def create_defaults(self):
        self.layer = LayerTable()
        self.linetype = LinetypeTable()
        self.textstyle = TextStyleTable()
        self.dimstyle = DimStyleTable()
        self.dimstyle_override = DimStyleOverrideTable()
        self.ucs = UCSTable()
        self.view = ViewTable()
        self.vport = VPortTable()
        self.appid = AppIDTable()
        self.regapp = AppIDTable()
        self.block_record = BlockRecordTable()
        self.plotstyle = PlotStyleTable()
        self.material = MaterialTableDWG()

        self.mlinestyle = MLineStyleTable()
        self.tablestyle = TableStyleTable()
        self.mleaderstyle = MLeaderStyleTable()

        self.light = LightTable()
        self.render_env = RenderEnvironmentTable()
        self.render_settings = RenderSettingsTable()

        self.underlay = UnderlayTable()
        self.raster = RasterImageTable()
        self.plotconfig = PlotConfigTable()
        self.ole = OLETable()
        self.datalink = DataLinkTable()

    def register_dcf_table(self, name: str, table: DCFCustomTable):
        self.dcf_tables = table


# ============================================================
# DOCUMENT INTEGRATION
# ============================================================

def _attach_tables_to_document():
    CSDMDocument.tables = CSDMTableCollection()

    def create_standard_tables(self: CSDMDocument):
        self.tables.create_defaults()

    CSDMDocument.create_standard_tables = create_standard_tables


_attach_tables_to_document()


# ============================================================
# FINAL BOOTSTRAP
# ============================================================

def bootstrap_tables():
    doc = CSDMDocument()
    doc.create_standard_tables()
    return doc


