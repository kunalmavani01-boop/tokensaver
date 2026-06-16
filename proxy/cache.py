"""Prompt caching engine — exact SHA256 + semantic embedding search, SQLite backed."""
import json
import hashlib
import sqlite3
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import numpy as np

from .config import config

logger = logging.getLogger(__name__)

DB_PATH = Path(config.db_path)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_embedder = None
_embedder_lock = threading.Lock()

MODEL_COSTS = {
    "gpt-4o": {"prompt": 0.01, "completion": 0.03},
    "gpt-4o-mini": {"prompt": 0.0015, "completion": 0.006},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    "claude-3.5-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3.5-haiku": {"prompt": 0.00025, "completion": 0.00125},
    "gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
    "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
    "llama-3-70b": {"prompt": 0.00065, "completion": 0.00079},
    "llama-3-8b": {"prompt": 0.00006, "completion": 0.00008},
}


def get_default_cost() -> Dict[str, float]:
    return {"prompt": 0.003, "completion": 0.015}


def get_embedder():
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
                    logger.info("Loaded embedding model (all-MiniLM-L6-v2)")
                except ImportError:
                    logger.warning("sentence-transformers not installed — semantic cache disabled")
                    _embedder = False
    return _embedder if _embedder is not False else None


def init_cache_db():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prompt_cache (
            cache_key TEXT PRIMARY KEY,
            model TEXT NOT NULL,
            messages_hash TEXT NOT NULL,
            response TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            embedding BLOB,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT,
            hit_count INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS proxy_metrics (
            metric_key TEXT PRIMARY KEY,
            metric_value REAL NOT NULL DEFAULT 0
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_id_ts ON rate_limits(identifier, timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON prompt_cache(expires_at)")
    conn.commit()
    conn.close()


def messages_to_text(messages: list) -> str:
    return " ".join(m.get("content", "") for m in messages)


def compute_embedding(text: str) -> Optional[np.ndarray]:
    embedder = get_embedder()
    if embedder is None:
        return None
    try:
        return embedder.encode(text, normalize_embeddings=True)
    except Exception as e:
        logger.warning("Embedding failed: %s", e)
        return None


def hash_messages(messages: list) -> str:
    normalized = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode()).hexdigest()


def get_cache_key(messages: list, model: str) -> str:
    msg_hash = hash_messages(messages)
    raw = f"{msg_hash}:{model}"
    return hashlib.sha256(raw.encode()).hexdigest()


def check_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "SELECT * FROM prompt_cache WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > ?)",
        (cache_key, now)
    )
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def check_semantic_cache(messages: list, model: str) -> Optional[Dict[str, Any]]:
    """Check for semantically similar prompts (embedding cosine similarity)."""
    embedder = get_embedder()
    if embedder is None:
        return None
    text = messages_to_text(messages)
    emb = compute_embedding(text)
    if emb is None:
        return None

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "SELECT * FROM prompt_cache WHERE model = ? AND embedding IS NOT NULL AND (expires_at IS NULL OR expires_at > ?)",
        (model, now)
    )
    best_score = 0.0
    best_row = None
    for row in c.fetchall():
        stored_emb = row["embedding"]
        try:
            vec = np.frombuffer(stored_emb, dtype=np.float32)
            score = float(np.dot(emb, vec))
            if score > best_score:
                best_score = score
                best_row = dict(row)
        except Exception:
            continue
    conn.close()

    threshold = config.semantic_threshold
    if best_row and best_score >= threshold:
        logger.info("SEMANTIC HIT: score=%.4f threshold=%.2f model=%s", best_score, threshold, model)
        return best_row
    logger.debug("Semantic miss: best=%.4f threshold=%.2f", best_score, threshold)
    return None


