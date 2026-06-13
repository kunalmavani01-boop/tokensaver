# LinkedIn Post

---

## Draft

*[Attach screenshot of the dashboard overview page]*

**I just open-sourced TokenSaver — a self-hosted LLM cost governance tool.**

The problem: My team was paying for the same GPT-4o responses 3-4 times because different devs sent identical prompts. No visibility into who was spending what.

The solution:
→ A caching proxy that deduplicates prompts — SHA256 for exact matches, sentence-transformers embeddings for semantic duplicates
→ Per-user budgets with Slack and email alerts at 50%, 80%, and 100% thresholds
→ Per-model cost analytics — see exactly which model is draining your budget
→ Rate limiting per API key
→ All self-hosted with Docker — your data never leaves your infrastructure

Built entirely solo from Mumbai, zero budget.

**Pricing** (no monthly subscriptions):
• Free (MIT) for ≤5 users — all features included
• Pro at ₹8,500 / $99 one-time for unlimited users
• Enterprise at ₹50,000 / $500 with standalone mode

Tech stack: Python, FastAPI, SQLite, sentence-transformers, Docker, Chart.js

GitHub: https://github.com/kunalmavani01-boop/tokensaver

If you're managing LLM costs for your team, I'd love your feedback. ☕

#LLM #OpenSource #CostOptimization #AI #Startup #India #Python

---

## Alternative short version

**I built a caching proxy that cut my team's GPT-4o bill by 40%. It's now open-source.**

TokenSaver sits between your app and the LLM API. Every prompt gets hashed — exact duplicates return cached responses instantly. For near-identical queries, it uses embedding similarity to catch retries with different wording.

Also includes: per-user budgets, Slack/email alerts, per-model analytics, rate limiting.

Self-hosted, Docker, free for ≤5 users. Pro is ₹8,500 one-time (not a subscription).

https://github.com/kunalmavani01-boop/tokensaver

#LLM #OpenSource #DevTools
