"""Alert dispatch system for budget thresholds — Slack + Email."""
import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from .database import get_all_alerts, get_user
from .budget_engine import check_crossed_thresholds
from .email_alerts import send_budget_alert

logger = logging.getLogger(__name__)

async def send_slack_message(webhook_url: str, message: str, color: str = "#eab308") -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            payload = {
                "attachments": [{
                    "color": color,
                    "title": "TokenSaver Alert",
                    "text": message,
                    "footer": "TokenSaver Budget Monitor",
                    "ts": datetime.now().timestamp(),
                }]
            }
            r = await client.post(webhook_url, json=payload)
            if r.status_code in (200, 204):
                return True
            logger.warning("Slack webhook returned HTTP %d", r.status_code)
    except httpx.RequestError as e:
        logger.error("Slack webhook failed: %s", e)
    return False

def format_budget_alert(crossing: Dict[str, Any]) -> str:
    emoji = "\U0001f6a8" if crossing["threshold"] == 100 else "\u26a0\ufe0f"
    level = "EXCEEDED" if crossing["threshold"] == 100 else f"AT {crossing['threshold']}%"
    return (
        f"{emoji} *{crossing['user_name']}* has {level} of their budget\n"
        f"  \u2022 Budget: Rs.{crossing['budget']:.2f}\n"
        f"  \u2022 Spent: Rs.{crossing['spent']:.2f}\n"
        f"  \u2022 Usage: {crossing['percent']}%\n"
        f"  \u2022 Email: {crossing['email']}"
    )

async def check_and_alert() -> List[str]:
    alerts_sent = []
    crossings = check_crossed_thresholds()

    if not crossings:
        return []

    alert_configs = get_all_alerts()

    for crossing in crossings:
        for alert_config in alert_configs:
            user = get_user(crossing["user_id"])
            applies = (
                alert_config.team_id is None and alert_config.user_id is None
                or (user and alert_config.team_id and user.team_id == alert_config.team_id)
                or alert_config.user_id == crossing["user_id"]
            )

            if not applies:
                continue

            threshold = crossing["threshold"]
            if threshold == 50 and not alert_config.threshold_50:
                continue
            if threshold == 80 and not alert_config.threshold_80:
                continue
            if threshold == 100 and not alert_config.threshold_100:
                continue

            message = format_budget_alert(crossing)

            # Slack
            if alert_config.slack_webhook:
                color = "#ef4444" if threshold == 100 else "#eab308"
                success = await send_slack_message(alert_config.slack_webhook, message, color)
                if success:
                    alerts_sent.append(f"Slack alert sent for {crossing['user_name']} at {threshold}%")

            # Email
            if alert_config.email:
                email_ok = send_budget_alert(crossing, alert_config.email)
                if email_ok:
                    alerts_sent.append(f"Email alert sent to {alert_config.email} for {crossing['user_name']} at {threshold}%")

            logger.info("Budget alert: %s at %d%% (spent Rs.%.2f of Rs.%.2f)",
                       crossing['user_name'], threshold, crossing['spent'], crossing['budget'])

    return alerts_sent
