"""TokenSaver Caching Proxy — OpenAI-compatible prompt deduplication with semantic search + rate limiting."""
import asyncio
import json
import logging
import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from .config import config
from .cache import (
    init_cache_db, get_cache_key, check_cache, set_cache,
    record_cache_hit, get_cache_stats, estimate_cost,
    check_semantic_cache, compute_embedding, messages_to_text,
    check_rate_limit,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="TokenSaver Caching Proxy", version="1.0.0")

init_cache_db()

UPSTREAM_TIMEOUT = 60

_manager_url = None


def get_manager_url() -> str:
    global _manager_url
    if _manager_url is None:
        port = os.environ.get("TOKENSAVER_MANAGER_PORT", "3001")
        _manager_url = os.environ.get("TOKENSAVER_MANAGER_URL", f"http://127.0.0.1:{port}")
    return _manager_url


async def periodic_report_stats():
    await asyncio.sleep(30)
    while True:
        try:
            stats = get_cache_stats()
            manager_url = get_manager_url()
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{manager_url}/manager/api/proxy/stats/json",
                    json={
                        "cache_hits": stats["total_cache_hits"],
                        "cache_misses": 0,
                        "tokens_saved": stats["tokens_saved"],
                        "cost_saved": stats["estimated_cost_saved"],
                        "total_requests": stats["total_cache_hits"],
                    }
                )
        except Exception as e:
            logger.debug("Failed to report stats to Manager: %s", e)
        await asyncio.sleep(300)


@app.on_event("startup")
async def startup():
    logger.info("TokenSaver Proxy starting on port %s", config.port)
    logger.info("Upstream: %s", config.upstream_url)
    logger.info("Cache TTL: %sh | Semantic threshold: %.2f | Rate limit: %s/%ss",
                config.cache_ttl_hours, config.semantic_threshold,
                config.rate_limit_requests or "unlimited", config.rate_limit_window_seconds)
    asyncio.create_task(periodic_report_stats())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tokensaver-proxy", "version": "1.0.0"}


@app.get("/stats")
async def stats():
    s = get_cache_stats()
    return {
        "cache_entries": s["total_entries"],
        "cache_hits_total": s["total_cache_hits"],
        "unique_prompts_cached": s["entries_with_hits"],
        "semantic_entries": s["semantic_entries"],
        "tokens_saved_total": s["tokens_saved"],
        "cost_saved_estimated": round(s["estimated_cost_saved"], 4),
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "gpt-4o")
    messages = body.get("messages", [])
    stream = body.get("stream", False)

    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    # Rate limiting by API key (if provided)
    auth = request.headers.get("authorization", "")
    identifier = auth.replace("Bearer ", "").strip() or "anonymous"
    allowed, retry_after = check_rate_limit(identifier)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after}s."
        )

    if stream:
        return StreamingResponse(
            _proxy_stream(model, messages, body),
            media_type="text/event-stream"
        )

    return await _cached_completion(model, messages, body)


async def _cached_completion(model: str, messages: list, body: dict) -> JSONResponse:
    cache_key = get_cache_key(messages, model)

    # 1. Exact hash match
    cached = check_cache(cache_key)
    if cached:
        record_cache_hit(cache_key)
        response_data = json.loads(cached["response"])
        response_data["cached"] = True
        response_data["cache_info"] = {
            "match": "exact",
            "hit_count": cached["hit_count"] + 1,
            "tokens_saved": cached["prompt_tokens"] + cached["completion_tokens"],
            "cost_saved": estimate_cost(model, cached["prompt_tokens"], cached["completion_tokens"]),
        }
        return JSONResponse(content=response_data)

    # 2. Semantic match (embedding similarity)
    semantic = check_semantic_cache(messages, model)
    if semantic:
        record_cache_hit(semantic["cache_key"])
        response_data = json.loads(semantic["response"])
        response_data["cached"] = True
        response_data["cache_info"] = {
            "match": "semantic",
            "hit_count": semantic["hit_count"] + 1,
            "tokens_saved": semantic["prompt_tokens"] + semantic["completion_tokens"],
            "cost_saved": estimate_cost(model, semantic["prompt_tokens"], semantic["completion_tokens"]),
        }
        return JSONResponse(content=response_data)

    # 3. Cache miss — forward to upstream
    result = await _forward_to_upstream(model, messages, body)

    if result and "usage" in result:
        usage = result["usage"]
        emb = compute_embedding(messages_to_text(messages))
        set_cache(cache_key, "", model, json.dumps(result),
                  usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
                  embedding=emb)

    return JSONResponse(content=result)


async def _proxy_stream(model: str, messages: list, body: dict):
    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
        headers = _get_headers(model)
        payload = {k: v for k, v in body.items() if k != "stream"}
        async with client.stream("POST", f"{config.upstream_url}/v1/chat/completions",
                                 json={**payload, "stream": True}, headers=headers) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk


def _get_headers(model: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if any(k in model for k in ("gpt", "o1", "o3")):
        headers["Authorization"] = f"Bearer {config.openai_api_key}"
    elif "claude" in model:
        headers["x-api-key"] = config.anthropic_api_key
        headers["anthropic-version"] = "2023-06-01"
    else:
        headers["Authorization"] = f"Bearer {config.openai_api_key}"
    return headers


async def _forward_to_upstream(model: str, messages: list, body: dict) -> dict:
    upstream = config.upstream_url.rstrip("/")
    headers = _get_headers(model)
    payload = {k: v for k, v in body.items() if k != "stream"}

    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
        resp = await client.post(
            f"{upstream}/v1/chat/completions",
            json={**payload, "messages": messages, "model": model},
            headers=headers,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])

    return resp.json()


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    body = await request.json()
    model = body.get("model", "text-embedding-3-small")
    upstream = config.upstream_url.rstrip("/")
    headers = _get_headers(model)

    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
        resp = await client.post(f"{upstream}/v1/embeddings", json=body, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])
    return resp.json()


if __name__ == "__main__":
    port = config.port
    uvicorn.run(app, host="0.0.0.0", port=port)
