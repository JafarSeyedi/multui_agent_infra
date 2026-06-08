from __future__ import annotations
import traceback
from typing import Any

from ....models.base import BaseDocument
from ....models.csdm_core import CSDMDocument
from .base_context import WriterContext
from .dwg_builder import DWGBuilder
from .table_writer import TableWriter
from .non_graphical_writer import NonGraphicalWriter
from .block_writer import BlockWriter
from .entity_writer import EntityWriter
from .xdata_writer import XDataWriter
from .reactor_writer import ReactorWriter
from .acis_writer import ACISWriter
from .finalizer import Finalizer


class DWGPipeline:
    def __init__(self, csdm_doc: CSDMDocument):
        self.csdm_doc = csdm_doc

    def run(self) -> bytes:
        ctx = None
        try:
            ctx = WriterContext(self.csdm_doc)
            ctx.log("=== Starting DWG generation pipeline ===")
            DWGBuilder(ctx).build()
            TableWriter(ctx).write()
            NonGraphicalWriter(ctx).write()
            BlockWriter(ctx).write()
            EntityWriter(ctx).write()
            XDataWriter(ctx).write()
            ReactorWriter(ctx).write()
            ACISWriter(ctx).write()
            finalizer = Finalizer(ctx)
            output_bytes = finalizer.finalize()
            ctx.log("=== DWG pipeline successfully completed ===")
            return output_bytes
        except Exception as e:
            err_msg = f"DWG pipeline failed: {e}\n{traceback.format_exc()}"
            if ctx:
                ctx.error(err_msg)
            else:
                print(err_msg)
            raise
        finally:
            if ctx:
                try:
                    ctx.end()
                except Exception:
                    pass
