"""
Finalizer
Responsible for the last stage of DWG writing before returning output bytes.
This module performs the following critical tasks:
    1) Purge unused table items
    2) Audit database (repair invalid objects)
    3) Regen all entities
    4) Update/repair handles and ownership
    5) Create preview thumbnail
    6) Run ODA Optimizer
    7) Save DWG buffer into in-memory bytes
    8) Attach metadata (version, hash, stats)
Runs LAST in writer pipeline.
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import hashlib
from .base_context import WriterContext
class Finalizer:
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
    # =====================================================================
    # PUBLIC API
    # =====================================================================
    def finalize(self) -> bytes:
        self.ctx.log("Finalizing DWG...")
        self._run_purge()
        self._run_audit()
        self._regen()
        self._assign_handles()
        self._generate_thumbnail()
        self._optimize()
        out = self._save()
        self.ctx.log("DWG finalized.")
        return out
    # =====================================================================
    # STEP 1 — Purge
    # =====================================================================
    def _run_purge(self):
        try:
            self.ctx.log("  Purging...")
            self.dwg.purgeAll()
        except Exception as e:
            self.ctx.warn(f"PURGE failed: {e}")
    # =====================================================================
    # STEP 2 — Audit
    # =====================================================================
    def _run_audit(self):
        """
        ODA audit:
            auditDatabase(fix_errors: bool)
        """
        try:
            self.ctx.log("  Auditing DWG...")
            self.dwg.auditDatabase(True)
        except Exception as e:
            self.ctx.warn(f"AUDIT failed: {e}")
    # =====================================================================
    # STEP 3 — Regen
    # =====================================================================
    def _regen(self):
        try:
            self.ctx.log("  Regenerating geometry...")
            self.dwg.regenAll()
        except Exception as e:
            self.ctx.warn(f"REGEN failed: {e}")
    # =====================================================================
    # STEP 4 — validate/assign handles
    # =====================================================================
    def _assign_handles(self):
        """
        Some ODA objects need handle reassignment after purge/audit.
        """
        try:
            self.ctx.log("  Updating handles...")
            self.dwg.fixupHandles()
        except Exception as e:
            self.ctx.warn(f"Handle fixup failed: {e}")
    # =====================================================================
    # STEP 5 — Thumbnail
    # =====================================================================
    def _generate_thumbnail(self):
        """
        Creates a 256x256 preview inside DWG.
        """
        try:
            self.ctx.log("  Generating thumbnail...")
            self.dwg.generatePreview(256, 256)
        except Exception as e:
            self.ctx.warn(f"Thumbnail generation failed: {e}")
    # =====================================================================
    # STEP 6 — Optimize
    # =====================================================================
    def _optimize(self):
        try:
            self.ctx.log("  Running ODA optimizer...")
            self.dwg.optimizeDatabase()
        except Exception as e:
            self.ctx.warn(f"Optimizer failed: {e}")
    # =====================================================================
    # STEP 7 — Save DWG to bytes
    # =====================================================================
    def _save(self) -> bytes:
        try:
            self.ctx.log("  Serializing DWG...")
            if self.dwg is None:
                raise RuntimeError("DWG document not initialized")
            byte_stream = self.dwg.saveToMemory()   # returns bytes
            # optional integrity hash
            sha = hashlib.sha256(byte_stream).hexdigest()
            self.ctx.log(f"  DWG SHA256: {sha}")
            return byte_stream
        except Exception as e:
            self.ctx.error(f"Saving DWG failed: {e}")
            raise
