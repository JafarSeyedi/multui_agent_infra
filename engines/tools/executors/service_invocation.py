from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.SERVICE_INVOCATION)
class ServiceInvocationExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._service_url = self.param(self._params, ParameterName.URL, "")
        self._auth_token = self.param(self._params, ParameterName.AUTH_TOKEN, "")
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        from engines.communication import ServiceInvocationClient
        self._client = ServiceInvocationClient()
        return self._client

    @property
    def name(self) -> str:
        return "service_invocation"

    @property
    def description(self) -> str:
        return "Invoke SSDM service operations"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import json as _json

        operation_name = self.arg(args, ArgName.OPERATION, "")
        arguments_str = self.arg(args, ArgName.ARGUMENTS, "{}")
        binding_str = self.arg(args, ParameterName.BINDING_DATA, "")

        try:
            from engines.communication.consumption.models import InvocationResult
            from engines.document.models.ssdm_models import ServiceOperation, ServiceBinding

            arguments = _json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
            binding = None
            if binding_str:
                from engines.communication import BindingParser
                parsed = BindingParser.parse_raw(_json.loads(binding_str))
                binding = parsed[0] if parsed else None

            operation = ServiceOperation(name=operation_name)
            client = self._get_client()
            result: InvocationResult = await client.invoke(
                operation,
                arguments=arguments,
                binding=binding,
            )
            return ToolResult(success=True, data={
                "operation": operation_name,
                "payload": result.payload,
                "transport": result.transport.value if result.transport else None,
            })
        except ImportError as e:
            return ToolResult(success=False, error=f"Missing dependency: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
