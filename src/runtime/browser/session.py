from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page, sync_playwright

from src.runtime.browser.engine import HermeticBrowser


@dataclass
class BrowserSession:
    chrome_path: Optional[str] = None
    headless: bool = True

    def __post_init__(self) -> None:
        self.chrome = HermeticBrowser(self.chrome_path)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page: Optional[Page] = None

    def start(self) -> None:
        if self._browser:
            return
        self.chrome.launch(headless=self.headless)
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp("http://localhost:9222")
        if self._browser.contexts:
            self._context = self._browser.contexts[0]
        else:
            self._context = self._browser.new_context()
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser session has no active page.")
        return self._page

    def navigate(self, url: str) -> str:
        self.start()
        self.page.goto(url, wait_until="domcontentloaded")
        return self.page.content()

    def click(self, selector: str) -> str:
        self.start()
        self.page.click(selector)
        return self.page.content()

    def type(self, selector: str, text: str, clear: bool = True) -> str:
        self.start()
        if clear:
            self.page.fill(selector, text)
        else:
            self.page.type(selector, text)
        return self.page.content()

    def screenshot(self, path: str) -> str:
        self.start()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.page.screenshot(path=path, full_page=True)
        return path

    def html(self) -> str:
        self.start()
        return self.page.content()

    def current_url(self) -> str:
        self.start()
        return self.page.url

    def close(self) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self.chrome.stop()
        self._context = None
        self._browser = None
        self._playwright = None
        self._page = None
