"""Async poller for Headroom proxy stats."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import httpx

from .config import config
from .database import insert_snapshot, insert_usage, get_recent_snapshots
from .models import HeadroomSnapshot

logger = logging.getLogger(__name__)

HEADROOM_URL = config.headroom_url.rstrip("/")

async def fetch_json(endpoint: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON from a Headroom endpoint, return None on failure."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{HEADROOM_URL}{endpoint}")
            if r.status_code == 200:
                return r.json()
            logger.warning("Headroom %s returned HTTP %d", endpoint, r.status_code)
    except httpx.RequestError as e:
        logger.warning("Headroom %s unreachable: %s", endpoint, e)
    return None

async def poll_health() -> Dict[str, Any]:
    """Fetch /health endpoint."""
    data = await fetch_json("/health")
    if data:
        return data
    return {"status": "offline"}

async def poll_stats() -> Dict[str, Any]:
    """Fetch /stats endpoint for token savings data."""
    data = await fetch_json("/stats")
    if data:
        return data
    return {}

async def poll_metrics() -> str:
    """Fetch /metrics endpoint (Prometheus format)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{HEADROOM_URL}/metrics")
            if r.status_code == 200:
                return r.text
    except httpx.RequestError:
        pass
    return ""

async def parse_metrics_prometheus(text: str) -> Dict[str, int]:
    """Parse Prometheus metrics for cache hits and requests."""
    result = {"cache_hits": 0, "cache_misses": 0, "total_requests": 0}
    if not text:
        return result
    for line in text.split("\n"):
        if line.startswith("#") or not line.strip():
            continue
        if "headroom_cache_hits" in line and "{" not in line.split(" ")[0]:
            try:
                result["cache_hits"] = int(line.split()[-1])
            except (IndexError, ValueError):
                pass
        if "headroom_requests_total" in line:
            try:
                result["total_requests"] = int(line.split()[-1])
            except (IndexError, ValueError):
                pass
    return result

async def poll_and_store() -> Dict[str, Any]:
    """Complete poll cycle: fetch all Headroom endpoints and store to DB.
    In standalone mode, returns empty data without connecting."""
    if config.standalone_mode:
        return {"health": "standalone", "tokens_saved": 0, "savings_percent": 0, "cache_hits": 0, "cost_saved": 0}
    health = await poll_health()
    stats = await poll_stats()
    metrics_text = await poll_metrics()
    metrics = await parse_metrics_prometheus(metrics_text)
    
    now = datetime.now(timezone.utc).isoformat()
    
    tokens_saved = stats.get("tokens_saved", 0) or stats.get("persistent_savings", {}).get("tokens_saved", 0)
    savings_percent = stats.get("savings_percent", 0) or stats.get("persistent_savings", {}).get("savings_percent", 0)
    total_requests = stats.get("total_requests", 0) or metrics.get("total_requests", 0)
    cost_saved = stats.get("estimated_cost_saved_usd", 0) or stats.get("persistent_savings", {}).get("estimated_cost_saved_usd", 0)
    
    snapshot = HeadroomSnapshot(
        timestamp=now,
        total_requests=total_requests,
        tokens_saved=tokens_saved,
        savings_percent=float(savings_percent) if savings_percent else 0.0,
        cache_hits=metrics.get("cache_hits", 0),
        cache_misses=metrics.get("cache_misses", 0),
        total_cost_saved=float(cost_saved) if cost_saved else 0.0,
    )
    insert_snapshot(snapshot)
    
    # Also store as a general usage record for trend tracking
    insert_usage({
        "timestamp": now,
        "user_id": None,
        "team_id": None,
        "model": "headroom-proxy",
        "provider": "headroom",
        "endpoint": "/stats",
        "tokens_before": 0,
        "tokens_after": 0,
        "tokens_saved": tokens_saved,
        "cost_estimated": float(cost_saved) if cost_saved else 0.0,
        "cache_hits": metrics.get("cache_hits", 0),
    })
    
    return {
        "health": health.get("status", "unknown"),
        "tokens_saved": tokens_saved,
        "savings_percent": savings_percent,
        "cache_hits": metrics.get("cache_hits", 0),
        "cost_saved": cost_saved,
    }

async def get_headroom_status() -> str:
    """Quick health check, returns 'running', 'offline', or 'standalone'."""
    if config.standalone_mode:
        return "standalone"
    health = await poll_health()
    status = health.get("status", "")
    if status in ("healthy", "ok", "running") or health.get("ready") is True:
        return "running"
    return "offline"

async def periodic_poll():
    """Run poll_and_store every N seconds (runs forever).
    In standalone mode, this is a no-op."""
    if config.standalone_mode:
        logger.info("Standalone mode — poller disabled")
        return
    logger.info("Starting Headroom poller (interval: %ss)", config.poll_interval_seconds)
    while True:
        try:
            result = await poll_and_store()
            logger.debug("Polled Headroom: %s", result.get("health", "unknown"))
        except Exception as e:
            logger.error("Headroom poll failed: %s", e)
        await asyncio.sleep(config.poll_interval_seconds)
