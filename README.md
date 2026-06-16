# TokenSaver

Self-hosted LLM cost governance stack with **active token saving** — prompt deduplication (exact + semantic), rate limiting, per-user/team budgets, Slack + email alerts, anomaly detection, CSV reports, and per-model cost analytics.

**Free for individual use (≤5 users) under the included community license. Pro at ₹8,500 / $99 one-time for organizations. Enterprise at ₹50,000 / $500 with standalone mode + data ingestion.**

---

## Features

### Save Money
- **Exact Prompt Caching** — SHA256-hashes every prompt, returns cached response for exact duplicates (retries, refreshes)
- **Semantic Caching** — sentence-transformers embeddings (cosine similarity ≥0.92) catch near-identical queries — same intent, different wording
- **14-Model Pricing Table** — GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Llama 3, and 10 more — accurate cost-per-cache-hit estimates

### Control Usage
- **Rate Limiting** — Per-API-key request cap with rolling window (configurable requests / seconds)
- **Per-User Budgets** — Set monthly budgets, see who's at 50%, 80%, or over budget when requests are attributed to users
- **Anomaly Detection** — Rolling 24h std-dev detection for cost spikes and compression drops

### Stay Informed
- **Slack Alerts** — Automatic notifications at 50% / 80% / 100% of attributed budget usage
- **Email Alerts** — SMTP-based budget threshold emails (works with Gmail, SendGrid, any SMTP)
- **Model Analytics** — Per-model cost breakdown with donut chart
- **Per-User Spend Charts** — 7-day usage sparklines for every user

### Export & Integrate
- **CSV Reports** — Usage, budget, and anomaly reports
- **Data Ingestion** — Add usage records via form, CSV upload, or JSON API (Enterprise)
- **OpenAI-Compatible** — Drop-in replacement for `https://api.openai.com` — just change your `base_url`

---

## Architecture

```
Your Apps → Caching Proxy (:8788) → OpenAI / Anthropic / any LLM API
                │
                ├── Exact-match cache (SHA256 hash)
                ├── Semantic cache (embedding similarity)
                ├── Rate limiting (per API key)
                └── Stats report every 5 min
                     │
                TokenSaver Manager (:3001)
                ├── Per-user budgets
                ├── Slack + email alerts
                ├── Model cost analytics
                ├── Anomaly detection
                ├── CSV report exports
                ├── License verification
                └── Usage dashboard (9 pages)
```

---

## Quick Start

### Prerequisites
- Python >= 3.10
- `pip install -r requirements.txt`
- Docker (optional)

### Native (Windows PowerShell)
```powershell
.\start_tokensaver.ps1
```
Opens: http://127.0.0.1:3001/manager/

### Native (Linux / macOS)
```bash
./start.sh
```

### Docker
```bash
docker-compose up
```

### Connect Your Apps
Point any OpenAI-compatible client to the Caching Proxy:
```python
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:8788/v1",  # ← TokenSaver proxy
    api_key="sk-your-real-api-key"
)
```

### Attribute Requests To Users
If you want live per-user budgets, alerts, and analytics from proxy traffic, send one of these headers with each request:

- `X-TokenSaver-User-Id`
- `X-TokenSaver-User-Email`
- `X-TokenSaver-User-Api-Key`
- optional `X-TokenSaver-Team-Id`

TokenSaver uses these headers for internal attribution only and does not forward them upstream.

---

## Configuration

### Manager
| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENSAVER_MANAGER_PORT` | `3001` | Manager web UI port |
| `HEADROOM_URL` | `http://127.0.0.1:8787` | Headroom proxy address |
| `TOKENSAVER_DB_PATH` | `./data/savings.db` | SQLite database path |
| `TOKENSAVER_POLL_INTERVAL` | `60` | Headroom poll interval (s) |
| `TOKENSAVER_LICENSE_KEY` | `dev-mode` | License signing secret (set a strong random value in production!) |
| `TOKENSAVER_STANDALONE` | `false` | Enable standalone mode (Enterprise, no Headroom) |
| `SLACK_WEBHOOK_URL` | `` | Default Slack webhook |
| `TOKENSAVER_SMTP_HOST` | `` | SMTP server hostname (enables email alerts) |
| `TOKENSAVER_SMTP_PORT` | `587` | SMTP port |
| `TOKENSAVER_SMTP_USER` | `` | SMTP username |
| `TOKENSAVER_SMTP_PASSWORD` | `` | SMTP password |
| `TOKENSAVER_SMTP_FROM` | `tokensaver@localhost` | From address for alert emails |
| `TOKENSAVER_INTERNAL_TOKEN` | `` | Optional shared token for proxy-to-manager internal APIs |
| `HEADROOM_REQUIRE_RUST_CORE` | `false` | Disable Rust core requirement |
| `HEADROOM_TELEMETRY` | `off` | Disable telemetry |

### Caching Proxy
| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENSAVER_PROXY_PORT` | `8788` | Proxy server port |
| `TOKENSAVER_PROXY_UPSTREAM` | `https://api.openai.com` | Upstream LLM API |
| `TOKENSAVER_CACHE_TTL` | `24` | Cache entry TTL (hours) |
| `TOKENSAVER_SEMANTIC_THRESHOLD` | `0.92` | Cosine similarity threshold for semantic cache |
| `TOKENSAVER_RATE_LIMIT_REQUESTS` | `0` | Max requests per window (0 = unlimited) |
| `TOKENSAVER_RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |
| `OPENAI_API_KEY` | `` | Default upstream API key |
| `ANTHROPIC_API_KEY` | `` | Alternative upstream API key |

---

## License & Pricing

| Tier | Price | Users | Features |
|------|-------|-------|----------|
| **Free** | Community license | ≤5 | Individual use, evaluation, and local testing. |
| **Pro** | ₹8,500 / $99 | Unlimited | All features + unlimited users + 1yr updates |
| **Enterprise** | ₹50,000 / $500 | Unlimited | All features + standalone mode + data ingestion (form, CSV, JSON API) |

To purchase: email `kunalmavani@outlook.com` with your team size. Pay via UPI to `9836050235` — you'll receive a license key within 1 hour.

---

## Project Structure

```
tokensaver/
├── manager/
│   ├── server.py            # FastAPI app (port 3001) — 9 pages, 8 APIs
│   ├── database.py          # SQLite CRUD — 8 tables
│   ├── models.py            # Pydantic models
│   ├── config.py            # Env var config
│   ├── headroom_client.py   # Async Headroom poller
│   ├── budget_engine.py     # Budget tracking
│   ├── alerts.py            # Slack + email dispatch
│   ├── email_alerts.py      # SMTP email alerts
│   ├── anomaly.py           # Std-dev anomaly detection
│   ├── license.py           # License key system
│   ├── ingestion.py         # Data ingestion (Enterprise)
│   ├── reports.py           # CSV exports + dashboard stats
│   └── templates/           # 12 Jinja2 templates
├── proxy/
│   ├── server.py            # Caching proxy FastAPI app (port 8788)
│   ├── cache.py             # SHA256 + semantic cache, rate limiting, pricing
│   ├── config.py            # Proxy env var config
│   └── models.py            # Pydantic models
├── scripts/
│   ├── gen_license.py       # Generate Pro/Enterprise license keys
│   └── seed_demo.py         # Seed demo data for testing
├── docker-compose.yml       # Headroom + Caching Proxy + Manager
├── Dockerfile
├── .dockerignore
├── .env.example
└── requirements.txt
```

---

## License

TokenSaver is distributed under the included TokenSaver Community License. Individual use is free. Organizational use requires a paid commercial license.
