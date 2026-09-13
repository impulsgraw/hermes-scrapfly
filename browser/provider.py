"""Scrapfly Cloud Browser provider.

Uses the `Scrapfly Cloud Browser API <https://scrapfly.io/docs/cloud-browser-api>`_
to provision remote Chromium sessions reachable via a CDP WebSocket URL
(``wss://browser.scrapfly.io``). Each ``create_session`` call builds a signed
WebSocket URL that agent-browser dials directly — no intermediary gateway.

Connection parameters (env vars, all optional):
  ``SCRAPFLY_BROWSER_PROXY_POOL``  — ``datacenter`` (default) or ``residential``
  ``SCRAPFLY_BROWSER_OS``          — ``linux``, ``windows``, ``macos``, or mobile
  ``SCRAPFLY_BROWSER_COUNTRY``     — ISO 3166-1 alpha-2 (e.g. ``us``)
  ``SCRAPFLY_BROWSER_SESSION_TTL`` — max session seconds (default 900, max 1800)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from agent.browser_provider import BrowserProvider
from agent.secret_scope import get_secret

logger = logging.getLogger(__name__)

_WS_BASE = "wss://browser.scrapfly.io"
_DEFAULT_PROXY_POOL = "residential"
_DEFAULT_OS = "linux"
_DEFAULT_TTL = 900
_MAX_TTL = 1800


class ScrapflyBrowserProvider(BrowserProvider):
    """Scrapfly (https://scrapfly.io) Cloud Browser backend.

    Provision a remote Chromium session via Scrapfly's CDP WebSocket endpoint.
    The returned ``cdp_url`` is a fully-formed ``wss://`` URL that agent-browser
    can connect to directly using Playwright, Puppeteer, or raw CDP.
    """

    provider_id = "scrapfly"
    label = "Scrapfly"
    setup_tag = "Cloud browser with anti-bot bypass, proxies, and OS fingerprinting"
    setup_env_vars: list = [
        {
            "key": "SCRAPFLY_API_KEY",
            "prompt": "Scrapfly API key",
            "url": "https://scrapfly.io",
        },
    ]

    @property
    def name(self) -> str:
        return self.provider_id

    @property
    def display_name(self) -> str:
        return self.label

    def is_available(self) -> bool:
        return bool(get_secret("SCRAPFLY_API_KEY"))

    def create_session(self, task_id: str) -> Dict[str, object]:
        """Create a new Cloud Browser session.

        Returns a session metadata dict with ``session_name``, ``bb_session_id``,
        ``cdp_url``, and ``features``. There is no separate REST create endpoint —
        the CDP URL encodes all configuration as query parameters and is dialled
        directly by agent-browser.
        """
        api_key = get_secret("SCRAPFLY_API_KEY")
        if not api_key:
            raise ValueError(
                "SCRAPFLY_API_KEY environment variable is required. "
                "Get your key at https://scrapfly.io"
            )

        proxy_pool = (
            (get_secret("SCRAPFLY_BROWSER_PROXY_POOL") or "").strip()
            or _DEFAULT_PROXY_POOL
        )
        os_fingerprint = (
            (get_secret("SCRAPFLY_BROWSER_OS") or "").strip() or _DEFAULT_OS
        )
        country = (get_secret("SCRAPFLY_BROWSER_COUNTRY") or "").strip()

        raw_ttl = (get_secret("SCRAPFLY_BROWSER_SESSION_TTL") or "").strip()
        try:
            ttl = int(raw_ttl) if raw_ttl else _DEFAULT_TTL
        except ValueError:
            logger.warning(
                "Invalid SCRAPFLY_BROWSER_SESSION_TTL value: %s, using default %d",
                raw_ttl,
                _DEFAULT_TTL,
            )
            ttl = _DEFAULT_TTL
        ttl = max(1, min(ttl, _MAX_TTL))

        session_id = f"hermes_{task_id}_{uuid.uuid4().hex[:8]}"

        params: Dict[str, str] = {
            "api_key": api_key,
            "proxy_pool": f"public_{proxy_pool}_pool",
            "os": os_fingerprint,
            "session": session_id,
            "timeout": str(ttl),
        }
        if country:
            params["country"] = country

        cdp_url = f"{_WS_BASE}?{urlencode(params)}"
        # The target URL isn't known at session-creation time (agent-browser navigates
        # later), so we omit ``target_url``. The proxy selection is therefore blind
        # to the destination — country pinning via ``country`` still applies.

        logger.info(cdp_url)

        logger.info(
            "Created Scrapfly Cloud Browser session %s (proxy=%s, os=%s, ttl=%ds)",
            session_id,
            proxy_pool,
            os_fingerprint,
            ttl,
        )
        return {
            "session_name": session_id,
            "bb_session_id": session_id,
            "cdp_url": cdp_url,
            "features": {
                "scrapfly": True,
                "proxy_pool": proxy_pool,
                "os": os_fingerprint,
                "country": country or None,
            },
        }

    def close_session(self, session_id: str) -> bool:
        """Scrapfly Cloud Browser sessions auto-close on CDP disconnect when
        ``auto_close=true`` (the default), or expire at their TTL. If a manual
        close is needed, a DELETE to the CDP endpoint is not documented — so
        this is a best-effort no-op that always reports success."""
        logger.debug(
            "Scrapfly Cloud Browser session %s will auto-close on disconnect or TTL expiry",
            session_id,
        )
        return True

    def emergency_cleanup(self, session_id: str) -> None:
        """Best-effort teardown from signal/atexit handlers. Sessions auto-close,
        so this is safe as a no-op."""
        logger.debug(
            "Emergency cleanup for Scrapfly session %s (auto-close on disconnect)",
            session_id,
        )

    def get_setup_schema(self) -> Optional[Dict[str, Any]]:
        return {
            "name": self.label,
            "badge": "paid",
            "tag": self.setup_tag,
            "env_vars": [dict(v) for v in self.setup_env_vars],
        }