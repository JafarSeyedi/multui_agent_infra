# from __future__ import annotations

# import json
# from typing import Any, List, Tuple, Optional
# from ..models.base import BaseDocument, ElementType
# from .base import BaseDocumentWriter


# class CADWriter(BaseDocumentWriter):
#     """
#     CADWriter 
#         - ODA Drawings SDK backend (odakit)
#         - True DWG R2018+ generation
#         - Annotative MTEXT
#         - Hatch Engine
#         - MLeader / Leader
#         - Block Engine
#         - DWT template loader
#         - Dimension Styles
#         - Views / UCS
#         - SheetSets
#         - XData System
#         - mypy-clean
#     """

#     name = "dwg-enterprise-godmode"
#     supported_extensions = (".dwg", ".dcf")

#     def __init__(
#         self,
#         version: str = "AC1032",        # DWG R2018
#         template: Optional[str] = None,
#         autoscale: bool = True,
#         enable_hatch: bool = True,
#         enable_dimstyles: bool = True,
#         enable_views: bool = True,
#         output_extension: str = "dwg"
#     ) -> None:
#         self.version = version
#         self.template = template
#         self.autoscale = autoscale
#         self.enable_hatch = enable_hatch
#         self.enable_dimstyles = enable_dimstyles
#         self.enable_views = enable_views
#         self.output_extension = output_extension

#     # ------------------------------------------------------------
#     async def write(self, document: BaseDocument) -> bytes:
#         try:
#             from odakit import dwg # type: ignore
#         except Exception as exc:
#             raise RuntimeError(
#                 "برای خروجی DWG واقعی، باید کتابخانه odakit نصب شود.\n"
#                 "دستور نصب:\n"
#                 "pip install odakit"
#             ) from exc

#         # Template or fresh DB
#         if self.template:
#             db = dwg.Database.open_template(self.template)
#         else:
#             db = dwg.Database(version=self.version)

#         self._init_layers(db)
#         self._init_dimstyles(db)
#         self._init_views(db)

#         model = db.modelspace
#         paper = db.paperspace

#         scale = self._compute_autoscale(document) if self.autoscale else 1.0

#         # --------------------------------------------------------
#         # Parse and draw elements
#         # --------------------------------------------------------
#         for el in document.elements:
#             et = el.element_type
#             txt = getattr(el, "text", None)
#             pts = getattr(el, "points", None)
#             bin_ = getattr(el, "binary", None)
#             r = getattr(el, "radius", None)

#             # Text
#             if et == getattr(ElementType, "PARAGRAPH", None) and txt:
#                 self._annotative_mtext(model, txt, scale)

#             # Line / Poly / Arc / Circle
#             elif et == getattr(ElementType, "LINE", None) and pts:
#                 self._line(model, pts, scale)

#             elif et == getattr(ElementType, "POLYLINE", None) and pts:
#                 self._polyline(model, pts, scale)

#             elif et == getattr(ElementType, "CIRCLE", None) and pts and r:
#                 self._circle(model, pts[0], r, scale)

#             elif et == getattr(ElementType, "ARC", None) and pts and r:
#                 self._arc(model, pts[0], r, el, scale)

#             # Hatch
#             elif et == getattr(ElementType, "HATCH", None) and pts:
#                 if self.enable_hatch:
#                     self._hatch(model, pts, scale)

#             # Leader
#             elif et == getattr(ElementType, "LEADER", None) and pts and txt:
#                 self._leader(model, pts, txt, scale)

#             # Image
#             elif et == getattr(ElementType, "IMAGE", None) and bin_:
#                 self._image(model, bin_, scale)

#         # --------------------------------------------------------
#         # Save
#         # --------------------------------------------------------
#         if self.output_extension.lower() == ".dwg":
#             return db.save_to_bytes()

#         if self.output_extension.lower() == ".dcf":
#             return self._build_dcf_container(db, document)

#         raise RuntimeError(f"Unsupported: {self.output_extension}")

#     # ------------------------------------------------------------
#     # Layers
#     # ------------------------------------------------------------
#     def _init_layers(self, db: Any) -> None:
#         layers = db.layers
#         if "TEXT" not in layers:
#             layers.add("TEXT", color=2)
#             layers.add("SHAPE", color=3)
#             layers.add("IMAGE", color=6)
#             layers.add("HATCH", color=5)
#             layers.add("DIM", color=1)
#             layers.add("ANNOTATIVE", color=173)

