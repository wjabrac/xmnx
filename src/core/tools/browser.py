from __future__ import annotations

import os
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field

from src.interfaces.tool import Tool
from src.runtime.browser.dom_parser import DomParser
from src.runtime.browser.session import BrowserSession


class BrowserInput(BaseModel):
    action: Literal["navigate", "click", "type", "screenshot", "html", "close"] = Field(
        ..., description="Browser action to perform."
    )
    url: Optional[str] = Field(None, description="URL to navigate to.")
    selector: Optional[str] = Field(None, description="CSS selector for click/type.")
    text: Optional[str] = Field(None, description="Text to type into the selector.")
    clear: bool = Field(True, description="Clear the input before typing.")
    screenshot_path: Optional[str] = Field(
        None, description="Path to save the screenshot."
    )
    markdown: bool = Field(
        True, description="Return markdown instead of raw HTML when available."
    )


class BrowserTool(Tool):
    name = "browser"
    description = (
        "Control a browser session. Supports navigation, clicking, typing, "
        "HTML retrieval, and screenshots."
    )
    input_model = BrowserInput

    def __init__(self, chrome_path: Optional[str] = None, headless: bool = True):
        env_path = os.getenv("BROWSER_CHROME_PATH")
        self.session = BrowserSession(chrome_path=chrome_path or env_path, headless=headless)
        self.parser = DomParser()

    def run(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        clear: bool = True,
        screenshot_path: Optional[str] = None,
        markdown: bool = True,
    ) -> Any:
        if action == "navigate":
            if not url:
                return {"error": "url is required for navigate"}
            html = self.session.navigate(url)
        elif action == "click":
            if not selector:
                return {"error": "selector is required for click"}
            html = self.session.click(selector)
        elif action == "type":
            if not selector or text is None:
                return {"error": "selector and text are required for type"}
            html = self.session.type(selector, text, clear=clear)
        elif action == "screenshot":
            if not screenshot_path:
                return {"error": "screenshot_path is required for screenshot"}
            path = self.session.screenshot(screenshot_path)
            return {"status": "success", "path": path, "url": self.session.current_url()}
        elif action == "html":
            html = self.session.html()
        elif action == "close":
            self.session.close()
            return {"status": "closed"}
        else:
            return {"error": f"Unsupported action: {action}"}

        content = self.parser.to_markdown(html) if markdown else html
        return {
            "content": content,
            "url": self.session.current_url(),
            "markdown": markdown,
        }
