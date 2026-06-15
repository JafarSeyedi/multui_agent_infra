from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class ComputerUseExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "computer_use"

    @property
    def description(self) -> str:
        return "Browser automation via Playwright"

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "navigate")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=kwargs.get("headless", True))
                page = await browser.new_page()

                if action == "navigate":
                    url = kwargs.get("url", "")
                    await page.goto(url)
                    return ToolResult(success=True, data={"title": await page.title(), "url": page.url})

                elif action == "click":
                    selector = kwargs.get("selector", "")
                    await page.click(selector)
                    return ToolResult(success=True, data={"clicked": selector})

                elif action == "type":
                    selector = kwargs.get("selector", "")
                    value = kwargs.get("value", "")
                    await page.fill(selector, value)
                    return ToolResult(success=True, data={"typed": value, "into": selector})

                elif action == "screenshot":
                    bytes_data = await page.screenshot()
                    return ToolResult(success=True, data={"screenshot": bytes_data.hex(), "format": "png"})

                elif action == "extract":
                    selector = kwargs.get("selector", "")
                    texts = await page.locator(selector).all_text_contents()
                    return ToolResult(success=True, data={"texts": texts})

                await browser.close()
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except ImportError:
            return ToolResult(success=False, error="playwright not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