def set_cache(cache_key: str, messages_hash: str, model: str, response: str,
              prompt_tokens: int, completion_tokens: int, ttl_hours: int = None,
              embedding: Optional[np.ndarray] = None):
    if ttl_hours is None:
        ttl_hours = config.cache_ttl_hours
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(hours=ttl_hours)).isoformat() if ttl_hours > 0 else None
    emb_bytes = embedding.tobytes() if embedding is not None else None
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO prompt_cache 
           (cache_key, model, messages_hash, response, prompt_tokens, completion_tokens, embedding, created_at, expires_at, hit_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 
               COALESCE((SELECT hit_count + 1 FROM prompt_cache WHERE cache_key = ?), 1))""",
        (cache_key, model, messages_hash, response, prompt_tokens, completion_tokens,
         emb_bytes, now.isoformat(), expires, cache_key)
    )
    conn.commit()
    conn.close()


def record_cache_hit(cache_key: str):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("UPDATE prompt_cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (cache_key,))
    conn.commit()
    conn.close()


def get_cache_stats() -> Dict[str, Any]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total, COALESCE(SUM(hit_count), 0) as total_hits FROM prompt_cache")
    counts = dict(c.fetchone())
    c.execute("SELECT COALESCE(SUM((hit_count - 1) * (prompt_tokens + completion_tokens)), 0) as tokens_saved FROM prompt_cache WHERE hit_count > 1")
    tokens = dict(c.fetchone())
    c.execute("SELECT COUNT(*) as entries FROM prompt_cache WHERE hit_count > 1")
    cached = dict(c.fetchone())
    c.execute("SELECT COUNT(*) as semantic FROM prompt_cache WHERE embedding IS NOT NULL")
    sem = dict(c.fetchone())
    c.execute("SELECT metric_key, metric_value FROM proxy_metrics")
    metrics = {row["metric_key"]: row["metric_value"] for row in c.fetchall()}
    conn.close()
    tokens_saved = tokens.get("tokens_saved", 0)
    return {
        "total_entries": counts.get("total", 0),
        "total_cache_hits": counts.get("total_hits", 0),
        "entries_with_hits": cached.get("entries", 0),
        "semantic_entries": sem.get("semantic", 0),
        "tokens_saved": tokens_saved,
        "estimated_cost_saved": tokens_saved * 0.000003,
        "request_count": int(metrics.get("requests_total", 0)),
        "cache_hit_events": int(metrics.get("cache_hits_total", 0)),
        "cache_miss_events": int(metrics.get("cache_misses_total", 0)),
        "runtime_tokens_saved": int(metrics.get("tokens_saved_total", 0)),
        "runtime_cost_saved": float(metrics.get("cost_saved_total", 0.0)),
    }


def increment_proxy_metric(metric_key: str, amount: float = 1) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO proxy_metrics (metric_key, metric_value)
        VALUES (?, ?)
        ON CONFLICT(metric_key) DO UPDATE SET metric_value = metric_value + excluded.metric_value
        """,
        (metric_key, amount),
    )
    conn.commit()
    conn.close()


def record_proxy_request(cache_hit: bool, tokens_saved: int = 0, cost_saved: float = 0.0) -> None:
    increment_proxy_metric("requests_total", 1)
    increment_proxy_metric("cache_hits_total" if cache_hit else "cache_misses_total", 1)
    if tokens_saved > 0:
        increment_proxy_metric("tokens_saved_total", tokens_saved)
    if cost_saved > 0:
        increment_proxy_metric("cost_saved_total", cost_saved)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    costs = MODEL_COSTS.get(model, get_default_cost())
    prompt_cost = (prompt_tokens / 1000) * costs["prompt"]
    completion_cost = (completion_tokens / 1000) * costs["completion"]
    return round(prompt_cost + completion_cost, 6)


# ─── Rate Limiting ──────────────────────────────────────────────────────

def check_rate_limit(identifier: str) -> Tuple[bool, int]:
    """Check if an identifier (user/api_key) has exceeded rate limit.
    Returns (allowed: bool, retry_after_seconds: int)."""
    limit = config.rate_limit_requests
    if limit <= 0:
        return True, 0
    window = config.rate_limit_window_seconds
    now = time.time()
    cutoff = now - window

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("DELETE FROM rate_limits WHERE timestamp < ?", (cutoff,))

    c.execute("SELECT COUNT(*) as cnt FROM rate_limits WHERE identifier = ? AND timestamp > ?",
              (identifier, cutoff))
    row = c.fetchone()
    count = row[0] if row else 0

    if count >= limit:
        oldest_allowed = cutoff
        c.execute("SELECT timestamp FROM rate_limits WHERE identifier = ? ORDER BY timestamp ASC LIMIT 1",
                  (identifier,))
        oldest = c.fetchone()
        retry_after = int(window - (now - oldest[0])) if oldest else window
        conn.close()
        return False, max(retry_after, 1)

    c.execute("INSERT INTO rate_limits (identifier, timestamp) VALUES (?, ?)", (identifier, now))
    conn.commit()
    conn.close()
    return True, 0
