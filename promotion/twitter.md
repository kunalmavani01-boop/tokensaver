# Twitter / X Thread

---

## Thread Draft (8 tweets)

*[Attach screenshot of overview dashboard as image]*

**Tweet 1:**
I built a thing: TokenSaver — a self-hosted caching proxy that reduced my team's LLM bill by 40%.

It's open-source and free for small teams. 🧵👇

**Tweet 2:**
The problem: 3 devs, same GPT-4o calls, paying 3x for identical responses. No visibility into who spends what. Every retry costs the same as the first call.

**Tweet 3:**
Solution: A caching proxy that sits between your app and the LLM API.

• SHA256 hash → exact duplicates return cached response in ~5ms
• Semantic embeddings → catches "summarize this" vs "give me a summary" (cosine similarity)
• Both run locally, no external API

**Tweet 4:**
Also built in:
• Per-user budgets with Slack + email alerts at 50/80/100%
• Rate limiting per API key
• Per-model cost breakdown (doughnut chart 🍩)
• 7-day usage sparklines per user
• Anomaly detection for cost spikes
• CSV report exports

**Tweet 5:**
Stack: Python + FastAPI + SQLite + sentence-transformers + Docker

Drop-in replacement for api.openai.com — just change your base_url.

3 Docker services: proxy (:8788) → manager dashboard (:3001)

**Tweet 6:**
Pricing (no subscriptions):
• Free (MIT): ≤5 users, all features
• Pro: ₹8,500 / $99 one-time — unlimited users
• Enterprise: ₹50,000 — standalone mode + data ingestion

Built solo from Mumbai, India 🇮🇳

**Tweet 7:**
GitHub: https://github.com/kunalmavani01-boop/tokensaver

If you manage LLM costs for your team, give it a star ⭐ and tell me what you think!

**Tweet 8:**
Also: payment via UPI to 9836050235 (India) — because Indian startups shouldn't need a credit card to buy good software.

#buildinpublic #opensource #LLM #AI #startup

---

## Quick Post (non-thread)

Self-hosted LLM cost governance is now open-source.

TokenSaver = caching proxy (exact + semantic dedup) + manager dashboard (budgets, alerts, analytics).

Docker-based, free for ≤5 users (MIT), ₹8,500 Pro.

GitHub: https://github.com/kunalmavani01-boop/tokensaver

#opensource #LLM #devtools
