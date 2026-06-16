from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.MESSAGE_BUS)
class MessageBusExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._bus_type = self.param(self._params, ParameterName.BUS_TYPE, "in_memory")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._bus_instance = None

    def _bus(self):
        if self._bus_instance is not None:
            return self._bus_instance
        if not self._connection:
            from engines.communication.buses.in_memory_message_bus import InMemoryMessageBus
            self._bus_instance = InMemoryMessageBus()
            return self._bus_instance
        buses = {
            "redis": ("engines.communication.buses.redis_pub_sub_bus", "RedisMessageBus"),
            "kafka": ("engines.communication.buses.kafka_bus", "KafkaMessageBus"),
            "rabbitmq": ("engines.communication.buses.rabbitmq_bus", "RabbitMQMessageBus"),
        }
        entry = buses.get(self._bus_type)
        if entry is None:
            from engines.communication.buses.in_memory_message_bus import InMemoryMessageBus
            self._bus_instance = InMemoryMessageBus()
            return self._bus_instance
        import importlib
        mod = importlib.import_module(entry[0])
        bus_cls = getattr(mod, entry[1])
        self._bus_instance = bus_cls(self._connection)
        return self._bus_instance

    @property
    def name(self) -> str:
        return f"message_bus:{self._bus_type}"

    @property
    def description(self) -> str:
        return f"Publish/subscribe via {self._bus_type} bus"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import json as _json
        from datetime import datetime, timezone

        action = self.arg(args, ArgName.ACTION, "publish")
        topic = self.arg(args, ParameterName.TOPIC, "")
        recipient = self.arg(args, ParameterName.RECIPIENT, "")
        message_str = self.arg(args, ArgName.PAYLOAD, "{}")
        message_type = self.arg(args, ParameterName.MESSAGE_TYPE, "default")

        try:
            bus = self._bus()
            await bus.start()

            if action == "publish":
                from engines.communication.buses.message_models import AgentMessage
                payload = _json.loads(message_str) if isinstance(message_str, str) else message_str
                msg = AgentMessage(
                    message_id=recipient or topic,
                    sender="tool",
                    recipient=recipient or topic,
                    message_type=message_type,
                    payload=payload,
                    timestamp=datetime.now(timezone.utc),
                )
                await bus.publish(msg)
                return ToolResult(success=True, data={"action": "publish", "recipient": msg.recipient, "published": True})
            elif action == "subscribe":
                async def _noop_handler(msg):
                    return None
                await bus.subscribe(recipient, _noop_handler)
                return ToolResult(success=True, data={"action": "subscribe", "recipient": recipient, "subscribed": True})
            elif action == "unsubscribe":
                async def _noop_handler(msg):
                    return None
                await bus.unsubscribe(recipient, _noop_handler)
                return ToolResult(success=True, data={"action": "unsubscribe", "recipient": recipient, "unsubscribed": True})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ToolResult(success=False, error=f"Missing dependency: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
        finally:
            if self._bus_instance is not None:
                try:
                    await self._bus_instance.stop()
                except Exception:
                    pass
