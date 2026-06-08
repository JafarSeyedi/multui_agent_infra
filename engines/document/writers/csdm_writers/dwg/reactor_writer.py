"""
ReactorWriter
Responsible for writing all DWG reactors from CSDMDocument.
Reactors allow DWG objects to respond automatically to events such as:
    - object modified
    - erased
    - appended
    - database changes
Runs AFTER:
    - All DWG objects (Blocks, Entities, Dictionaries, Tables, etc.) exist
    - Registry is fully populated
Runs BEFORE:
    - Finalizer
"""
from __future__ import annotations
from typing import Any
from .base_context import WriterContext
from ....models.csdm_core import ReactorLink
class ReactorWriter:
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
    # =====================================================================
    # PUBLIC API
    # =====================================================================
    def write(self):
        self.ctx.log("Writing DWG reactors...")
        # Iterate over all ODA objects we created earlier
        for handle, oda_obj in self.ctx.registry.items():
            # find the original CSDM object by its handle
            csdm_obj = self.ctx.csdm_doc.find_object_by_handle(handle)
            if not csdm_obj:
                continue
            if hasattr(csdm_obj, "reactors") and csdm_obj.reactors:
                for reactor_link in csdm_obj.reactors:
                    self._attach_reactor(oda_obj, reactor_link)
        self.ctx.log("DWG reactors written.")
    # =====================================================================
    # Attach reactor
    # =====================================================================
    def _attach_reactor(self, owner_obj: Any, reactor_link: ReactorLink):
        try:
            target = self.ctx.resolve(reactor_link.target)
            if not target:
                self.ctx.warn(f"Reactor target not found: {reactor_link.target}")
                return
            if hasattr(owner_obj, "addReactor"):
                owner_obj.addReactor(target)
            else:
                self.ctx.warn(f"Object cannot accept reactors: {owner_obj}")
        except Exception as e:
            self.ctx.error(f"Failed to attach reactor: {e}")
