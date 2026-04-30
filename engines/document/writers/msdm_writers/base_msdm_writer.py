# engines/document/writers/msdm_writers/base_msdm_writer.py
"""
Base class for all MSDM format writers.

Extends the generic BaseDocumentWriter with MSDM‑specific helpers:

- **Soft‑delete strategy** – when modifying an existing schema, columns
  and tables that are present in the target but missing from the model
  can be preserved by renaming them (prefix/suffix) or by adding an
  annotation, instead of physically dropping them.

- **Dual‑output mode** – some writers (e.g., SQL DDL) can produce a
  design file *or* apply changes directly to a live database. The
  writer accepts a `target_mode` and, for database targets, an
  optional `connection_config`.

Configuration is passed via the standard `WriteOptions.custom` dict or
through sensible constructor defaults.
"""

from __future__ import annotations
from abc import abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator, Union
from enum import Enum

from pydantic import BaseModel

from ..base import BaseDocumentWriter, WriteOptions
from ...models.msdm_models import MSDMDocument
from ...models.base import BaseDocument


# ── Enumerations ────────────────────────────────────────────────
class WriteTarget(str, Enum):
    """Destination of the writer."""
    DESIGN_FILE = "design_file"   # produce a schema file (.sql, .avsc, etc.)
    DATABASE    = "database"      # apply changes directly to a live database


class SoftDeleteStrategy(str, Enum):
    """How to handle entities/attributes removed from the model."""
    NONE      = "none"       # physically drop / delete (default for file output)
    PREFIX    = "prefix"     # rename with _deleted_ prefix
    SUFFIX    = "suffix"     # rename with _deleted suffix
    ANNOTATE  = "annotate"   # keep as is but mark with an annotation


# ── Optional database connection configuration ───────────────────
class ConnectionConfig(BaseModel):
    """Minimal database connection parameters.

    Extended by concrete writers (e.g., SQLite file path, PostgreSQL
    connection string).  All fields are optional so that each dialect
    can pick what it needs.
    """
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None        # full connection string (e.g. SQLAlchemy)
    extra_args: Dict[str, Any] = {}


# ── Base MSDM Writer ────────────────────────────────────────────
class BaseMSDMWriter(BaseDocumentWriter):
    """
    Common superclass for any writer that serialises an MSDMDocument.

    Subclasses implement:

    - ``_write_design(document) -> bytes``  for file‑based output.
    - ``_apply_to_database(document, connection)``  for live DB, if needed.

    By default ``target_mode = DESIGN_FILE`` and
    ``soft_delete = SoftDeleteStrategy.NONE``.
    """

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options or WriteOptions())
        self.target_mode = target_mode
        self.soft_delete_strategy = soft_delete_strategy

    # ── Core write entry points ─────────────────────────────────
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        data = await self.write(document)
        yield data

    async def write(self, document: BaseDocument) -> bytes:
        """
        By default produces design‑file output.  If the writer does
        not support design output it should raise NotImplementedError.
        """
        if not isinstance(document, MSDMDocument):
            raise TypeError("BaseMSDMWriter expects an MSDMDocument")
        if self.target_mode == WriteTarget.DATABASE:
            raise RuntimeError(
                "Target mode is DATABASE; use apply_to_database() instead of write()"
            )
        return await self._write_design(document)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        data = await self.write(document)
        target.write_bytes(data)

    # ── Database apply (subclasses override) ────────────────────
    async def apply_to_database(
        self,
        document: MSDMDocument,
        connection: Optional[ConnectionConfig] = None,
    ) -> None:
        """
        Apply the model to a live database.  `connection` provides
        the target coordinates; if None the writer may use a default
        from its own configuration.

        The default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support database application"
        )

    # ── Abstracts for concrete writers ──────────────────────────
    @abstractmethod
    async def _write_design(self, document: MSDMDocument) -> bytes:
        """Return the serialised schema as bytes (e.g. SQL DDL script)."""
        ...

    # ── Soft‑delete helpers (optional) ──────────────────────────
    def apply_soft_delete(
        self,
        existing_name: str,
        deleted: bool,
    ) -> str:
        """
        Return the name to use for a table/column that was removed
        from the model, according to the current soft‑delete strategy.

        Args:
            existing_name:  The original name in the target schema.
            deleted:        Whether the object was removed (True) or
                            merely altered (False).

        Returns:
            The name that should be written / preserved.
        """
        if not deleted:
            return existing_name
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            return existing_name   # caller is expected to physically drop
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            return f"_deleted_{existing_name}"
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            return f"{existing_name}_deleted"
        elif self.soft_delete_strategy == SoftDeleteStrategy.ANNOTATE:
            # keep name; the caller should also add an annotation that
            # marks it deleted – this method only returns the name.
            return existing_name
        return existing_name

    # ── Optional meta helpers ───────────────────────────────────
    def get_soft_delete_annotation(self) -> Optional[str]:
        """Return the annotation value that marks an entity/attribute as deleted."""
        if self.soft_delete_strategy == SoftDeleteStrategy.ANNOTATE:
            return "deleted"
        return None