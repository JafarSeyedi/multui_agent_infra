from __future__ import annotations

import pytest

from engines.tools import AIModelExecutor
from engines.tools import BaseToolExecutor
from engines.tools import CLIExecutor
from engines.tools import CompositeExecutor
from engines.tools import DBQueryExecutor
from engines.tools import FileExecutor
from engines.tools import GrpcToolExecutor
from engines.tools import HTTPServiceExecutor
from engines.tools import HTTPToolExecutor
from engines.tools import MCPToolExecutor
from engines.tools import MIBSNMPExecutor
from engines.tools import MessageBusExecutor
from engines.tools import ParameterMapper
from engines.tools import PythonFunctionExecutor
from engines.tools import TCPSocketExecutor
from engines.tools import ToolResult
from engines.tools import ToolRegistry
from engines.tools import YANGNetconfExecutor


class TestToolResult:
    def test_success_result(self) -> None:
        r = ToolResult(True, data={"key": "value"})
        assert r.success is True
        assert r.data == {"key": "value"}
        assert r.error is None

    def test_error_result(self) -> None:
        r = ToolResult(False, error="something went wrong")
        assert r.success is False
        assert r.error == "something went wrong"


class TestToolRegistry:
    @pytest.fixture
    def registry(self) -> ToolRegistry:
        return ToolRegistry()

    async def test_register_and_get(self, registry: ToolRegistry) -> None:
        executor = HTTPToolExecutor()
        registry.register(executor)
        assert registry.get("http_tool") is executor

    async def test_execute_known(self, registry: ToolRegistry) -> None:
        executor = HTTPToolExecutor()
        registry.register(executor)
        result = await registry.execute("http_tool", url="http://example.com")
        assert result.success is True

    async def test_execute_unknown(self, registry: ToolRegistry) -> None:
        result = await registry.execute("nonexistent")
        assert result.success is False

    async def test_list_tools(self, registry: ToolRegistry) -> None:
        registry.register(HTTPToolExecutor())
        registry.register(AIModelExecutor("gpt4"))
        tools = registry.list_tools()
        assert len(tools) == 2
        names = [t["name"] for t in tools]
        assert "http_tool" in names
        assert "ai_model:gpt4" in names

    async def test_unregister(self, registry: ToolRegistry) -> None:
        executor = HTTPToolExecutor()
        registry.register(executor)
        registry.unregister("http_tool")
        assert registry.get("http_tool") is None


class TestExecutors:
    async def test_ai_model(self) -> None:
        e = AIModelExecutor("gpt4")
        assert "ai_model:gpt4" in e.name
        r = await e.execute(prompt="Hello")
        assert r.success is True

    async def test_db_query(self) -> None:
        e = DBQueryExecutor()
        r = await e.execute(query="SELECT 1")
        assert r.success is True

    async def test_file_executor(self) -> None:
        e = FileExecutor()
        r = await e.execute(operation="read", path="/tmp/test")
        assert r.success is True

    async def test_grpc_tool(self) -> None:
        e = GrpcToolExecutor("localhost:50051")
        r = await e.execute(method="SayHello")
        assert r.success is True

    async def test_http_service(self) -> None:
        e = HTTPServiceExecutor("https://api.example.com")
        r = await e.execute(method="GET", path="/v1/status")
        assert r.success is True

    async def test_http_tool(self) -> None:
        e = HTTPToolExecutor("token123")
        r = await e.execute(url="https://example.com", method="POST")
        assert r.success is True

    async def test_mcp_tool(self) -> None:
        e = MCPToolExecutor("http://mcp.local")
        r = await e.execute(tool="search")
        assert r.success is True

    async def test_message_bus(self) -> None:
        e = MessageBusExecutor("redis")
        r = await e.execute(action="publish", topic="events")
        assert r.success is True

    async def test_snmp(self) -> None:
        e = MIBSNMPExecutor("192.168.1.1")
        r = await e.execute(operation="get", oid="1.3.6.1.2.1.1.1")
        assert r.success is True

    async def test_tcp_socket(self) -> None:
        e = TCPSocketExecutor("localhost", 8080)
        r = await e.execute(data="ping")
        assert r.success is True

    async def test_netconf(self) -> None:
        e = YANGNetconfExecutor("192.168.1.1", "admin")
        r = await e.execute(operation="get-config")
        assert r.success is True

    async def test_python_function(self) -> None:
        e = PythonFunctionExecutor()

        def add(a: int, b: int) -> int:
            return a + b

        e.register_function("add", add)
        r = await e.execute(function="add", args=(1, 2), kwargs={})
        assert r.success is True
        assert r.data["result"] == 3

    async def test_python_function_unknown(self) -> None:
        e = PythonFunctionExecutor()
        r = await e.execute(function="nonexistent")
        assert r.success is False

    async def test_python_function_error(self) -> None:
        e = PythonFunctionExecutor()

        def fail() -> None:
            raise ValueError("oops")

        e.register_function("fail", fail)
        r = await e.execute(function="fail")
        assert r.success is False

    async def test_cli_executor(self) -> None:
        e = CLIExecutor()
        r = await e.execute(command="echo hello")
        assert r.success is True
        assert "hello" in r.data.get("stdout", "")

    async def test_cli_executor_no_command(self) -> None:
        e = CLIExecutor()
        r = await e.execute()
        assert r.success is False

    async def test_composite_executor(self) -> None:
        inner = HTTPToolExecutor()
        composite = CompositeExecutor([inner])
        r = await composite.execute(url="http://test.com")
        assert r.success is True

    async def test_composite_executor_fails_fast(self) -> None:
        class FailingExecutor(BaseToolExecutor):
            @property
            def name(self) -> str:
                return "failer"
            @property
            def description(self) -> str:
                return "Always fails"
            async def execute(self, **kwargs: str) -> ToolResult:
                return ToolResult(False, error="fail")

        composite = CompositeExecutor([FailingExecutor(), HTTPToolExecutor()])
        r = await composite.execute()
        assert r.success is False


class TestParameterMapper:
    def test_map(self) -> None:
        mapper = ParameterMapper({"user_input": "prompt"})
        mapped = mapper.map({"user_input": "hello", "extra": "world"})
        assert mapped == {"prompt": "hello", "extra": "world"}

    def test_validate(self) -> None:
        mapper = ParameterMapper()
        missing = mapper.validate({"a": 1}, ["a", "b"])
        assert missing == ["b"]

    def test_validate_all_present(self) -> None:
        mapper = ParameterMapper()
        missing = mapper.validate({"a": 1, "b": 2}, ["a", "b"])
        assert missing == []
