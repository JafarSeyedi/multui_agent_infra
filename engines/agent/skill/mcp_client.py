"""
MCP client for connecting to MCP servers and calling tools.
"""
from typing import Any, List, Dict, Optional
import logging

ClientSession: Any = None
StdioServerParameters: Any = None
stdio_client: Any = None

try:
    from mcp import ClientSession as _MCPClientSession, StdioServerParameters as _MCPStdioServerParameters
    from mcp.client.stdio import stdio_client as _MCPStdioClient
    ClientSession = _MCPClientSession
    StdioServerParameters = _MCPStdioServerParameters
    stdio_client = _MCPStdioClient
except ImportError:
    logging.warning("MCP Python SDK not installed. MCP client will not be functional.")

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, server_command: Optional[List[str]] = None, server_url: Optional[str] = None):
        """
        Initialize the MCP client.
        Either server_command (for stdio connection) or server_url (for HTTP/WebSocket) must be provided.
        """
        if ClientSession is None:
            raise ImportError("MCP Python SDK is not installed. Please install it to use the MCP client.")

        self.server_command = server_command
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self._stdio_context = None  # For stdio client context

    async def connect(self):
        """
        Connect to the MCP server.
        """
        if self.server_command:
            # Stdio connection
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else [],
                env=None
            )
            self._stdio_context = stdio_client(server_params)
            read_stream, write_stream = await self._stdio_context.__aenter__()
            self.session = ClientSession(read_stream, write_stream)
            await self.session.__aenter__()
        elif self.server_url:
            # TODO: Implement HTTP/WebSocket connection
            # For now, we'll raise an error as we are focusing on stdio for simplicity.
            raise NotImplementedError("HTTP/WebSocket MCP connections are not yet implemented.")
        else:
            raise ValueError("Either server_command or server_url must be provided.")

    async def disconnect(self):
        """
        Disconnect from the MCP server.
        """
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)
            self._stdio_context = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.
        """
        if not self.session:
            raise RuntimeError("MCP client is not connected. Call connect() first.")
        result = await self.session.list_tools()
        return [tool.model_dump() for tool in result.tools]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.
        """
        if not self.session:
            raise RuntimeError("MCP client is not connected. Call connect() first.")
        result = await self.session.call_tool(tool_name, arguments)
        return result