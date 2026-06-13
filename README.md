# TokenSaver

Self-hosted LLM cost governance dashboard. Track who in your team is spending what on AI APIs, set per-user budgets, get Slack alerts, surfacing cache hit rates from the Headroom proxy.

**Free for individuals (≤5 users, MIT). Pro at ₹8,500 / $99 one-time for organizations.**

---

## Features

- **Per-User Budget Tracking** — Set monthly budgets per user/team, see who's at 50%, 80%, or over budget
- **Slack Alerts** — Get notified when someone crosses a budget threshold
- **LLM Cost Dashboard** — Server-rendered HTML with Chart.js graphs — 7 pages: Overview, Users, Teams, Budgets, Alerts, Reports, Settings
- **Cache Hit Rate Visibility** — Surface Headroom's semantic cache hit/miss rates
- **Anomaly Detection** — Rolling 24h std-dev detection for cost spikes and compression drops
- **CSV Reports** — Export usage, budget, and anomaly reports
- **License Key System** — SHA256-verified Pro keys for unlimited users
- **One Docker Image** — Headroom + Manager in a single stack

---

## Architecture

```
Your Apps → Headroom (:8787) → OpenAI / Anthropic
               ↓ polls /stats+/metrics every 60s
        TokenSaver Manager (:3001)
        ├── Per-user budgets & tracking
        ├── Slack/webhook alerts
        ├── CSV report exports
        ├── Anomaly detection
        └── License verification
```

---

## Quick Start

### Prerequisites

- Python >= 3.10
- Headroom (`pip install headroom`)
- Docker (optional)

### Run Natively

```bash
pip install -r requirements.txt
export HEADROOM_REQUIRE_RUST_CORE=false
headroom proxy --port 8787 --no-telemetry &
uvicorn manager.server:app --host 0.0.0.0 --port 3001
```

Open http://127.0.0.1:3001/manager/

### Run with Docker

```bash
docker-compose up
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENSAVER_MANAGER_PORT` | `3001` | Manager web UI port |
| `HEADROOM_URL` | `http://127.0.0.1:8787` | Headroom proxy address |
| `TOKENSAVER_DB_PATH` | `./data/savings.db` | SQLite database path |
| `TOKENSAVER_POLL_INTERVAL` | `60` | Headroom poll interval (s) |
| `TOKENSAVER_LICENSE_KEY` | `dev-mode` | License signing secret (set a strong random value in production!) |
| `TOKENSAVER_STANDALONE` | `false` | Enable standalone mode (Enterprise, no Headroom) |
| `SLACK_WEBHOOK_URL` | `` | Default Slack webhook |
| `HEADROOM_REQUIRE_RUST_CORE` | `false` | Disable Rust core requirement |
| `HEADROOM_TELEMETRY` | `off` | Disable telemetry |

---

## License & Pricing

**Free (MIT)** — Individuals, ≤5 users. No registration needed.

**Pro (₹8,500 / $99)** — Unlimited users + Slack alerts + CSV reports + 1yr updates.

To purchase: email `kunalmavani@outlook.com` with your team size. Pay via UPI to `9836050235` — you'll receive a license key within 1 hour.

---

## Project Structure

```
tokensaver/
├── manager/
│   ├── server.py            # FastAPI app (port 3001)
│   ├── database.py          # SQLite CRUD
│   ├── models.py            # Pydantic models
│   ├── config.py            # Env var config
│   ├── headroom_client.py   # Async Headroom poller
│   ├── budget_engine.py    # Budget tracking
│   ├── alerts.py            # Slack dispatch
│   ├── anomaly.py           # Std-dev anomaly detection
│   ├── license.py           # License key system
│   ├── reports.py           # CSV exports
│   └── templates/           # 8 Jinja2 templates
├── scripts/
│   ├── gen_license.py       # Generate Pro/Enterprise license keys
│   └── seed_demo.py         # Seed demo data for testing
├── docker-compose.yml       # Headroom proxy + Manager
├── Dockerfile
├── .dockerignore
└── requirements.txt
```

---

## License

MIT License — Copyright (c) 2026 Kunal. Pro features require a paid license for organizations.
