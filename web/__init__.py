"""Scrapfly web content extraction plugin — installable, auto-loadable.

Provides a web extraction provider that uses the Scrapfly Scrape API
(``https://api.scrapfly.io/scrape``) to fetch clean, LLM-ready content from
web pages. Supports markdown, text, raw HTML, and clean HTML output formats
with full anti-bot bypass, proxy rotation, and JS rendering.

Config: ``web.extract_backend: "scrapfly"`` (or ``web.backend: "scrapfly"``)
Env: ``SCRAPFLY_API_KEY`` (required), ``SCRAPFLY_FORMAT`` (default ``markdown``)
"""

from __future__ import annotations

from .provider import ScrapflyWebSearchProvider


def register(ctx) -> None:
    ctx.register_web_search_provider(ScrapflyWebSearchProvider())