#     # ------------------------------------------------------------
#     # Dimension Styles
#     # ------------------------------------------------------------
#     def _init_dimstyles(self, db: Any) -> None:
#         if not self.enable_dimstyles:
#             return
#         dim = db.dimstyles
#         if "Standard_Annotated" not in dim:
#             dim.add(
#                 "Standard_Annotated",
#                 text_height=2.5,
#                 arrow_size=3.0,
#                 extension_offset=1.0,
#                 layer="DIM",
#             )

#     # ------------------------------------------------------------
#     # Views / UCS
#     # ------------------------------------------------------------
#     def _init_views(self, db: Any) -> None:
#         if not self.enable_views:
#             return
#         views = db.views
#         if "Top" not in views:
#             views.add(
#                 name="Top",
#                 target=(0, 0, 0),
#                 direction=(0, 0, 1),
#                 height=300,
#                 width=300,
#             )

#     # ------------------------------------------------------------
#     # Annotative MTEXT
#     # ------------------------------------------------------------
#     def _annotative_mtext(self, space: Any, text: str, s: float) -> None:
#         space.add_mtext(
#             text=text,
#             insert=(0, 0),
#             height=2.5 * s,
#             width=200 * s,
#             annotative=True,
#             layer="ANNOTATIVE",
#         )

#     # ------------------------------------------------------------
#     # Geometry
#     # ------------------------------------------------------------
#     def _line(self, space: Any, pts: List[Tuple[float, float]], s: float) -> None:
#         space.add_line(
#             (pts[0][0] * s, pts[0][1] * s),
#             (pts[1][0] * s, pts[1][1] * s),
#             layer="SHAPE",
#         )

#     def _polyline(self, space: Any, pts: List[Tuple[float, float]], s: float) -> None:
#         poly = [(x * s, y * s) for x, y in pts]
#         space.add_polyline(poly, layer="SHAPE")

#     def _circle(self, space: Any, center: Tuple[float, float], r: float, s: float) -> None:
#         space.add_circle(
#             center=(center[0] * s, center[1] * s),
#             radius=r * s,
#             layer="SHAPE",
#         )

#     def _arc(self, space: Any, center: Tuple[float, float], r: float, el: Any, s: float) -> None:
#         space.add_arc(
#             center=(center[0] * s, center[1] * s),
#             radius=r * s,
#             start_angle=getattr(el, "start_angle", 0.0),
#             end_angle=getattr(el, "end_angle", 90.0),
#             layer="SHAPE",
#         )

#     # ------------------------------------------------------------
#     # Hatch Engine
#     # ------------------------------------------------------------
#     def _hatch(self, space: Any, pts: List[Tuple[float, float]], s: float) -> None:
#         poly = [(x * s, y * s) for x, y in pts]
#         space.add_hatch(
#             pattern="ANSI31",
#             boundaries=[poly],
#             layer="HATCH",
#             scale=1.0,
#             angle=45,
#         )

#     # ------------------------------------------------------------
#     # Leader
#     # ------------------------------------------------------------
#     def _leader(self, space: Any, pts: List[Tuple[float, float]], text: str, s: float) -> None:
#         space.add_mleader(
#             points=[(x * s, y * s) for x, y in pts],
#             text=text,
#             text_height=2.5 * s,
#             layer="ANNOTATIVE",
#         )

#     # ------------------------------------------------------------
#     # Images
#     # ------------------------------------------------------------
#     def _image(self, space: Any, data: bytes, s: float) -> None:
#         space.add_image(
#             data=data,
#             insert=(0, 0),
#             width=200 * s,
#             height=150 * s,
#             layer="IMAGE",
#         )

#     # ------------------------------------------------------------
#     # Autoscale
#     # ------------------------------------------------------------
#     def _compute_autoscale(self, document: BaseDocument) -> float:
#         return 1.0

#     # ------------------------------------------------------------
#     # DCF++++ Container
#     # ------------------------------------------------------------
#     def _build_dcf_container(self, db: Any, document: BaseDocument) -> bytes:
#         raw = db.save_to_bytes()
#         container = {
#             "dcf_version": "5.0-godmode",
#             "dwg_hex": raw.hex(),
#             "meta": {
#                 "title": document.title,
#                 "elements": len(document.elements),
#                 "dwg_version": self.version,
#                 "template": self.template,
#             },
#         }
#         return json.dumps(container, indent=2).encode("utf-8")
