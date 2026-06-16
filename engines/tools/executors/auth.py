from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.AUTH)
class AuthExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._auth_type = self.param(self._params, ParameterName.METHOD, "api_key")
        self._auth_value = self.param(self._params, ParameterName.AUTH_TOKEN, "")
        self._auth_mgr = None

    def _get_manager(self):
        if self._auth_mgr is not None:
            return self._auth_mgr
        from engines.communication import AuthManager
        self._auth_mgr = AuthManager()
        return self._auth_mgr

    @property
    def name(self) -> str:
        return f"auth:{self._auth_type}"

    @property
    def description(self) -> str:
        return f"Authentication via {self._auth_type}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import json as _json

        action = self.arg(args, ArgName.ACTION, "apply")
        headers_str = self.arg(args, ArgName.HEADERS, "{}")
        params_str = self.arg(args, ArgName.PARAMS, "{}")

        try:
            from engines.document.models.ssdm_models import AuthConfig, AuthMethod
            headers = _json.loads(headers_str) if isinstance(headers_str, str) else headers_str
            params = _json.loads(params_str) if isinstance(params_str, str) else params_str

            method_map = {
                "api_key": AuthMethod.API_KEY,
                "bearer": AuthMethod.BEARER_TOKEN,
                "jwt": AuthMethod.JWT,
                "basic": AuthMethod.HTTP_BASIC,
                "oauth2": AuthMethod.OAUTH2,
            }
            method = method_map.get(self._auth_type, AuthMethod.NONE)

            auth_cfg = AuthConfig(method=method, value=self._auth_value or None)
            mgr = self._get_manager()
            cookies: dict = {}

            if action == "apply":
                await mgr.apply(auth_cfg, headers, params, cookies)
                return ToolResult(success=True, data={
                    "headers": headers,
                    "params": params,
                    "cookies": cookies,
                })
            elif action == "validate":
                valid = bool(self._auth_value) if method != AuthMethod.NONE else True
                return ToolResult(success=True, data={"valid": valid, "method": self._auth_type})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ToolResult(success=False, error=f"Missing dependency: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
