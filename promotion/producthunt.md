# ProductHunt Launch Page

---

## Listing Details

**Product Name:** TokenSaver

**Tagline (max 60 chars):**
> Self-hosted LLM cost governance with active prompt deduplication

**Description:**
> TokenSaver is a self-hosted caching proxy + management dashboard that cuts your LLM API costs by eliminating duplicate prompts.

**Key differentiator:**
> Unlike usage monitors (which only show what you spent), TokenSaver actively saves money by catching repeated and near-identical prompts before they reach the API.

---

## Full Description (for the "About" section)

```
TokenSaver is a self-hosted caching proxy that saves you money on LLM API calls by deduplicating prompts — both exact duplicates (SHA256 hash) and semantic duplicates (embedding similarity).

**How it works:**
Your apps point to TokenSaver's proxy instead of the LLM API directly. The proxy checks every incoming prompt against its cache:
→ Exact match found? Returns cached response in ~5ms — zero cost.
→ Semantic match found (cosine similarity ≥0.92)? Returns cached response — zero cost.
→ No match? Forwards to the upstream API, caches the response for next time.

**What's included:**
• Caching Proxy (port 8788) — exact SHA256 + semantic embedding cache with 14-model pricing table
• Manager Dashboard (port 3001) — 9 pages with per-user budgets, Slack/email alerts, per-model cost analytics, anomaly detection, CSV reports
• Rate limiting per API key with configurable window
• Per-user budget tracking with alerts at 50%/80%/100%
• 7-day usage sparklines per user
• Model breakdown with donut chart
• CSV report exports (usage, budgets, anomalies)
• Anomaly detection (rolling 24h std-dev)

**Pricing (no monthly subscriptions):**
• Free (MIT): ≤5 users, all features — no registration needed
• Pro: ₹8,500 / $99 one-time — unlimited users, 1yr updates
• Enterprise: ₹50,000 / $500 — standalone mode + data ingestion

**Technical:**
• Python + FastAPI + SQLite + sentence-transformers + Docker
• Drop-in replacement for https://api.openai.com
• 3 Docker services, single docker-compose up
• All data stays on your infrastructure
```

---

## First Comment (maker comment — pin this)

> Hey ProductHunt! 👋
> 
> I built TokenSaver because my team was paying for the same GPT-4o calls 3-4 times without realizing it.
> 
> The key insight: most teams send the same prompts repeatedly — retries after timeouts, multiple devs building the same feature, dashboard refreshes. A SHA256 cache catches exact duplicates. A semantic embedding cache catches near-identical queries.
> 
> It's self-hosted with Docker, works with any OpenAI-compatible client. Free for small teams (MIT license).
> 
> Built solo from Mumbai, India. Would love your feedback!

---

## Screenshots (attach in order)

1. `screenshots/overview.png` — Dashboard overview with stats cards and top users
2. `screenshots/models.png` — Per-model cost breakdown with donut chart
3. `screenshots/users.png` — User management page
4. `screenshots/budgets.png` — Budget tracking page
5. `screenshots/alerts.png` — Budget alerts history
6. `screenshots/proxy.png` — Proxy stats page with cache hit rate
7. `screenshots/reports.png` — CSV report exports

---

## Topics / Tags

- Developer Tools
- Artificial Intelligence
- Open Source
- Python
- Docker

---

## Launch Checklist

- [ ] Create/verify ProductHunt account (use kunalmavani@outlook.com)
- [ ] Schedule launch for Tuesday or Wednesday morning (US time = evening IST)
- [ ] Upload all 7 screenshots
- [ ] Upload maker photo (your profile pic)
- [ ] Paste the maker comment above as the first comment
- [ ] Share the ProductHunt link on Twitter, LinkedIn, and Reddit after launch
- [ ] Reply to every comment within 2 hours
