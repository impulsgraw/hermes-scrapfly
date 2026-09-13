# Scrapfly Plugin for Hermes Agent

Plugins that integrate [Scrapfly.io](https://scrapfly.io) — a managed scraping platform — as a **web content extractor** and **cloud browser backend** for Hermes Agent.

## Structure

```
plugins/scrapfly/
├── README.md              # This file
├── web/                   # Web extract provider (Scrape API)
│   ├── __init__.py
│   ├── plugin.yaml
│   └── provider.py
└── browser/               # Cloud Browser provider (CDP WebSocket)
    ├── __init__.py
    ├── plugin.yaml
    └── provider.py
```

## HERMES COMPATIBILITY

This plugin is compatible with hermes v0.21.2 (v2026.9.11).


## Separability

The plugin source lives **outside** the `hermes-agent/` tree in `./plugins/scrapfly/`. 

To install into a Hermes Agent:

```bash
hermes install plugin git@github.com:impulsgraw/hermes-scrapfly.git/web
hermes install plugin git@github.com:impulsgraw/hermes-scrapfly.git/browser
```

Alternatively, copy (or symlink) the repo root contents directly into `~/.hermes/plugins/scrapfly/` — Hermes also loads user plugins from `$HERMES_HOME/plugins/`.

## .env Configuration

All configuration is read from Hermes' environment (`.env` file in `$HERMES_HOME/` or process environment).

### Required

| Variable | Description |
|---|---|
| `SCRAPFLY_API_KEY` | Your Scrapfly API key (find it at https://scrapfly.io/dashboard) |

### Optional — Web Extract

| Variable | Default | Description |
|---|---|---|
| `SCRAPFLY_FORMAT` | `markdown` | Output format: `markdown`, `text`, `raw`, `clean_html`, `json` |

### Optional — Cloud Browser

| Variable | Default | Description |
|---|---|---|
| `SCRAPFLY_BROWSER_PROXY_POOL` | `datacenter` | Proxy pool: `datacenter` or `residential` |
| `SCRAPFLY_BROWSER_OS` | `linux` | OS fingerprint: `linux`, `windows`, `macos`, `android`, `iphone`, `ipad` |
| `SCRAPFLY_BROWSER_COUNTRY` | (none) | ISO 3166-1 alpha-2 proxy country (e.g. `us`, `de`) |
| `SCRAPFLY_BROWSER_SESSION_TTL` | `900` | Max session seconds (min 1, max 1800) |

### Example `.env`

```bash
SCRAPFLY_API_KEY=scp-live-xxxxxxxxxxxxxxxx
SCRAPFLY_FORMAT=markdown
SCRAPFLY_BROWSER_PROXY_POOL=residential
SCRAPFLY_BROWSER_OS=macos
SCRAPFLY_BROWSER_COUNTRY=us
```

## Usage

After setting `SCRAPFLY_API_KEY`, the plugin is auto-discovered by Hermes. Select it via the `hermes tools` picker:

```bash
hermes tools
```

Or configure directly:

```bash
# Use Scrapfly for web content extraction:
hermes config set web.extract_backend scrapfly

# Use Scrapfly for cloud browser:
hermes config set browser.cloud_provider scrapfly
```

## API Coverage

| Feature | Endpoint | Notes |
|---|---|---|
| Web extract | `GET https://api.scrapfly.io/scrape` | Fetches clean content: markdown, text, HTML |
| Cloud Browser | `wss://browser.scrapfly.io` | CDP WebSocket for Playwright/Puppeteer/Selenium |

Scrapfly's Extract API (`POST /extraction`) and Screenshot API (`GET /screenshot`) are also available and could be added as additional providers in a future version of this plugin.

## References

- [Scrapfly Documentation](https://scrapfly.io/docs)
- [Scrape API Reference](https://scrapfly.io/docs/scrape-api)
- [Cloud Browser API Reference](https://scrapfly.io/docs/cloud-browser-api)
- [Hermes Plugin Guide](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)