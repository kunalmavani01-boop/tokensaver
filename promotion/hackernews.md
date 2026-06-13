# Hacker News — Show HN Post

## Title (pick one)

**Option A** (direct):
> Show HN: TokenSaver – Self-hosted caching proxy that cuts LLM API costs by deduplicating prompts

**Option B** (problem-focused):
> Show HN: TokenSaver – I built an open-source cache that saved my team 40% on GPT-4o bills

**Option C** (technical):
> Show HN: TokenSaver – Prompt deduplication (exact SHA256 + semantic embeddings) for any LLM API

---

## First Comment (paste as soon as post goes live)

```
I built TokenSaver because my team hit the same problem: 3 devs sending identical prompts to GPT-4o, paying 3x for the same work.

It's a self-hosted caching proxy that sits between your app and the LLM API:

• Exact-match cache – SHA256 hashes every prompt, returns cached response for duplicates in ~5ms
• Semantic cache – sentence-transformers embeddings (cosine similarity ≥0.92) catch near-identical queries with different wording
• Rate limiting – per-API-key configurable limits
• Per-user/team budgets with Slack + email alerts at 50/80/100%
• Per-model cost breakdown (see which model is draining your budget)
• Anomaly detection – rolling std-dev detection for cost spikes
• Docker-based, 3 services (proxy :8788 → manager :3001)

Drop-in replacement for https://api.openai.com – just change base_url.

Free for ≤5 users (MIT), Pro ₹8,500 / $99 one-time for unlimited users.

GitHub: https://github.com/kunalmavani01-boop/tokensaver

Would love feedback on the semantic caching threshold (defaulting to 0.92 cosine similarity).
```

---

## Anticipated Questions & Answers

**Q: Doesn't OpenAI already cache?**
A: OpenAI caches at their end between API key usages, but they still charge for cache hits at a reduced rate. TokenSaver caches locally — zero cost for repeat prompts. Plus it catches semantic duplicates across your whole team.

**Q: Why not just use Redis?**
A: Redis works for exact-match key-value. TokenSaver's semantic cache uses embeddings (sentence-transformers) to catch approximate duplicates — "summarize Q3 results" vs "can you summarize Q3 financial results" – which Redis alone can't handle.

**Q: How much does it actually save?**
A: In my testing with a 3-person team, ~30-40% of prompts were near-duplicates. YMMV based on team size and workflow.

**Q: Is it production-ready?**
A: It's v1.0 with 35 automated tests and 17 clean modules. I'd recommend testing with 10% traffic first and scaling up.
