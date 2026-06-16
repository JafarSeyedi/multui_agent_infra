from __future__ import annotations

import json as _json
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

from .._types import VariableValue

logger = logging.getLogger(__name__)


class ToolResult:
    def __init__(self, success: bool, data: VariableValue = None, error: str | None = None) -> None:
        self.success = success
        self.data = data
        self.error = error

    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult(success=True, data={self.data!r})"
        return f"ToolResult(success=False, error={self.error!r})"


class BaseToolExecutor(ABC):
    """Each executor follows the Tool model definition.

    Setup parameters (``Tool.params``) are passed to ``__init__`` and
    configure the executor.  Execution arguments (``Tool.args``) are
    passed to ``execute()`` — never raw ``**kwargs``.
    """

    _kind_registry: dict[Any, type[BaseToolExecutor]] = {}

    @classmethod
    def register(cls, kind: Any):
        """Decorator that registers a subclass for a ToolKind.

        Can be stacked for executors that support multiple kinds::

            @BaseToolExecutor.register(ToolKind.FILE_READ)
            @BaseToolExecutor.register(ToolKind.FILE_WRITE)
            class FileExecutor(BaseToolExecutor):
                ...
        """
        def _wrapper(sub_cls: type[BaseToolExecutor]) -> type[BaseToolExecutor]:
            existing = cls._kind_registry.get(kind)
            if existing is not None and existing is not sub_cls:
                logger.warning(
                    "Overriding executor for %s: %s -> %s",
                    kind, existing.__name__, sub_cls.__name__,
                )
            cls._kind_registry[kind] = sub_cls
            return sub_cls
        return _wrapper

    @classmethod
    def for_kind(cls, kind: Any) -> type[BaseToolExecutor] | None:
        return cls._kind_registry.get(kind)

    def __init__(self, params: list[Any] | None = None) -> None:
        self._params: list[Any] = params or []
        self._apply_params()

    def set_params(self, params: list[Any]) -> None:
        self._params = list(params)
        self._apply_params()

    def _apply_params(self) -> None:
        """Override in subclasses to extract setup values from ``self._params``."""

    @abstractmethod
    async def execute(self, args: list[Any]) -> ToolResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    def param(
        self,
        params: list[Any],
        name: Any,
        default: Any = None,
    ) -> Any:
        for p in params:
            if p.name == name:
                if p.default is None:
                    return default
                return self._convert(p.type, p.default)
        return default

    def arg(
        self,
        args: list[Any],
        name: Any,
        default: Any = None,
    ) -> Any:
        return self.param(args, name, default)

    def _convert(self, ptype: Any, value: str) -> Any:
        if ptype.value == "integer":
            return int(value)
        if ptype.value == "float":
            return float(value)
        if ptype.value == "boolean":
            return value.lower() in ("true", "1", "yes")
        if ptype.value == "json":
            return _json.loads(value)
        return value
