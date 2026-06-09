"""
ACISWriter
Writes ACIS / SAT / BREP data into DWG objects.
Responsible for:
    - OdDb3dSolid
    - OdDbSurface
    - OdDbBody
    - OdDbRegion
    - Any custom CSDM ACIS object
Runs AFTER:
    - All geometry objects created
    - Registry resolved
Runs BEFORE:
    - Finalizer
"""
from __future__ import annotations
from typing import List, Any
from .base_context import WriterContext
from ....models import csdm_entities as E
from ....models.csdm_core import CSDMObject
class ACISWriter:
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
    # =====================================================================
    # PUBLIC
    # =====================================================================
    def write(self):
        self.ctx.log("Writing ACIS/BREP data...")
        acis_objects = self._collect_acis_objects()
        for csdm_obj in acis_objects:
            oda_obj = self.ctx.resolve(csdm_obj.handle)
            if not oda_obj:
                self.ctx.warn(f"ACIS target missing in registry: {csdm_obj.handle}")
                continue
            data = getattr(csdm_obj, "acis_data", None) or getattr(csdm_obj, "brep_data", None)
            if not data:
                self.ctx.warn(f"No ACIS/BREP data on: {csdm_obj.handle}")
                continue
            self._apply_acis_data(oda_obj, data)
        self.ctx.log("ACIS writing done.")
    # =====================================================================
    # Detect ACIS-bearing objects
    # =====================================================================
    def _collect_acis_objects(self) -> List[CSDMObject]:
        out: List[CSDMObject] = []
        # geometry entities
        for e in self.ctx.csdm_doc.entities:
            if isinstance(e, (E.Solid3DEntity, E.SurfaceACISEntity, E.BodyEntity)) and \
               (hasattr(e, "acis_data") or hasattr(e, "brep_data")):
                out.append(e)
        return out
    # =====================================================================
    # Apply ACIS data to ODA object
    # =====================================================================
    def _apply_acis_data(self, oda_obj: Any, acis_str: str):
        try:
            if hasattr(oda_obj, "loadAcis"):
                oda_obj.loadAcis(acis_str)
                return
            if hasattr(oda_obj, "setAcisStream"):
                oda_obj.setAcisStream(acis_str)
                return
            self.ctx.warn(f"Unsupported ACIS target {type(oda_obj)}")
        except Exception as e:
            self.ctx.error(f"ACIS load failed on {oda_obj}: {e}")
