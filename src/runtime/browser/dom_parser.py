from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup
from markdownify import markdownify


@dataclass
class DomParser:
    """
    Convert raw HTML into a cleaned, markdown-friendly representation.
    """

    def to_markdown(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        cleaned_html = str(soup)
        return markdownify(cleaned_html, heading_style="ATX").strip()
