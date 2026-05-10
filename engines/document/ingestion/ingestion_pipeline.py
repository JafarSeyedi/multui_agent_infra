# engines/document/ingestion/ingestion_pipeline.py
from __future__ import annotations

import logging

from ..models.media_types import MEDIA_TYPES
from .ingestion_context import IngestionContext
from .ingestion_errors import IngestionError
from .ingestion_errors import IngestionStepFailed
from .steps.step_chunk import step_chunk
from .steps.step_embed import step_embed
from .steps.step_extract import step_extract
from .steps.step_parse import step_parse
from .steps.step_store import step_store

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Executes an ordered list of ingestion steps on an IngestionContext.
    A workflow is an ordered list of step names.
    """

    def __init__(self):
        # static registry of built-in step functions
        self._step_map = {
            "extract": step_extract,
            "parse": step_parse,
            "chunk": step_chunk,
            "embed": step_embed,
            "store": step_store,
        }

    # ---------------------------------------------------------------------
    async def run(
        self,
        ctx: IngestionContext,
        workflow: list[str],
    ) -> IngestionContext:
        """
        Executes the given workflow steps sequentially on the provided context.
        """

        if not workflow:
            raise IngestionError("Workflow steps list is empty")

        # ensure media_type consistency (lookup if string)
        if isinstance(ctx.media_type, str):
            key = ctx.media_type.lower()
            if key in MEDIA_TYPES:
                ctx.media_type = MEDIA_TYPES[key]
            else:
                raise IngestionError(f"Unknown media_type: {ctx.media_type}")

        for step_name in workflow:
            step = self._step_map.get(step_name)
            if step is None:
                raise IngestionError(f"Unknown step: {step_name}")

            try:
                logger.debug(f"[INGESTION] → Running step '{step_name}' for {ctx.filename}")
                ctx = await step(ctx)
            except Exception as exc:
                logger.exception(f"[INGESTION] Step '{step_name}' failed")
                raise IngestionStepFailed(step_name, exc) from exc

        logger.info(f"[INGESTION] Pipeline finished successfully for {ctx.filename}")

        if ctx.document_record is None:
            raise IngestionError("Finalize step did not produce a DocumentRecord")

        return ctx
