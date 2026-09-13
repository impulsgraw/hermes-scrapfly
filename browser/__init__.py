"""Scrapfly Cloud Browser plugin — installable, auto-loadable.

Provides a cloud browser backend that connects to Scrapfly's Cloud Browser
via a CDP WebSocket endpoint (``wss://browser.scrapfly.io``). Compatible with
Playwright, Puppeteer, Selenium, and agent-browser.

Config: ``browser.cloud_provider: "scrapfly"``
Env: ``SCRAPFLY_API_KEY`` (required)
"""

from __future__ import annotations

from .provider import ScrapflyBrowserProvider


def register(ctx) -> None:
    ctx.register_browser_provider(ScrapflyBrowserProvider())