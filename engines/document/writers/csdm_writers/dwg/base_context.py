import os
import time
import logging
from typing import Any, Dict, Optional
from ....parsers.csdm_parsers.oda_bridge import ODABridge
from ....models.csdm_core import CSDMDocument

class WriterContext:
    def __init__(self, csdm_doc: CSDMDocument):
        self.csdm_doc = csdm_doc
        self.oda: Optional[ODABridge] = None
        self.dwg: Optional[Any] = None
        self.registry: Dict[str, Any] = {}
        self.logger = logging.getLogger("CSDMWriter")
        self.time_start: float = 0.0

    def start(self):
        self.time_start = time.time()
        self.logger.info("[WriterContext] Creating ODA DWG document...")
        self.oda = ODABridge()
        self.dwg = self.oda.create_new_document()
        self.logger.info("[WriterContext] ODA document created.")

    def end(self):
        elapsed = time.time() - self.time_start
        self.logger.info(f"[WriterContext] Writer pipeline finished in {elapsed:.3f}s")

    def register(self, handle: str, oda_obj: Any):
        self.registry[handle] = oda_obj

    def resolve(self, handle: str) -> Optional[Any]:
        return self.registry.get(handle)

    def log(self, msg: str):
        self.logger.info("[Writer] " + msg)

    def warn(self, msg: str):
        self.logger.warning("[Writer][WARN] " + msg)

    def error(self, msg: str):
        self.logger.error("[Writer][ERR] " + msg)
