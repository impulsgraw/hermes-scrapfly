"""Scrapfly web content extraction provider.

Uses the `Scrapfly Scrape API <https://scrapfly.io/docs/scrape-api>`_ to fetch
and extract clean content from web pages. Each URL is fetched individually via
``GET https://api.scrapfly.io/scrape`` with configurable output format
(``markdown`` by default, overridable via ``SCRAPFLY_FORMAT`` or the ``format``
kwarg).

Supports extract only (no native search endpoint); the ``web_extract`` tool
routes here when ``web.extract_backend`` (or ``web.backend``) is ``"scrapfly"``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from agent.secret_scope import get_secret
from plugins.web._common import (
    BaseWebSearchProvider,
    document,
    extract_fail,
    page_error,
    run_extract,
    setup_schema,
)

logger = logging.getLogger(__name__)

_SCRAPFLY_API_URL = "https://api.scrapfly.io"


class ScrapflyWebSearchProvider(BaseWebSearchProvider):
    """Scrapfly (https://scrapfly.io) web content extraction backend.

    Scrapfly is a managed scraping platform. This provider uses the Scrape API
    to extract clean content from URLs — ideal for feeding LLMs with sanitised
    markdown/text. It does **not** provide web search; for search use another
    backend like Tavily, Firecrawl, or Brave.
    """

    NAME = "scrapfly"
    DISPLAY_NAME = "Scrapfly"
    KEY_ENV = "SCRAPFLY_API_KEY"
    EXTRACT = True
    KEYLESS = False

    def supports_search(self) -> bool:
        """Scrapfly has no native web-search endpoint."""
        return False

    def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract content from *urls* via the Scrapfly Scrape API.

        Keyword Args:
            format: Output format — ``markdown``, ``text``, ``raw``,
                    ``clean_html``, or ``json``. Falls back to the
                    ``SCRAPFLY_FORMAT`` env var, then to ``"markdown"``.
            max_chars: If set, truncate each result's content to this many
                       characters (applied client-side after fetch).
        """
        api_key = get_secret("SCRAPFLY_API_KEY")
        if not api_key:
            return extract_fail(
                urls,
                "SCRAPFLY_API_KEY environment variable is not set. "
                "Get your key at https://scrapfly.io",
            )

        output_format = (
            kwargs.get("format")
            or (get_secret("SCRAPFLY_FORMAT") or "").strip()
            or "markdown"
        )
        max_chars = kwargs.get("max_chars")

        def _extract_one(url: str) -> Dict[str, Any]:
            try:
                params: Dict[str, str] = {
                    "key": api_key,
                    "url": url,
                    "format": output_format,
                }
                response = httpx.get(
                    f"{_SCRAPFLY_API_URL}/scrape",
                    params=params,
                    timeout=90.0,
                )
                response.raise_for_status()
                data = response.json()
                result = data.get("result", {}) if isinstance(data, dict) else {}
                content = result.get("content", "") or ""
                title = result.get("title", "") or ""
                if max_chars and isinstance(max_chars, int) and len(content) > max_chars:
                    content = content[:max_chars]
                return document(url, title, content)
            except httpx.HTTPStatusError as exc:
                detail = (
                    (exc.response.text or "").strip()[:300]
                    or f"HTTP {exc.response.status_code}"
                )
                logger.warning(
                    "Scrapfly extract HTTP %s for %s: %s",
                    exc.response.status_code,
                    url,
                    detail,
                )
                return page_error(url, f"HTTP {exc.response.status_code}: {detail}")
            except httpx.RequestError as exc:
                logger.warning("Scrapfly extract request error for %s: %s", url, exc)
                return page_error(url, f"Request failed: {exc}")
            except Exception as exc:  # noqa: BLE001 — per-URL error surface
                logger.warning("Scrapfly extract error for %s: %s", url, exc)
                return page_error(url, str(exc))

        return run_extract(
            "Scrapfly",
            logger,
            urls,
            lambda: [_extract_one(u) for u in urls],
        )

    def get_setup_schema(self) -> Dict[str, Any]:
        return setup_schema(
            "Scrapfly · Paid (API key)",
            "paid",
            "Web content extraction with anti-bot bypass, proxies, and JS rendering",
            key_env="SCRAPFLY_API_KEY",
            prompt="Scrapfly API key",
            url="https://scrapfly.io",
        )