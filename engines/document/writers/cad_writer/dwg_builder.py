# """
# DWG Builder for CSDM v2.0 Ultra
# Responsible for creating the initial DWG structure in ODA:
#     - Root database
#     - System dictionaries
#     - All core DWG tables (Layers, Linetypes, TextStyles, DimStyles, etc.)
#     - ModelSpace, PaperSpace
#     - System variables
#     - Default records
# This prepares the DWG before TableWriter, EntityWriter, BlockWriter, etc.
# """
# from __future__ import annotations
# from typing import Any
# from .base_context import WriterContext
# class DWGBuilder:
#     """
#     Responsible for building the initial DWG scaffolding according to
#     CSDM v2.0 Ultra requirements.
#     NOTE:
#     Only builds the structural DWG components.
#     Population of records happens in table_writer.py, entity_writer.py, etc.
#     """
#     def __init__(self, ctx: WriterContext):
#         self.ctx = ctx
#         self.oda = ctx.oda
#         self.dwg = ctx.dwg
#     # ==================================================================
#     # Public API
#     # ==================================================================
#     def build(self):
#         self.ctx.log("Building base DWG structure...")
#         self._create_root_dictionaries()
#         self._create_tables()
#         self._create_default_blocks()
#         self._configure_system_vars()
#         self.ctx.log("DWG base structure ready.")
#     # ==================================================================
#     # Root Dictionaries
#     # ==================================================================
#     def _create_root_dictionaries(self):
#         """
#         Ensures all root dictionaries required by the DWG standard exist.
#         Many writers (XDataWriter, ReactorWriter, ACISWriter) depend on these.
#         """
#         self.ctx.log("Creating root dictionaries...")
#         dicts = self.dwg.getRootDictionary()
#         required = [
#             "ACAD_GROUP",
#             "ACAD_MLINESTYLE",
#             "ACAD_PLOTSETTINGS",
#             "ACAD_PLOTSTYLENAME",
#             "ACAD_SCALELIST",
#             "ACAD_TABLESTYLE",
#             "ACAD_MLEADERSTYLE",
#             "ACAD_LAYOUT",
#             "ACAD_VISUALSTYLE",
#             "ACAD_LIGHTING",
#             "ACAD_MATERIAL",
#             "ACAD_RENDERSETTINGS",
#             "ACAD_RENDERENVIRONMENT",
#             "ACAD_COLOR",
#         ]
#         for name in required:
#             if not dicts.hasEntry(name):
#                 dicts.createEntry(name)
#                 self.ctx.log(f"  Root dictionary created: {name}")
#     # ==================================================================
#     # DWG Tables
#     # ==================================================================
#     def _create_tables(self):
#         """
#         Create all DWG tables required for CSDM v2.
#         Writers will populate these later.
#         """
#         self.ctx.log("Creating DWG tables...")
#         tables = [
#             "LAYER",
#             "LTYPE",
#             "STYLE",
#             "DIMSTYLE",
#             "UCS",
#             "VIEW",
#             "VPORT",
#             "BLOCK_RECORD",
#             "APPID",
#             "MLEADERSTYLE",
#             "MLINESTYLE",
#             "TABLESTYLE",
#             "LIGHTLIST",
#         ]
#         for table in tables:
#             if not self.dwg.hasTable(table):
#                 self.dwg.createTable(table)
#                 self.ctx.log(f"  DWG table created: {table}")
#     # ==================================================================
#     # Block Table (ModelSpace / PaperSpace)
#     # ==================================================================
#     def _create_default_blocks(self):
#         """
#         Creates the mandatory block table records:
#             - *Model_Space
#             - *Paper_Space
#         Additional layouts and viewports will be written by LayoutWriter.
#         """
#         self.ctx.log("Setting up ModelSpace and PaperSpace...")
#         block_table = self.dwg.getBlockTable()
#         # Model Space
#         if not block_table.has("ModelSpace"):
#             model = block_table.create("ModelSpace", layout="Model")
#             self.ctx.register("MODELSPACE", model)
#             self.ctx.log("  Created ModelSpace")
#         # Paper Space
#         if not block_table.has("PaperSpace"):
#             paper = block_table.create("PaperSpace", layout="Paper")
#             self.ctx.register("PAPERSPACE", paper)
#             self.ctx.log("  Created PaperSpace")
#     # ==================================================================
#     # System Variables
#     # ==================================================================
#     def _configure_system_vars(self):
#         """
#         Sets DWG system variables that must be initialized before writing content.
#         These match Autodesk’s baseline, ODA draw standards, and CSDM required fields.
#         """
#         self.ctx.log("Applying DWG system variables...")
#         sysvar = self.dwg.setSystemVariable
#         # Basic drawing properties
#         sysvar("LTSCALE", 1.0)
#         sysvar("CELTSCALE", 1.0)
#         sysvar("TEXTSIZE", 2.5)
#         sysvar("DIMTXT", 2.5)
#         # Measurement settings
#         sysvar("MEASUREMENT", 1)  # metric
#         # Units
#         sysvar("INSUNITS", 4)      # mm
#         sysvar("LUNITS", 2)        # decimal units
#         sysvar("LUPREC", 4)        # precision
#         # Display settings
#         sysvar("CELTYPE", "BYLAYER")
#         sysvar("CELWEIGHT", -1)
#         sysvar("CELTSCALE", 1.0)
#         # View/control
#         sysvar("PLINEGEN", 1)
#         sysvar("SPLFRAME", 0)
#         sysvar("HPINHERIT", 1)
#         self.ctx.log("  System variables applied.")
