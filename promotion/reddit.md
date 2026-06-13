# Reddit Posts

---

## r/developersIndia (priority — India market wide open)

**Title:**
> I built an open-source LLM cost saver — priced in ₹ for Indian teams

**Body:**
```
TokenSaver is a self-hosted caching proxy that sits between your app and OpenAI/Anthropic/etc:

• Exact-match cache (SHA256) — stops paying for identical prompts repeated by different devs
• Semantic cache (embedding similarity) — catches "summarize this" vs "give me a summary of this"
• Per-user budget tracking with Slack + email alerts
• Per-model cost breakdown
• Rate limiting per API key
• Docker-based, self-hosted — your data never leaves your infra

Pricing in INR because Indian startups shouldn't pay US SaaS prices:
→ Free (MIT): ≤5 users, all features
→ Pro: ₹8,500 one-time — unlimited users, 1yr updates
→ Enterprise: ₹50,000 — includes standalone mode + data ingestion

Built solo from Mumbai. Would love feedback from Indian devs who manage LLM costs.

GitHub: https://github.com/kunalmavani01-boop/tokensaver
Email: kunalmavani@outlook.com
```

---

## r/LocalLLaMA

**Title:**
> TokenSaver – Open-source caching proxy with semantic dedup for any LLM API

**Body:**
```
For those running self-hosted LLM setups or proxying to commercial APIs, I built a caching proxy that uses sentence-transformers for semantic prompt deduplication.

The stack:
• SHA256 exact-match cache in SQLite (5ms lookup)
• all-MiniLM-L6-v2 embeddings for semantic similarity (cosine ≥0.92 threshold)
• Per-model pricing table (14 models from GPT-4o to Llama 3)
• Rate limiting per API key
• Reports stats to a Manager dashboard every 5 min

The semantic cache runs entirely locally (~90MB model, no external API). Threshold is configurable via env var.

GitHub (MIT): https://github.com/kunalmavani01-boop/tokensaver

Curious what similarity threshold you all use in production for semantic caching of LLM prompts.
```

---

## r/SideProject

**Title:**
> I built TokenSaver – solo from Mumbai, zero budget, open-source LLM cost governance

**Body:**
```
Six weeks ago I started building TokenSaver because my small team was spending too much on repeated LLM API calls.

What it does:
• Caching proxy that deduplicates prompts (exact + semantic)
• Budget management with Slack + email alerts
• Per-model cost analytics
• All self-hosted, no SaaS fees

Tech: Python + FastAPI + SQLite + sentence-transformers + Docker

The pricing model: Free (MIT) for ≤5 users, ₹8,500 one-time for Pro. No monthly subscriptions.

Revenue so far: ₹0 (launching today!)

GitHub: https://github.com/kunalmavani01-boop/tokensaver

Happy to answer any questions about the stack, pricing, or the Indian market opportunity.
```

---

## r/opensource

**Title:**
> TokenSaver – MIT-licensed LLM cost governance with prompt caching, budgets, and alerts

**Body:**
```
We just open-sourced TokenSaver v1.0 under MIT for ≤5 users.

It's a self-hosted caching proxy + management dashboard for controlling LLM API costs:

• Exact-match and semantic prompt caching
• Per-user budget tracking
• Slack + email budget alerts
• Rate limiting
• Model-level cost analytics
• Anomaly detection
• CSV report exports

The free tier is fully MIT — all features, no restrictions except the 5-user limit. Pro is a one-time purchase for unlimited users.

Docker single-command setup.

GitHub: https://github.com/kunalmavani01-boop/tokensaver
```

---

## Posting Schedule

| Subreddit | Best time (IST) | Notes |
|-----------|----------------|-------|
| r/developersIndia | 10 AM - 12 PM | Weekdays. Title should include ₹ pricing |
| r/LocalLLaMA | 6 PM - 10 PM | Technical audience, focus on semantic cache |
| r/SideProject | 8 AM - 10 AM | Focus on the solo-founder story |
| r/opensource | 12 PM - 2 PM | Focus on MIT license, self-hosted |
