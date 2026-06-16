from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.COMPUTER_USE)
class ComputerUseExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._action = self.param(self._params, ParameterName.ACTION, "navigate")
        self._url = self.param(self._params, ParameterName.URL, "")
        self._headless = self.param(self._params, ParameterName.HEADLESS, True)
        self._selector = self.param(self._params, ParameterName.SELECTOR, "")

    @property
    def name(self) -> str:
        return "computer_use"

    @property
    def description(self) -> str:
        return "Browser automation via Playwright"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        value = self.arg(args, ArgName.CONTENT, "")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self._headless)
                page = await browser.new_page()

                if self._action == "navigate":
                    await page.goto(self._url)
                    return ToolResult(success=True, data={"title": await page.title(), "url": page.url})

                elif self._action == "click":
                    await page.click(self._selector)
                    return ToolResult(success=True, data={"clicked": self._selector})

                elif self._action == "type":
                    await page.fill(self._selector, value)
                    return ToolResult(success=True, data={"typed": value, "into": self._selector})

                elif self._action == "screenshot":
                    bytes_data = await page.screenshot()
                    return ToolResult(success=True, data={"screenshot": bytes_data.hex(), "format": "png"})

                elif self._action == "extract":
                    texts = await page.locator(self._selector).all_text_contents()
                    return ToolResult(success=True, data={"texts": texts})

                await browser.close()
                return ToolResult(success=False, error=f"Unknown action: {self._action}")
        except ImportError:
            return ToolResult(success=False, error="playwright not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
