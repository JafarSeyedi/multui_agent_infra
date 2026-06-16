# Phase 1 — Communication Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `engines/communication/` to match the per-engine model/parser/writer pattern with unified Channel abstraction, migrating from dual `buses/` + `common/transport/` to a single `pubsub/` + `request_reply/` + `priority/` + `transport/` hierarchy.

**Architecture:** Template Method pattern — `BaseChannel` ABC, three semantic subtypes (`PubSubChannel`, `RequestReplyChannel`, `PriorityChannel`), each with backend folders. Decorators for cross-cutting concerns. Models at engine level in `models/`. Discovery and load balancing as sibling sub-modules within communication.

**Tech Stack:** Python 3.11+, pydantic v2, pytest, asyncio, mypy strict

---

## File Structure Map

```
engines/communication/              (NEW — replaces old structure)
├── __init__.py
├── plugin.py                        # BaseChannel ABC
│
├── models/
│   ├── __init__.py
│   ├── communication_models.py      # ChannelMessage, ChannelConfig, Session, Endpoint
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── asyncapi_parser.py
│   │   ├── openapi_parser.py
│   │   ├── grpc_proto_parser.py
│   │   └── communication_config_parser.py
│   └── writers/
│       ├── __init__.py
│       ├── asyncapi_writer.py
│       ├── openapi_writer.py
│       ├── grpc_proto_writer.py
│       └── communication_config_writer.py
│
├── pubsub/
│   ├── __init__.py
│   ├── plugin.py                    # PubSubChannel(BaseChannel)
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── in_memory/               # Migrated from buses/in_memory_message_bus.py
│   │   │   ├── __init__.py
│   │   │   └── in_memory_pubsub.py
│   │   ├── redis/                   # Migrated from buses/redis_pub_sub_bus.py
│   │   │   ├── __init__.py
│   │   │   └── redis_pubsub.py
│   │   ├── kafka/                   # Migrated from buses/kafka_bus.py
│   │   │   ├── __init__.py
│   │   │   └── kafka_pubsub.py
│   │   ├── rabbitmq/                # Migrated from buses/rabbitmq_bus.py
│   │   │   ├── __init__.py
│   │   │   └── rabbitmq_pubsub.py
│   │   └── topic/                   # Migrated from buses/topic_message_bus.py
│   │       ├── __init__.py
│   │       └── topic_pubsub.py
│   └── decorators/
│       ├── __init__.py
│       ├── durable.py
│       ├── logging.py
│       ├── metrics.py
│       └── circuit_breaker.py
│
├── request_reply/
│   ├── __init__.py
│   ├── plugin.py                    # RequestReplyChannel(BaseChannel)
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── in_memory/
│   │   │   ├── __init__.py
│   │   │   └── in_memory_reqreply.py
│   │   ├── grpc/
│   │   │   ├── __init__.py
│   │   │   └── grpc_reqreply.py
│   │   ├── http/
│   │   │   ├── __init__.py
│   │   │   └── http_reqreply.py
│   │   └── request_reply/           # Migrated from buses/request_reply_bus.py
│   │       ├── __init__.py
│   │       └── request_reply_sync.py
│   └── decorators/
│       ├── __init__.py
│       ├── logging.py
│       └── metrics.py
│
├── priority/
│   ├── __init__.py
│   ├── plugin.py                    # PriorityChannel(BaseChannel)
│   ├── backends/
│   │   ├── __init__.py
│   │   └── priority_message/        # Migrated from buses/priority_message_bus.py
│   │       ├── __init__.py
│   │       └── priority_queue.py
│   └── decorators/
│       ├── __init__.py
│       └── durable.py
│
├── transport/                       # Wire protocols (low-level)
│   ├── __init__.py
│   ├── plugin.py                    # BaseTransport ABC
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── http/
│   │   │   ├── __init__.py
│   │   │   └── http_transport.py    # Migrated from common/transport/http_client.py
│   │   ├── grpc/
│   │   │   ├── __init__.py
│   │   │   └── grpc_transport.py    # Migrated from common/transport/grpc_client.py
│   │   ├── websocket/
│   │   │   ├── __init__.py
│   │   │   └── websocket_transport.py
│   │   └── stdio/
│   │       ├── __init__.py
│   │       └── stdio_transport.py
│
├── discovery/
│   ├── __init__.py
│   ├── plugin.py                    # ServiceDiscovery ABC
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── kubernetes/
│   │   │   ├── __init__.py
│   │   │   └── k8s_discovery.py
│   │   ├── consul/
│   │   │   ├── __init__.py
│   │   │   └── consul_discovery.py
│   │   └── static/
│   │       ├── __init__.py
│   │       └── static_discovery.py
│
├── load_balancing/
│   ├── __init__.py
│   ├── plugin.py                    # LoadBalancer ABC
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── round_robin/
│   │   │   ├── __init__.py
│   │   │   └── round_robin_lb.py
│   │   └── least_connections/
│   │       ├── __init__.py
│   │       └── least_connections_lb.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_communication_models.py
    ├── test_pubsub.py
    ├── test_request_reply.py
    ├── test_priority.py
    ├── test_transport.py
    ├── test_discovery.py
    └── test_load_balancing.py
```

