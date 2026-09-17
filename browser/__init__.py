"""Scrapfly Cloud Browser plugin — installable, auto-loadable.

Provides a cloud browser backend that connects to Scrapfly's Cloud Browser
via a CDP WebSocket endpoint (``wss://browser.scrapfly.io``). Compatible with
Playwright, Puppeteer, Selenium, and agent-browser.

Config: ``browser.cloud_provider: "scrapfly"``
Env: ``SCRAPFLY_API_KEY`` (required)

Single-connection constraint
----------------------------
Scrapfly allows exactly ONE live CDP connection per session: a second
concurrent WebSocket drops the first. Hermes' persistent CDP supervisor and
agent-browser's daemon both want a socket on the same session URL, so the
supervisor is suppressed for sessions that declare ``features.single_connection``
(see :func:`_patch_cdp_supervisor`).
"""

from __future__ import annotations

from .provider import ScrapflyBrowserProvider

_PATCH_MARKER = "_scrapfly_single_connection_patch"


def _ensure_cdp_supervisor_gated(task_id: str) -> None:
    """Skip the CDP supervisor for single-connection sessions; delegate otherwise.

    Scrapfly's one-connection-per-session model means the supervisor's persistent
    WebSocket would steal the slot from agent-browser's daemon, killing in-flight
    commands with "CDP response channel closed". Sessions that declare
    ``features.single_connection`` skip the supervisor; everything else (including
    the explicit CDP-override path and other providers) delegates to the original.
    """
    try:
        from tools import browser_tool as _bt
        from tools import browser_tool_cdp as _cdp
    except Exception:  # pragma: no cover — plugin surface changed; fail safe
        return
    try:
        with _bt._cleanup_lock:
            session = _bt._active_sessions.get(task_id, {})
        if (session.get("features") or {}).get("single_connection"):
            return
    except Exception:
        pass
    _cdp._ensure_cdp_supervisor_orig(task_id)


def _patch_cdp_supervisor() -> None:
    """Wrap ``tools.browser_tool_cdp._ensure_cdp_supervisor`` once (idempotent).

    Runs from :func:`register`, which plugin discovery fires before the first
    browser command creates any session — so the very first supervisor start for
    a Scrapfly session is already gated. Non-single-connection sessions are
    untouched.
    """
    try:
        from tools import browser_tool_cdp as _cdp
    except Exception:  # pragma: no cover — hermes layout changed; do not break registration
        return
    if getattr(_cdp, _PATCH_MARKER, False):
        return
    _cdp._ensure_cdp_supervisor_orig = _cdp._ensure_cdp_supervisor
    _cdp._ensure_cdp_supervisor = _ensure_cdp_supervisor_gated
    setattr(_cdp, _PATCH_MARKER, True)


def register(ctx) -> None:
    ctx.register_browser_provider(ScrapflyBrowserProvider())
    _patch_cdp_supervisor()