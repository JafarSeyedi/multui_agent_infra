# import os
# import time
# import logging
# from typing import Any, Dict, Optional
# from ...parsers.cad_parser.oda_bridge import ODABridge
# from ...models.base.csdm_core import CSDMDocument
# class WriterContext:
#     """
#     Shared writer context for the entire CAD writer pipeline.
#     This is NOT a writer by itself.
#     It is a support object used by the actual BaseDocumentWriter subclass.
#     Responsibilities:
#         - Instantiate/load ODA document
#         - Maintain registry of handle -> ODA object
#         - Provide logging utilities
#         - Track writer pipeline timing
#     """
#     def __init__(self, csdm_doc: CSDMDocument):
#         self.csdm_doc = csdm_doc
#         # ODA members
#         self.oda: Optional[ODABridge] = None
#         self.dwg: Optional[Any] = None
#         # Handle registry
#         self.registry: Dict[str, Any] = {}
#         # Logging
#         self.logger = logging.getLogger("CSDMWriter")
#         self.time_start: float = 0.0
#     # -------------------------------------------------------------
#     # ODA lifecycle
#     # -------------------------------------------------------------
#     def start(self):
#         """Initialize ODA and create a fresh DWG document."""
#         self.time_start = time.time()
#         self.logger.info("[WriterContext] Creating ODA DWG document...")
#         self.oda = ODABridge()
#         self.dwg = self.oda.create_new_document()
#         self.logger.info("[WriterContext] ODA document created.")
#     def end(self):
#         """Called after DWG writing ends (timer/log only)."""
#         elapsed = time.time() - self.time_start
#         self.logger.info(f"[WriterContext] Writer pipeline finished in {elapsed:.3f}s")
#     # -------------------------------------------------------------
#     # Registry utilities
#     # -------------------------------------------------------------
#     def register(self, handle: str, oda_obj: Any):
#         """Register ODA object by its DWG handle."""
#         self.registry[handle] = oda_obj
#     def resolve(self, handle: str) -> Optional[Any]:
#         """Resolve a registered DWG object by handle."""
#         return self.registry.get(handle)
#     # -------------------------------------------------------------
#     # Logging helpers
#     # -------------------------------------------------------------
#     def log(self, msg: str):
#         self.logger.info("[Writer] " + msg)
#     def warn(self, msg: str):
#         self.logger.warning("[Writer][WARN] " + msg)
#     def error(self, msg: str):
#         self.logger.error("[Writer][ERR] " + msg)