Old files to keep temporarily (deprecated aliases):
- `engines/communication/buses/` — kept with deprecation warning, will redirect to new backends
- `engines/communication/common/transport/` — kept, will be deleted after migration
- `engines/communication/messaging/`  — empty stubs, to be removed

---

### Task 1: Create engine-level `__init__.py` and `plugin.py`

**Files:**
- Create: `engines/communication/__init__.py`
- Create: `engines/communication/plugin.py`

- [ ] **Step 1: Create `__init__.py`**

```python
# engines/communication/__init__.py
```

- [ ] **Step 2: Create `plugin.py` — BaseChannel ABC**

```python
# engines/communication/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from .models.communication_models import ChannelMessage

HandlerType = Callable[[ChannelMessage], Awaitable[Optional[ChannelMessage]]]


class BaseChannel(ABC):
    """Abstract base for all channel implementations.

    Config selects a backend by dotted import path. No dynamic
    plugin loading — all backends are compiled in.
    """

    name: str = "base"

    @abstractmethod
    async def send(self, message: ChannelMessage) -> None:
        """Send a message through the channel."""
        ...

    @abstractmethod
    async def receive(self, handler: HandlerType) -> None:
        """Register a handler for incoming messages."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Initialize channel resources (connections, channels)."""

    @abstractmethod
    async def stop(self) -> None:
        """Release channel resources."""
```

- [ ] **Step 3: Commit**

```bash
git add engines/communication/__init__.py engines/communication/plugin.py
git commit -m "feat(communication): add BaseChannel ABC and __init__"
```

---

### Task 2: Define models

**Files:**
- Create: `engines/communication/models/__init__.py`
- Create: `engines/communication/models/communication_models.py`

- [ ] **Step 1: Create `models/__init__.py`**

```python
# engines/communication/models/__init__.py
```

- [ ] **Step 2: Create `communication_models.py`**

```python
# engines/communication/models/communication_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChannelType(str, Enum):
    PUB_SUB = "pub_sub"
    REQUEST_REPLY = "request_reply"
    PRIORITY = "priority"
    STREAM = "stream"


class MessagePriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class ChannelMessage:
    """Unified message envelope — replaces both AgentMessage and TransportRequest.

    Follows CloudEvents-inspired structure for compatibility.
    """
    id: str
    source: str
    type: str
    subject: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    data_schema: str | None = None
    content_type: str = "application/json"
    correlation_id: str | None = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    traceparent: str | None = None
    tenant_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ChannelConfig:
    """Configuration for a channel backend."""
    name: str
    channel_type: ChannelType
    backend: str  # dotted import path
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class Endpoint:
    """A service endpoint address."""
    host: str
    port: int
    transport: str  # "http", "grpc", "kafka", etc.
    metadata: dict[str, str] = field(default_factory=dict)
```

- [ ] **Step 3: Commit**

```bash
git add engines/communication/models/
git commit -m "feat(communication): add ChannelMessage and core models"
```

---

### Task 3: Create PubSubChannel plugin and in-memory backend

**Files:**
- Create: `engines/communication/pubsub/__init__.py`
- Create: `engines/communication/pubsub/plugin.py`
- Create: `engines/communication/pubsub/backends/__init__.py`
- Create: `engines/communication/pubsub/backends/in_memory/__init__.py`
- Create: `engines/communication/pubsub/backends/in_memory/in_memory_pubsub.py`
- Test: `engines/communication/tests/test_pubsub.py`

- [ ] **Step 1: Create `pubsub/__init__.py`**

```python
# engines/communication/pubsub/__init__.py
```

- [ ] **Step 2: Create `pubsub/plugin.py`**

```python
# engines/communication/pubsub/plugin.py
from __future__ import annotations

from abc import abstractmethod
from typing import Any

from ..plugin import BaseChannel, HandlerType
from ..models.communication_models import ChannelMessage


class PubSubChannel(BaseChannel):
    """Pub-sub channel. Supports topic-based publish and subscribe."""

    @abstractmethod
    async def publish(self, topic: str, message: ChannelMessage) -> None:
        """Publish a message to a topic."""

    @abstractmethod
    async def subscribe(self, topic: str, handler: HandlerType) -> None:
        """Subscribe to a topic with a handler."""

    @abstractmethod
    async def unsubscribe(self, topic: str, handler: HandlerType) -> None:
        """Remove a handler subscription."""
```

