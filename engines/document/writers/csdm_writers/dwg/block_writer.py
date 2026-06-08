"""
BlockWriter
Responsible for building DWG BlockRecords (ModelSpace, PaperSpace, and user-defined blocks)
and populating them with entities using EntityWriter.
Operates AFTER:
    - DWGBuilder created empty BlockTable + initial BlockRecords
    - TableWriter & NonGraphicalWriter populated table objects
Operates BEFORE:
    - Finalizer (which closes/optimizes DB)
This module:
    ✓ Creates all BlockRecords from CSDM Blocks
    ✓ Handles XRef blocks
    ✓ Handles Anonymous blocks
    ✓ Calls EntityWriter for each block's local entities
    ✓ Registers all BlockRecords in context.registry for dependency resolution
"""
from __future__ import annotations
from typing import Dict, Callable, List
from .base_context import WriterContext
from .entity_writer import EntityWriter
from ....models import csdm_entities as E
from ....models import csdm_core as C
class BlockWriter:
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
        # Entity writer for inside blocks
        self.entity_writer = EntityWriter(ctx)
    # =====================================================================
    # PUBLIC API
    # =====================================================================
    def write(self):
        self.ctx.log("Writing BlockRecords...")
        # 1. Create all block records
        self._create_block_records()
        # 2. Populate each block with its entities
        self._write_block_contents()
        self.ctx.log("BlockRecords written.")
    # =====================================================================
    # Step 1: Create BlockRecords
    # =====================================================================
    def _create_block_records(self):
        for blk in self.ctx.csdm_doc.blocks:
            if blk.is_model_space:
                # ModelSpace already exists (created by DWGBuilder)
                rec = self.dwg.modelSpaceRecord()
                self.ctx.register(blk.handle, rec)
                continue
            if blk.is_paper_space:
                # PaperSpace already exists
                rec = self.dwg.paperSpaceRecord()
                self.ctx.register(blk.handle, rec)
                continue
            # ----- USER-DEFINED blocks -----
            rec = self.dwg.newBlockRecord()
            rec.setName(blk.name)
            rec.setAnonymous(blk.is_anonymous)
            # XRef support
            if blk.is_xref:
                rec.setXrefPath(blk.xref_path)
                rec.setXrefType(blk.xref_type)  # Attach / Overlay
            self.ctx.register(blk.handle, rec)
    # =====================================================================
    # Step 2: Write Block Contents
    # =====================================================================
    def _write_block_contents(self):
        """
        For each block, write all entities that belong to it.
        EntityWriter itself takes care of setting owner, layer, xdata, etc.
        """
        for blk in self.ctx.csdm_doc.blocks:
            # resolve its DWG BlockRecord
            rec = self.ctx.resolve(blk.handle)
            if not rec:
                self.ctx.log(f"  ERROR: BlockRecord not found for {blk.name}")
                continue
            # switch context to this block
            with self.ctx.enter_block(rec):
                self._write_entities_in_block(blk)
    def _write_entities_in_block(self, blk):
        """
        Write all entities inside a specific block.
        """
        self.ctx.log(f"    Writing contents of block: {blk.name}")
        # Filter entities that belong to this block
        local_entities = [
            e for e in self.ctx.csdm_doc.entities if e.owner == blk.handle
        ]
        for e in local_entities:
            handler = self.entity_writer._handlers.get(e.type)
            if not handler:
                self.ctx.log(f"      WARNING: Unsupported entity in block: {e.type}")
                continue
            oda_ent = handler(e)
            if oda_ent:
                self.entity_writer._apply_common(e, oda_ent)
                self.ctx.register(e.handle, oda_ent)
        self.ctx.log(f"    Finished block: {blk.name}")
