# engines/document/parsers/csdm_parsers/oda_bridge.py
from __future__ import annotations
import io
import traceback
from dataclasses import dataclass
from typing import Any
from collections.abc import Iterable
import odapython as oda  # type: ignore[import-not-found]

@dataclass(frozen=True)
class ODAHandle:
    raw: str
    def __str__(self) -> str:
        return self.raw
    @staticmethod
    def from_obj(obj: Any) -> ODAHandle:
        try:
            h = obj.objectId().getHandle().ascii()
            return ODAHandle(h)
        except Exception:
            return ODAHandle("0")

class ODAObjectProxy:
    def __init__(self, obj: Any):
        self._obj = obj
    @property
    def handle(self) -> ODAHandle:
        return ODAHandle.from_obj(self._obj)
    @property
    def object_id(self) -> Any:
        try:
            return self._obj.objectId()
        except Exception:
            return None
    @property
    def object_class(self) -> str:
        try:
            return self._obj.isA().name()
        except Exception:
            return "Unknown"
    @property
    def owner_id(self) -> str | None:
        try:
            return self._obj.ownerId().getHandle().ascii()
        except Exception:
            return None
    def has_xdata(self) -> bool:
        try:
            return self._obj.hasXData()
        except Exception:
            return False
    def read_xdata(self) -> dict[str, Any]:
        if not self.has_xdata():
            return {}
        out: dict[str, Any] = {}
        try:
            xdata_dict = self._obj.xDataDictionary()
            if xdata_dict is None:
                return {}
            it = xdata_dict.newIterator()
            while not it.done():
                key = it.key()
                val = it.object()
                try:
                    out[key] = str(val)
                except Exception:
                    out[key] = "UNKNOWN"
                it.next()
        except Exception:
            pass
        return out
    def __repr__(self):
        return f"<ODAObjectProxy {self.object_class} {self.handle}>"

class ODADocumentHandle:
    def __init__(self, db: Any):
        self.db = db
    def list_tables(self) -> dict[str, list[ODAObjectProxy]]:
        return {
            "layers": self._extract_table(oda.OdDbLayerTable),
            "linetypes": self._extract_table(oda.OdDbLinetypeTable),
            "text_styles": self._extract_table(oda.OdDbTextStyleTable),
            "dim_styles": self._extract_table(oda.OdDbDimStyleTable),
            "ucs": self._extract_table(oda.OdDbUCSTable),
            "views": self._extract_table(oda.OdDbViewTable),
            "vports": self._extract_table(oda.OdDbViewportTable),
            "block_records": self._extract_table(oda.OdDbBlockTable),
            "appids": self._extract_table(oda.OdDbRegAppTable),
        }
    def _extract_table(self, table_type: Any) -> list[ODAObjectProxy]:
        out: list[ODAObjectProxy] = []
        try:
            table_id = self.db.getSymbolTableId(table_type.desc())
            table = table_id.safeOpenObject()
            it = table.newIterator()
            while not it.done():
                record = it.getRecordId().safeOpenObject()
                out.append(ODAObjectProxy(record))
                it.step()
        except Exception:
            pass
        return out
    def list_block_records(self) -> list[ODAObjectProxy]:
        try:
            blk_id = self.db.getSymbolTableId(oda.OdDbBlockTable.desc())
            blk = blk_id.safeOpenObject()
        except Exception:
            return []
        results: list[ODAObjectProxy] = []
        it = blk.newIterator()
        while not it.done():
            try:
                rec = it.getRecordId().safeOpenObject()
                results.append(ODAObjectProxy(rec))
            except Exception:
                pass
            it.step()
        return results
    def list_entities_in_block(self, block_record: ODAObjectProxy) -> list[ODAObjectProxy]:
        out: list[ODAObjectProxy] = []
        try:
            blk = block_record._obj
            it = blk.newIterator()
            while not it.done():
                try:
                    ent = it.entity().safeOpenObject()
                    out.append(ODAObjectProxy(ent))
                except Exception:
                    pass
                it.step()
        except Exception:
            pass
        return out
    def list_root_dictionary(self) -> dict[str, ODAObjectProxy]:
        out: dict[str, ODAObjectProxy] = {}
        try:
            dict_id = self.db.objectDictionary()
            root = dict_id.safeOpenObject()
            it = root.newIterator()
            while not it.done():
                key = it.name()
                obj = it.objectId().safeOpenObject()
                out[key] = ODAObjectProxy(obj)
                it.next()
        except Exception:
            pass
        return out
    def list_xrefs(self) -> list[ODAObjectProxy]:
        out: list[ODAObjectProxy] = []
        try:
            xref_dict = self.db.getXRefGraph()
            for i in range(xref_dict.numNodes()):
                try:
                    node = xref_dict.node(i)
                    id_ = node.database().ownerId()
                    out.append(ODAObjectProxy(id_.safeOpenObject()))
                except Exception:
                    pass
        except Exception:
            pass
        return out
    def extract_geometry(self, obj: ODAObjectProxy) -> dict[str, Any]:
        try:
            o = obj._obj
            if hasattr(o, "shells"):
                return {"type": "3d_solid", "acis_data": "raw_solid"}
            if hasattr(o, "mesh"):
                return {"type": "mesh", "faces": o.numFaces()}
            if hasattr(o, "get_A_database"):
                return {"type": "generic_geom"}
        except Exception:
            pass
        return {}
    def extract_reactors(self, obj: ODAObjectProxy) -> list[ODAHandle]:
        out: list[ODAHandle] = []
        try:
            ids = obj._obj.getPersistentReactors()
            for rid in ids:
                try:
                    h = rid.getHandle().ascii()
                    out.append(ODAHandle(h))
                except Exception:
                    pass
        except Exception:
            pass
        return out

class ODABridge:
    def __init__(self):
        self.services = oda.OdRxServices()
    def load_bytes(self, data: bytes) -> ODADocumentHandle:
        try:
            db = oda.OdDbDatabase.createDatabase()
            strm = oda.OdMemoryStream()
            strm.setData(data)
            db.readFile(strm)
            return ODADocumentHandle(db)
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Failed to load DWG data from bytes: {e}")
    def load_file(self, path: str) -> ODADocumentHandle:
        try:
            db = oda.OdDbDatabase.readFile(path)
            return ODADocumentHandle(db)
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Failed to load DWG file '{path}': {e}")
