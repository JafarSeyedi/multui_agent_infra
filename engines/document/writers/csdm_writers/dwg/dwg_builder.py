from __future__ import annotations
from typing import Any
from .base_context import WriterContext

class DWGBuilder:
    def __init__(self, ctx: WriterContext):
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg

    def build(self):
        self.ctx.log("Building base DWG structure...")
        self._create_root_dictionaries()
        self._create_tables()
        self._create_default_blocks()
        self._configure_system_vars()
        self.ctx.log("DWG base structure ready.")

    def _create_root_dictionaries(self):
        self.ctx.log("Creating root dictionaries...")
        dicts = self.dwg.getRootDictionary()
        required = [
            "ACAD_GROUP", "ACAD_MLINESTYLE", "ACAD_PLOTSETTINGS",
            "ACAD_PLOTSTYLENAME", "ACAD_SCALELIST", "ACAD_TABLESTYLE",
            "ACAD_MLEADERSTYLE", "ACAD_LAYOUT", "ACAD_VISUALSTYLE",
            "ACAD_LIGHTING", "ACAD_MATERIAL", "ACAD_RENDERSETTINGS",
            "ACAD_RENDERENVIRONMENT", "ACAD_COLOR",
        ]
        for name in required:
            if not dicts.hasEntry(name):
                dicts.createEntry(name)
                self.ctx.log(f"  Root dictionary created: {name}")

    def _create_tables(self):
        self.ctx.log("Creating DWG tables...")
        tables = [
            "LAYER", "LTYPE", "STYLE", "DIMSTYLE", "UCS", "VIEW",
            "VPORT", "BLOCK_RECORD", "APPID", "MLEADERSTYLE",
            "MLINESTYLE", "TABLESTYLE", "LIGHTLIST",
        ]
        for table in tables:
            if not self.dwg.hasTable(table):
                self.dwg.createTable(table)
                self.ctx.log(f"  DWG table created: {table}")

    def _create_default_blocks(self):
        self.ctx.log("Setting up ModelSpace and PaperSpace...")
        block_table = self.dwg.getBlockTable()
        if not block_table.has("ModelSpace"):
            model = block_table.create("ModelSpace", layout="Model")
            self.ctx.register("MODELSPACE", model)
            self.ctx.log("  Created ModelSpace")
        if not block_table.has("PaperSpace"):
            paper = block_table.create("PaperSpace", layout="Paper")
            self.ctx.register("PAPERSPACE", paper)
            self.ctx.log("  Created PaperSpace")

    def _configure_system_vars(self):
        self.ctx.log("Applying DWG system variables...")
        sysvar = self.dwg.setSystemVariable
        sysvar("LTSCALE", 1.0)
        sysvar("CELTSCALE", 1.0)
        sysvar("TEXTSIZE", 2.5)
        sysvar("DIMTXT", 2.5)
        sysvar("MEASUREMENT", 1)
        sysvar("INSUNITS", 4)
        sysvar("LUNITS", 2)
        sysvar("LUPREC", 4)
        sysvar("CELTYPE", "BYLAYER")
        sysvar("CELWEIGHT", -1)
        sysvar("CELTSCALE", 1.0)
        sysvar("PLINEGEN", 1)
        sysvar("SPLFRAME", 0)
        sysvar("HPINHERIT", 1)
        self.ctx.log("  System variables applied.")