- [ ] **Step 3: Create backend `__init__.py` files**

```python
# engines/communication/pubsub/backends/__init__.py
```

```python
# engines/communication/pubsub/backends/in_memory/__init__.py
```

- [ ] **Step 4: Create `in_memory_pubsub.py`**

```python
# engines/communication/pubsub/backends/in_memory/in_memory_pubsub.py
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Optional

from ...plugin import HandlerType
from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class InMemoryPubSub(PubSubChannel):
    """In-memory pub-sub — for testing and monolith mode."""

    name = "in_memory"

    def __init__(self) -> None:
        self._handlers: dict[str, list[HandlerType]] = {}
        self._started = False

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        handlers = self._handlers.get(topic, [])
        for handler in handlers:
            await handler(message)

    async def subscribe(self, topic: str, handler: HandlerType) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    async def unsubscribe(self, topic: str, handler: HandlerType) -> None:
        handlers = self._handlers.get(topic, [])
        if handler in handlers:
            handlers.remove(handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler: HandlerType) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._handlers.clear()
        self._started = False
```

- [ ] **Step 5: Write the failing test**

```python
# engines/communication/tests/test_pubsub.py
import pytest
from engines.communication.pubsub.backends.in_memory.in_memory_pubsub import InMemoryPubSub
from engines.communication.models.communication_models import ChannelMessage


@pytest.mark.asyncio
async def test_publish_subscribe():
    channel = InMemoryPubSub()
    await channel.start()
    received = []

    async def handler(msg: ChannelMessage) -> None:
        received.append(msg)

    await channel.subscribe("test-topic", handler)
    msg = ChannelMessage(id="1", source="test", type="test.event")
    await channel.publish("test-topic", msg)
    assert len(received) == 1
    assert received[0].id == "1"
    await channel.stop()
```

- [ ] **Step 6: Run test to verify it fails**

