from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from engines.session.models import Session
from engines.session.service import BaseSessionService


@dataclass
class CallbackContext:
    agent_name: str
    agent_id: str
    session: Session | None = None
    session_service: BaseSessionService | None = None
    invocation_id: str = ""
    state: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.session is not None and not self.state:
            self.state = self.session.state


@dataclass
class LlmRequest:
    contents: list[dict[str, Any]] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class LlmResponse:
    content: dict[str, Any] | None = None
    text: str = ""


@dataclass
class ToolContext(CallbackContext):
    tool_name: str = ""


BeforeAgentCallback = Callable[[CallbackContext], Awaitable[dict[str, Any] | None]]
AfterAgentCallback = Callable[[CallbackContext], Awaitable[None]]

BeforeModelCallback = Callable[[CallbackContext, LlmRequest], Awaitable[LlmResponse | None]]
AfterModelCallback = Callable[[CallbackContext, LlmResponse], Awaitable[LlmResponse | None]]

BeforeToolCallback = Callable[[ToolContext, dict[str, Any]], Awaitable[dict[str, Any] | None]]
AfterToolCallback = Callable[[ToolContext, dict[str, Any]], Awaitable[dict[str, Any] | None]]


@dataclass
class CallbackRegistry:
    before_agent: list[BeforeAgentCallback] = field(default_factory=list)
    after_agent: list[AfterAgentCallback] = field(default_factory=list)
    before_model: list[BeforeModelCallback] = field(default_factory=list)
    after_model: list[AfterModelCallback] = field(default_factory=list)
    before_tool: list[BeforeToolCallback] = field(default_factory=list)
    after_tool: list[AfterToolCallback] = field(default_factory=list)
