"""Data ingestion for standalone mode: manual entry, CSV import, API bulk ingest."""
import csv
import io
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .database import insert_usage, get_all_users, get_all_teams

logger = logging.getLogger(__name__)

MODEL_OPTIONS = [
    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
    "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
    "claude-3.5-sonnet", "claude-3.5-haiku",
    "gemini-1.5-pro", "gemini-1.5-flash",
    "llama-3-70b", "llama-3-8b", "mistral-large", "custom",
]

PROVIDER_OPTIONS = ["openai", "anthropic", "google", "meta", "mistral", "other"]


def validate_manual_entry(data: Dict[str, Any]) -> List[str]:
    """Validate manual entry form data. Returns list of error messages (empty = valid)."""
    errors = []
    user_id = data.get("user_id")
    if not user_id:
        errors.append("User is required")
    else:
        try:
            uid = int(user_id)
            users = get_all_users()
            if not any(u.id == uid for u in users):
                errors.append("Selected user not found")
        except (ValueError, TypeError):
            errors.append("Invalid user ID")

    cost = data.get("cost_estimated", 0)
    try:
        if float(cost) < 0:
            errors.append("Cost cannot be negative")
    except (ValueError, TypeError):
        errors.append("Cost must be a number")

    tokens = data.get("tokens_saved", 0)
    try:
        if int(tokens) < 0:
            errors.append("Tokens saved cannot be negative")
    except (ValueError, TypeError):
        errors.append("Tokens saved must be a number")

    return errors


def record_from_form(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert form data into a usage record dict."""
    now = datetime.now(timezone.utc).isoformat()
    cost = float(data.get("cost_estimated", 0))
    tokens = int(data.get("tokens_saved", 0))
    tokens_before = int(data.get("tokens_before", 0))
    tokens_after = max(0, tokens_before - tokens)
    model = data.get("model", "custom")
    provider = data.get("provider", "other")
    user_id = int(data["user_id"]) if data.get("user_id") else None

    # Resolve team_id from user
    team_id = None
    if user_id:
        users = get_all_users()
        for u in users:
            if u.id == user_id:
                team_id = u.team_id
                break

    return {
        "timestamp": now,
        "user_id": user_id,
        "team_id": team_id,
        "model": model,
        "provider": provider,
        "endpoint": "/v1/chat/completions",
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "tokens_saved": tokens,
        "cost_estimated": cost,
        "cache_hits": 0,
    }


def parse_usage_csv(content: str) -> List[Dict[str, Any]]:
    """Parse uploaded CSV content into usage records.
    Expected columns: user_id, model, cost_estimated, tokens_saved, [timestamp, provider, tokens_before]
    """
    records = []
    reader = csv.DictReader(io.StringIO(content))
    users = {u.id: u for u in get_all_users()}

    for row in reader:
        user_id = row.get("user_id", "").strip()
        if not user_id or not user_id.isdigit():
            logger.warning("Skipping row with invalid user_id: %s", user_id)
            continue
        uid = int(user_id)
        if uid not in users:
            logger.warning("Skipping row — user %d not found", uid)
            continue

        user = users[uid]
        try:
            cost = float(row.get("cost_estimated", 0) or 0)
            tokens_saved = int(row.get("tokens_saved", 0) or 0)
            tokens_before = int(row.get("tokens_before", 0) or 0)
        except (ValueError, TypeError):
            logger.warning("Skipping row — invalid numeric value")
            continue

        records.append({
            "timestamp": row.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "user_id": uid,
            "team_id": user.team_id,
            "model": row.get("model", "custom"),
            "provider": row.get("provider", "other"),
            "endpoint": "/v1/chat/completions",
            "tokens_before": tokens_before,
            "tokens_after": max(0, tokens_before - tokens_saved),
            "tokens_saved": tokens_saved,
            "cost_estimated": cost,
            "cache_hits": 0,
        })

    return records


def generate_csv_template() -> str:
    """Generate a CSV template with example row."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "model", "provider", "cost_estimated", "tokens_saved", "tokens_before", "timestamp"])
    writer.writerow(["1", "gpt-4o", "openai", "0.05", "500", "1500", "2026-06-01T12:00:00"])
    writer.writerow(["2", "claude-3.5-sonnet", "anthropic", "0.12", "1200", "3000", "2026-06-01T14:30:00"])
    return output.getvalue()


def bulk_insert_records(records: List[Dict[str, Any]]) -> int:
    """Insert multiple usage records. Returns count of inserted records."""
    count = 0
    for record in records:
        try:
            insert_usage(record)
            count += 1
        except Exception as e:
            logger.error("Failed to insert record: %s", e)
    logger.info("Bulk inserted %d/%d usage records", count, len(records))
    return count