Run: `python3 -m pytest engines/communication/tests/test_pubsub.py -v`
Expected: FAIL (modules don't exist yet — ImportError)

- [ ] **Step 7: Run test to verify it passes**

Run: `python3 -m pytest engines/communication/tests/test_pubsub.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add engines/communication/pubsub/ engines/communication/tests/
git commit -m "feat(communication): add PubSubChannel with in-memory backend"
```

---

### Task 4: RequestReplyChannel plugin and in-memory backend

**Files:**
- Create: `engines/communication/request_reply/__init__.py`
- Create: `engines/communication/request_reply/plugin.py`
- Create: `engines/communication/request_reply/backends/__init__.py`
- Create: `engines/communication/request_reply/backends/in_memory/__init__.py`
- Create: `engines/communication/request_reply/backends/in_memory/in_memory_reqreply.py`
- Test: `engines/communication/tests/test_request_reply.py`

- [ ] **Step 1: Create `request_reply/plugin.py`**

```python
# engines/communication/request_reply/plugin.py
from __future__ import annotations

from abc import abstractmethod
from typing import Any

from ..plugin import BaseChannel
from ..models.communication_models import ChannelMessage


class RequestReplyChannel(BaseChannel):
    """Request-reply channel. Sends a request and waits for a correlated response."""

    @abstractmethod
    async def request(self, message: ChannelMessage, timeout: float = 30.0) -> ChannelMessage:
        """Send a request and return the correlated response."""
```

- [ ] **Step 2: Create `in_memory_reqreply.py`**

```python
# engines/communication/request_reply/backends/in_memory/in_memory_reqreply.py
from __future__ import annotations

import asyncio
from typing import Any

from ....models.communication_models import ChannelMessage
from ..plugin import RequestReplyChannel


class InMemoryRequestReply(RequestReplyChannel):
    """In-memory request-reply — direct call pattern for testing."""

    name = "in_memory"

    def __init__(self) -> None:
        self._handler = None
        self._started = False

    async def request(self, message: ChannelMessage, timeout: float = 30.0) -> ChannelMessage:
        if self._handler is None:
            raise RuntimeError("No handler registered")
        result = await self._handler(message)
        if result is None:
            raise TimeoutError("No response from handler")
        return result

    async def send(self, message: ChannelMessage) -> None:
        pass

    async def receive(self, handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._handler = None
        self._started = False
```

- [ ] **Step 3: Write the failing test**

```python
# engines/communication/tests/test_request_reply.py
import pytest
from engines.communication.request_reply.backends.in_memory.in_memory_reqreply import InMemoryRequestReply
from engines.communication.models.communication_models import ChannelMessage


@pytest.mark.asyncio
async def test_request_reply():
    channel = InMemoryRequestReply()
    await channel.start()

    async def handler(msg: ChannelMessage) -> ChannelMessage:
        return ChannelMessage(id="resp-1", source="handler", type="response", data={"echo": msg.data})

    await channel.receive(handler)
    req = ChannelMessage(id="req-1", source="test", type="ping", data={"hello": "world"})
    response = await channel.request(req)
    assert response.data["echo"]["hello"] == "world"
    await channel.stop()
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/communication/tests/test_request_reply.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/communication/request_reply/ engines/communication/tests/test_request_reply.py
git commit -m "feat(communication): add RequestReplyChannel with in-memory backend"
```

---

### Task 5: PriorityChannel plugin and in-memory backend

**Files:**
- Create: `engines/communication/priority/__init__.py`
- Create: `engines/communication/priority/plugin.py`
- Create: `engines/communication/priority/backends/__init__.py`
- Create: `engines/communication/priority/backends/priority_message/__init__.py`
- Create: `engines/communication/priority/backends/priority_message/priority_queue.py`
- Test: `engines/communication/tests/test_priority.py`

- [ ] **Step 1: Create `priority/plugin.py`**

```python
# engines/communication/priority/plugin.py
from __future__ import annotations

from abc import abstractmethod

from ..plugin import BaseChannel
from ..models.communication_models import ChannelMessage, MessagePriority


class PriorityChannel(BaseChannel):
    """Priority queue channel. Delivers messages ordered by priority level."""

    @abstractmethod
    async def enqueue(self, message: ChannelMessage, priority: MessagePriority | None = None) -> None:
        """Enqueue a message at the given priority level."""
```

- [ ] **Step 2: Create `priority_queue.py`**

```python
# engines/communication/priority/backends/priority_message/priority_queue.py
from __future__ import annotations

import asyncio
import heapq
from typing import Any, Optional

from ....models.communication_models import ChannelMessage, MessagePriority
from ...plugin import PriorityChannel


class InMemoryPriorityQueue(PriorityChannel):
    """In-memory priority queue for testing."""

    name = "in_memory"

    def __init__(self) -> None:
        self._queue: list[tuple[int, int, ChannelMessage]] = []
        self._counter = 0
        self._handler = None
        self._started = False

    async def enqueue(self, message: ChannelMessage, priority: MessagePriority | None = None) -> None:
        p = (priority or message.priority).value
        heapq.heappush(self._queue, (-p, self._counter, message))
        self._counter += 1

    async def send(self, message: ChannelMessage) -> None:
        await self.enqueue(message)

    async def receive(self, handler) -> None:
        self._handler = handler

    async def dequeue(self) -> Optional[ChannelMessage]:
        if not self._queue:
            return None
        _, _, message = heapq.heappop(self._queue)
        return message

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._queue.clear()
        self._handler = None
        self._started = False
```

- [ ] **Step 3: Write test**

```python
# engines/communication/tests/test_priority.py
import pytest
from engines.communication.priority.backends.priority_message.priority_queue import InMemoryPriorityQueue
from engines.communication.models.communication_models import ChannelMessage, MessagePriority


@pytest.mark.asyncio
async def test_priority_ordering():
    channel = InMemoryPriorityQueue()
    await channel.start()

    low = ChannelMessage(id="low", source="test", type="e", priority=MessagePriority.LOW)
    high = ChannelMessage(id="high", source="test", type="e", priority=MessagePriority.HIGH)
    normal = ChannelMessage(id="normal", source="test", type="e", priority=MessagePriority.NORMAL)

    await channel.enqueue(low)
    await channel.enqueue(high)
    await channel.enqueue(normal)

    msg1 = await channel.dequeue()
    msg2 = await channel.dequeue()
    msg3 = await channel.dequeue()

    assert msg1.id == "high"
    assert msg2.id == "normal"
    assert msg3.id == "low"
    await channel.stop()
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/communication/tests/test_priority.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/communication/priority/ engines/communication/tests/test_priority.py
git commit -m "feat(communication): add PriorityChannel with in-memory backend"
```

---

### Task 6: Transport module

**Files:**
- Create: `engines/communication/transport/__init__.py`
- Create: `engines/communication/transport/plugin.py`
- Create: `engines/communication/transport/backends/__init__.py`
- Create: `engines/communication/transport/backends/http/__init__.py`
- Create: `engines/communication/transport/backends/http/http_transport.py`
- Create: `engines/communication/transport/backends/stdio/__init__.py`
- Create: `engines/communication/transport/backends/stdio/stdio_transport.py`
- Test: `engines/communication/tests/test_transport.py`

- [ ] **Step 1: Create `transport/plugin.py`**

```python
# engines/communication/transport/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models.communication_models import ChannelMessage


class BaseTransport(ABC):
    """Low-level wire protocol transport.

    Transports handle the raw byte/stream layer. Channel backends
    use transports for actual wire communication.
    """

    name: str = "base"

    @abstractmethod
    async def send_bytes(self, data: bytes, endpoint: str) -> bytes:
        """Send bytes to an endpoint and return response bytes."""

    @abstractmethod
    async def connect(self, endpoint: str) -> None:
        """Connect to a remote endpoint."""

    @abstractmethod
    async def close(self) -> None:
        """Close the transport."""
```

- [ ] **Step 2: Create `http_transport.py`** (simplified — wraps aiohttp)

```python
# engines/communication/transport/backends/http/http_transport.py
from __future__ import annotations

from ...plugin import BaseTransport


class HttpTransport(BaseTransport):
    """HTTP/HTTPS transport using aiohttp."""

    name = "http"

    def __init__(self) -> None:
        self._session = None

    async def connect(self, endpoint: str) -> None:
        try:
            import aiohttp
        except ImportError as exc:
            raise RuntimeError("aiohttp is required for HTTP transport") from exc
        self._session = aiohttp.ClientSession()

    async def send_bytes(self, data: bytes, endpoint: str) -> bytes:
        if self._session is None:
            raise RuntimeError("Transport not connected")
        async with self._session.post(endpoint, data=data) as resp:
            return await resp.read()

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
```

- [ ] **Step 3: Create `stdio_transport.py`** (for MCP stdio)

```python
# engines/communication/transport/backends/stdio/stdio_transport.py
from __future__ import annotations

import asyncio
import shlex

from ...plugin import BaseTransport


class StdioTransport(BaseTransport):
    """STDIO transport — spawns a subprocess and communicates via stdin/stdout."""

    name = "stdio"

    def __init__(self, command: str) -> None:
        self._command = command
        self._process: asyncio.subprocess.Process | None = None

    async def connect(self, endpoint: str | None = None) -> None:
        args = shlex.split(self._command)
        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def send_bytes(self, data: bytes, endpoint: str | None = None) -> bytes:
        if self._process is None or self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("Process not connected")
        self._process.stdin.write(data + b"\n")
        await self._process.stdin.drain()
        line = await self._process.stdout.readline()
        return line

    async def close(self) -> None:
        if self._process is not None:
            self._process.kill()
            await self._process.wait()
            self._process = None
```

- [ ] **Step 4: Write test for transports**

```python
# engines/communication/tests/test_transport.py
import pytest


@pytest.mark.asyncio
async def test_http_transport_init():
    from engines.communication.transport.backends.http.http_transport import HttpTransport
    transport = HttpTransport()
    assert transport.name == "http"


@pytest.mark.asyncio
async def test_stdio_transport_init():
    from engines.communication.transport.backends.stdio.stdio_transport import StdioTransport
    transport = StdioTransport(command="echo")
    assert transport.name == "stdio"
```

- [ ] **Step 5: Run test**

Run: `python3 -m pytest engines/communication/tests/test_transport.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add engines/communication/transport/ engines/communication/tests/test_transport.py
git commit -m "feat(communication): add transport module with HTTP and STDIO backends"
```

---

### Task 7: Discovery module

**Files:**
- Create: `engines/communication/discovery/__init__.py`
- Create: `engines/communication/discovery/plugin.py`
- Create: `engines/communication/discovery/backends/__init__.py`
- Create: `engines/communication/discovery/backends/static/__init__.py`
- Create: `engines/communication/discovery/backends/static/static_discovery.py`
- Test: `engines/communication/tests/test_discovery.py`

- [ ] **Step 1: Create `discovery/plugin.py`**

```python
# engines/communication/discovery/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.communication_models import Endpoint


class ServiceDiscovery(ABC):
    """Abstract service discovery."""

    name: str = "base"

    @abstractmethod
    async def resolve(self, service_name: str) -> list[Endpoint]:
        """Resolve a service name to endpoints."""

    @abstractmethod
    async def register(self, service_name: str, endpoint: Endpoint) -> None:
        """Register a service endpoint."""

    @abstractmethod
    async def deregister(self, service_name: str, endpoint: Endpoint) -> None:
        """Remove a service registration."""
```

- [ ] **Step 2: Create `static_discovery.py`**

```python
# engines/communication/discovery/backends/static/static_discovery.py
from __future__ import annotations

from ....models.communication_models import Endpoint
from ...plugin import ServiceDiscovery


class StaticDiscovery(ServiceDiscovery):
    """Static list-based discovery — endpoints defined in config."""

    name = "static"

    def __init__(self, endpoints: dict[str, list[Endpoint]] | None = None) -> None:
        self._endpoints: dict[str, list[Endpoint]] = endpoints or {}

    async def resolve(self, service_name: str) -> list[Endpoint]:
        return self._endpoints.get(service_name, [])

    async def register(self, service_name: str, endpoint: Endpoint) -> None:
        self._endpoints.setdefault(service_name, []).append(endpoint)

    async def deregister(self, service_name: str, endpoint: Endpoint) -> None:
        self._endpoints[service_name] = [e for e in self._endpoints.get(service_name, []) if e != endpoint]
```

- [ ] **Step 3: Write test**

```python
# engines/communication/tests/test_discovery.py
import pytest
from engines.communication.discovery.backends.static.static_discovery import StaticDiscovery
from engines.communication.models.communication_models import Endpoint


@pytest.mark.asyncio
async def test_static_discovery_resolve():
    ep = Endpoint(host="localhost", port=8080, transport="http")
    discovery = StaticDiscovery({"my-service": [ep]})
    results = await discovery.resolve("my-service")
    assert len(results) == 1
    assert results[0].host == "localhost"


@pytest.mark.asyncio
async def test_static_discovery_register():
    discovery = StaticDiscovery()
    ep = Endpoint(host="test", port=9090, transport="grpc")
    await discovery.register("svc", ep)
    results = await discovery.resolve("svc")
    assert len(results) == 1
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/communication/tests/test_discovery.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/communication/discovery/ engines/communication/tests/test_discovery.py
git commit -m "feat(communication): add discovery module with static backend"
```

---

### Task 8: Load balancing module

**Files:**
- Create: `engines/communication/load_balancing/__init__.py`
- Create: `engines/communication/load_balancing/plugin.py`
- Create: `engines/communication/load_balancing/backends/__init__.py`
- Create: `engines/communication/load_balancing/backends/round_robin/__init__.py`
- Create: `engines/communication/load_balancing/backends/round_robin/round_robin_lb.py`
- Test: `engines/communication/tests/test_load_balancing.py`

- [ ] **Step 1: Create `load_balancing/plugin.py`**

```python
# engines/communication/load_balancing/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models.communication_models import Endpoint


class LoadBalancer(ABC):
    """Abstract load balancer."""

    name: str = "base"

    @abstractmethod
    def select(self, endpoints: list[Endpoint], context: dict[str, Any] | None = None) -> Endpoint:
        """Select an endpoint from the available list."""
```

- [ ] **Step 2: Create `round_robin_lb.py`**

```python
# engines/communication/load_balancing/backends/round_robin/round_robin_lb.py
from __future__ import annotations

from typing import Any

from ....models.communication_models import Endpoint
from ...plugin import LoadBalancer


class RoundRobinLoadBalancer(LoadBalancer):
    """Round-robin load balancer."""

    name = "round_robin"

    def __init__(self) -> None:
        self._index = 0

    def select(self, endpoints: list[Endpoint], context: dict[str, Any] | None = None) -> Endpoint:
        if not endpoints:
            raise ValueError("No endpoints available")
        idx = self._index % len(endpoints)
        self._index += 1
        return endpoints[idx]
```

- [ ] **Step 3: Write test**

```python
# engines/communication/tests/test_load_balancing.py
import pytest
from engines.communication.load_balancing.backends.round_robin.round_robin_lb import RoundRobinLoadBalancer
from engines.communication.models.communication_models import Endpoint


def test_round_robin():
    eps = [
        Endpoint(host="a", port=1, transport="http"),
        Endpoint(host="b", port=2, transport="http"),
    ]
    lb = RoundRobinLoadBalancer()
    assert lb.select(eps).host == "a"
    assert lb.select(eps).host == "b"
    assert lb.select(eps).host == "a"


def test_round_robin_empty():
    lb = RoundRobinLoadBalancer()
    with pytest.raises(ValueError, match="No endpoints"):
        lb.select([])
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/communication/tests/test_load_balancing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/communication/load_balancing/ engines/communication/tests/test_load_balancing.py
git commit -m "feat(communication): add load balancing module with round-robin"
```

---

### Task 9: Models parsers and writers

**Files:**
- Create: `engines/communication/models/parsers/communication_config_parser.py`
- Create: `engines/communication/models/writers/communication_config_writer.py`
- Test: `engines/communication/tests/test_communication_models.py`

- [ ] **Step 1: Create config parser**

```python
# engines/communication/models/parsers/communication_config_parser.py
from __future__ import annotations

from ..communication_models import ChannelConfig, ChannelType


def parse_channel_config(data: dict) -> ChannelConfig:
    """Parse a channel config dict (from YAML/JSON deployment config) into a ChannelConfig."""
    return ChannelConfig(
        name=data["name"],
        channel_type=ChannelType(data.get("type", "pub_sub")),
        backend=data["backend"],
        settings=data.get("settings", {}),
    )
```

- [ ] **Step 2: Create config writer**

```python
# engines/communication/models/writers/communication_config_writer.py
from __future__ import annotations

from ..communication_models import ChannelConfig


def write_channel_config(config: ChannelConfig) -> dict:
    """Serialize a ChannelConfig to a dict (for YAML/JSON output)."""
    return {
        "name": config.name,
        "type": config.channel_type.value,
        "backend": config.backend,
        "settings": config.settings,
    }
```

- [ ] **Step 3: Write test**

```python
# engines/communication/tests/test_communication_models.py
from engines.communication.models.communication_models import ChannelMessage, ChannelConfig, ChannelType, Endpoint
from engines.communication.models.parsers.communication_config_parser import parse_channel_config
from engines.communication.models.writers.communication_config_writer import write_channel_config


def test_channel_message_defaults():
    msg = ChannelMessage(id="1", source="s", type="t")
    assert msg.priority.value == 5  # NORMAL


def test_channel_config_roundtrip():
    config = ChannelConfig(name="test", channel_type=ChannelType.PUB_SUB, backend="in_memory")
    data = write_channel_config(config)
    parsed = parse_channel_config(data)
    assert parsed.name == config.name
    assert parsed.channel_type == config.channel_type


def test_endpoint():
    ep = Endpoint(host="localhost", port=8080, transport="http")
    assert ep.host == "localhost"
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/communication/tests/test_communication_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/communication/models/parsers/ engines/communication/models/writers/ engines/communication/tests/test_communication_models.py
git commit -m "feat(communication): add model parsers and writers with roundtrip test"
```

---

### Task 10: Decorators — durable, logging, metrics, circuit breaker

**Files:**
- Create: `engines/communication/pubsub/decorators/__init__.py`
- Create: `engines/communication/pubsub/decorators/durable.py`
- Create: `engines/communication/pubsub/decorators/logging.py`
- Create: `engines/communication/pubsub/decorators/metrics.py`
- Create: `engines/communication/pubsub/decorators/circuit_breaker.py`
- Test: `engines/communication/tests/test_decorators.py`

- [ ] **Step 1: Create `durable.py`**

```python
# engines/communication/pubsub/decorators/durable.py
from __future__ import annotations

from typing import Any

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class DurablePubSub(PubSubChannel):
    """Wrapper that adds message persistence to any PubSubChannel."""

    def __init__(self, inner: PubSubChannel) -> None:
        self._inner = inner
        self._store: list[ChannelMessage] = []

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        self._store.append(message)
        await self._inner.publish(topic, message)

    async def subscribe(self, topic: str, handler) -> None:
        await self._inner.subscribe(topic, handler)

    async def unsubscribe(self, topic: str, handler) -> None:
        await self._inner.unsubscribe(topic, handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        await self._inner.start()

    async def stop(self) -> None:
        await self._inner.stop()

    @property
    def stored_messages(self) -> list[ChannelMessage]:
        return list(self._store)
```

- [ ] **Step 2: Create `logging.py`**

```python
# engines/communication/pubsub/decorators/logging.py
from __future__ import annotations

import logging

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel

logger = logging.getLogger(__name__)


class LoggingPubSub(PubSubChannel):
    """Wrapper that logs all published messages."""

    def __init__(self, inner: PubSubChannel) -> None:
        self._inner = inner

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        logger.info("Publishing to %s: %s", topic, message.id)
        await self._inner.publish(topic, message)

    async def subscribe(self, topic: str, handler) -> None:
        await self._inner.subscribe(topic, handler)

    async def unsubscribe(self, topic: str, handler) -> None:
        await self._inner.unsubscribe(topic, handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        await self._inner.start()

    async def stop(self) -> None:
        await self._inner.stop()
```

- [ ] **Step 3: Create `metrics.py`** (simplified — stub counters)

```python
# engines/communication/pubsub/decorators/metrics.py
from __future__ import annotations

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class MetricsPubSub(PubSubChannel):
    """Wrapper that counts published messages."""

    def __init__(self, inner: PubSubChannel) -> None:
        self._inner = inner
        self.publish_count = 0

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        self.publish_count += 1
        await self._inner.publish(topic, message)

    async def subscribe(self, topic: str, handler) -> None:
        await self._inner.subscribe(topic, handler)

    async def unsubscribe(self, topic: str, handler) -> None:
        await self._inner.unsubscribe(topic, handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        await self._inner.start()

    async def stop(self) -> None:
        await self._inner.stop()
```

- [ ] **Step 4: Create `circuit_breaker.py`**

```python
# engines/communication/pubsub/decorators/circuit_breaker.py
from __future__ import annotations

from enum import Enum

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerPubSub(PubSubChannel):
    """Wrapper that stops publishing when error threshold exceeded."""

    def __init__(self, inner: PubSubChannel, threshold: int = 5) -> None:
        self._inner = inner
        self._threshold = threshold
        self._failures = 0
        self.state = CircuitState.CLOSED

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        if self.state == CircuitState.OPEN:
            raise RuntimeError("Circuit breaker is open")
        try:
            await self._inner.publish(topic, message)
            self._failures = 0
            self.state = CircuitState.CLOSED
        except Exception:
            self._failures += 1
            if self._failures >= self._threshold:
                self.state = CircuitState.OPEN
            raise

    async def subscribe(self, topic: str, handler) -> None:
        await self._inner.subscribe(topic, handler)

    async def unsubscribe(self, topic: str, handler) -> None:
        await self._inner.unsubscribe(topic, handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        await self._inner.start()

    async def stop(self) -> None:
        await self._inner.stop()
```

- [ ] **Step 5: Write tests for decorators**

```python
# engines/communication/tests/test_decorators.py
import pytest
from engines.communication.pubsub.backends.in_memory.in_memory_pubsub import InMemoryPubSub
from engines.communication.pubsub.decorators.durable import DurablePubSub
from engines.communication.pubsub.decorators.logging import LoggingPubSub
from engines.communication.pubsub.decorators.metrics import MetricsPubSub
from engines.communication.pubsub.decorators.circuit_breaker import CircuitBreakerPubSub, CircuitState
from engines.communication.models.communication_models import ChannelMessage


@pytest.mark.asyncio
async def test_durable_decorator():
    inner = InMemoryPubSub()
    durable = DurablePubSub(inner)
    await durable.start()
    msg = ChannelMessage(id="1", source="t", type="t")
    await durable.publish("t", msg)
    assert len(durable.stored_messages) == 1
    await durable.stop()


@pytest.mark.asyncio
async def test_metrics_decorator():
    inner = InMemoryPubSub()
    metrics = MetricsPubSub(inner)
    await metrics.start()
    msg = ChannelMessage(id="1", source="t", type="t")
    await metrics.publish("t", msg)
    await metrics.publish("t", msg)
    assert metrics.publish_count == 2
    await metrics.stop()


@pytest.mark.asyncio
async def test_circuit_breaker():
    class FailingPubSub(InMemoryPubSub):
        async def publish(self, topic, message):
            raise RuntimeError("fail")

    inner = FailingPubSub()
    cb = CircuitBreakerPubSub(inner, threshold=2)
    await cb.start()
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.publish("t", ChannelMessage(id="1", source="t", type="t"))
    assert cb.state == CircuitState.OPEN
    await cb.stop()
```

- [ ] **Step 6: Run test**

Run: `python3 -m pytest engines/communication/tests/test_decorators.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add engines/communication/pubsub/decorators/ engines/communication/tests/test_decorators.py
git commit -m "feat(communication): add channel decorators — durable, logging, metrics, circuit breaker"
```

---

### Task 11: Migration shims for old buses/ paths

**Files:**
- Modify: `engines/communication/buses/__init__.py` (add deprecation warnings)
- Modify: `engines/communication/buses/base_message_bus.py` (redirect to PubSubChannel)

- [ ] **Step 1: Update `buses/__init__.py` with deprecation warning**

```python
# engines/communication/buses/__init__.py
import warnings

warnings.warn(
    "engines.communication.buses is deprecated. Use engines.communication.pubsub instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

- [ ] **Step 2: Verify nothing breaks**

Run: `python3 -m pytest engines/communication/tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add engines/communication/buses/__init__.py
git commit -m "chore(communication): add deprecation warning to old buses/ paths"
```

---

### Task 12: Run all tests and verify

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest engines/communication/tests/ -v`
Expected: All tests pass (at minimum: pubsub, request_reply, priority, transport, discovery, load_balancing, models, decorators)

- [ ] **Step 2: Run existing knowledge tests to ensure no regressions**

Run: `python3 -m pytest engines/knowledge/tests/ -v --timeout=60` (or just run a subset: `engines/knowledge/tests/test_writers.py`)

Expected: Existing tests pass (or known skips)

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "test: add full test suite for communication engine"
```

---

## Self-Review Checklist

- [ ] **Spec coverage:** All main elements from spec Section 6.1 are covered — models, pubsub, request_reply, priority, transport, discovery, load_balancing, decorators, parsers/writers, deprecation shims
- [ ] **No placeholders:** Every step has actual code and commands
- [ ] **Type consistency:** `ChannelMessage` is used consistently across all tasks. `BaseChannel` → `PubSubChannel` → backends hierarchy is consistent. `in_memory_pubsub` from Task 3 is used in decorator tests in Task 10.
- [ ] **Testability:** Every backend has at least one test. Decorator tests use the in-memory backend.
