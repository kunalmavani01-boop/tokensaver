# IndieHackers Post

---

## Title

> How I built TokenSaver – an open-source LLM cost governance tool solo from Mumbai

---

## Body

**The problem**

My team of 3 was spending ~$150/month on GPT-4o. When I looked at the actual usage, I realized ~40% of calls were duplicates — same prompts sent by different devs, retries after timeouts, dashboard refreshes. We were burning money on exactly the same work.

**The idea**

A caching proxy that sits between your app and the LLM API. First request goes upstream, response is cached. Second identical request returns the cached response instantly — zero cost.

I added semantic embeddings (sentence-transformers all-MiniLM-L6-v2) to catch near-identical queries — "summarize Q3 results" vs "can you summarize Q3 financial results" — which a simple hash can't detect.

**Building it**

Stack: Python, FastAPI, SQLite, sentence-transformers, Docker, Chart.js.

Key decisions:
- SQLite over Redis — zero infrastructure, one file, good enough for teams
- sentence-transformers over an external embedding API — self-hosted, no recurring cost
- Starlette Templates for the dashboard — no JavaScript framework, simpler to maintain
- Polling over websockets — the proxy reports stats every 5 minutes via POST

Hardest part: The semantic cache. Getting the embedding model to load fast, tuning the cosine similarity threshold, and making sure the vector comparison didn't become a bottleneck.

**Pricing model**

I went with one-time payments instead of SaaS:
- Free (MIT): ≤5 users, all features
- Pro: ₹8,500 / $99 one-time — unlimited users, 1yr updates
- Enterprise: ₹50,000 — standalone mode + data ingestion

Why? The Indian market is price-sensitive. Monthly SaaS fees are a non-starter for most Indian startups. One-time payments at Indian pricing tiers unlock a market that most US-focused tools ignore.

**Revenue**

₹0 so far — launching today!

**Marketing plan**

- Hacker News Show HN
- ProductHunt launch
- Reddit (r/developersIndia, r/LocalLLaMA, r/SideProject, r/opensource)
- LinkedIn post
- Twitter thread

**Lessons so far**

1. Building is the easy part. Marketing is harder.
2. The 5-user free tier is a conversion mechanic — teams try it free, upgrade when they grow.
3. Pricing in INR opens a huge market (1.4B people, thousands of dev teams).
4. Self-hosted tools have a real advantage in India where data residency concerns are growing.

**Links**

GitHub: https://github.com/kunalmavani01-boop/tokensaver
Email: kunalmavani@outlook.com
UPI: 9836050235 (India payments)
