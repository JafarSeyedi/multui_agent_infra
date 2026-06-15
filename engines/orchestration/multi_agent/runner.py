from __future__ import annotations

import uuid
from typing import Any, AsyncIterator

from engines.agent.models import AgentInput, AgentOutput
from engines.session.models import Event, EventActions
from engines.session.service import BaseSessionService, InMemorySessionService
from .plugins import PluginRegistry


class Runner:
    def __init__(
        self,
        agent: Any = None,
        app_name: str = "",
        session_service: BaseSessionService | None = None,
        multi_agent_engine: Any = None,
        plugins: PluginRegistry | None = None,
    ) -> None:
        self._agent = agent
        self._app_name = app_name
        self.session_service = session_service or InMemorySessionService()
        self._multi_agent_engine = multi_agent_engine
        self.plugins = plugins or PluginRegistry()

    async def run_async(
        self,
        user_id: str,
        session_id: str,
        new_message: str,
    ) -> AsyncIterator[Event]:
        session = await self.session_service.create_session(
            self._app_name, user_id, session_id,
        )

        await self.plugins.fire_session_start(
            self._app_name, user_id, session_id,
        )

        invocation_id = str(uuid.uuid4())

        user_event = Event(
            id=str(uuid.uuid4()),
            invocation_id=invocation_id,
            author="user",
            content={"text": new_message},
        )
        await self.session_service.append_event(session, user_event)
        yield user_event

        if self._multi_agent_engine is not None:
            from ..core.engine import ProcessDefinition
            from ..core.instance import ProcessInstance

            instance = ProcessInstance(
                id=session_id,
                definition_id=session_id,
                variables={"user_message": new_message},
            )
            instance_key = f"runner_{session_id}"
            definition = ProcessDefinition(
                key=instance_key,
                definition_xml={"message": new_message, "_engine_type": "multi_agent"},
            )
            await self._multi_agent_engine.execute_instance(instance, definition)

            agent_event = Event(
                id=str(uuid.uuid4()),
                invocation_id=invocation_id,
                author="agent",
                content={"text": f"engine executed instance {instance.id}"},
            )
        elif self._agent is not None:
            input_data = AgentInput(
                agent_name="runner",
                message=new_message,
                context={"session_id": session_id, "app_name": self._app_name},
                metadata={"invocation_id": invocation_id},
            )

            plugin_override = await self.plugins.fire_before_agent(
                "runner", input_data,
            )
            if plugin_override is not None:
                output = plugin_override
            else:
                output: AgentOutput = await self._agent.run(input_data)

            await self.plugins.fire_after_agent("runner", input_data, output)

            agent_event = Event(
                id=str(uuid.uuid4()),
                invocation_id=invocation_id,
                author="agent",
                content={
                    "text": output.message or "",
                    "payload": output.payload,
                },
                actions=EventActions(state_delta={}),
            )
        else:
            raise ValueError("Runner requires either agent or multi_agent_engine")

        await self.session_service.append_event(session, agent_event)
        await self.plugins.fire_session_end(
            self._app_name, user_id, session_id,
        )
        yield agent_event
