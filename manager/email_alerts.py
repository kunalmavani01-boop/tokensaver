"""Email alert dispatch via SMTP."""
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

from .config import config

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    return bool(config.smtp_host and config.smtp_user)


def send_budget_alert(crossing: Dict[str, Any], to_email: str) -> bool:
    """Send a budget threshold alert via SMTP."""
    if not is_smtp_configured():
        logger.debug("SMTP not configured — skipping email alert")
        return False

    threshold = crossing["threshold"]
    level = "EXCEEDED" if threshold == 100 else f"AT {threshold}%"
    subject = f"TokenSaver Alert — {crossing['user_name']} has {level} of their budget"

    body = f"""
<html><body style="font-family:sans-serif;background:#f8fafc;padding:24px;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;border:1px solid #e2e8f0;">
<div style="font-size:24px;margin-bottom:16px;">
{'🚨' if threshold == 100 else '⚠️'}
<span style="color:{'#ef4444' if threshold == 100 else '#eab308'};font-weight:700;">Budget {level}</span>
</div>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
<tr><td style="padding:8px 0;color:#64748b;">User</td><td style="font-weight:600;">{crossing['user_name']}</td></tr>
<tr><td style="padding:8px 0;color:#64748b;">Email</td><td>{crossing['email']}</td></tr>
<tr><td style="padding:8px 0;color:#64748b;">Budget</td><td>Rs.{crossing['budget']:.2f}</td></tr>
<tr><td style="padding:8px 0;color:#64748b;">Spent</td><td style="color:{'#ef4444' if threshold == 100 else '#eab308'};font-weight:600;">Rs.{crossing['spent']:.2f}</td></tr>
<tr><td style="padding:8px 0;color:#64748b;">Usage</td><td>{crossing['percent']}%</td></tr>
</table>
<hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">
<div style="font-size:12px;color:#94a3b8;">Sent by <strong>TokenSaver</strong> — LLM Cost Governance</div>
</div></body></html>
"""

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = config.smtp_from
    msg["To"] = to_email

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as server:
            if config.smtp_port == 587:
                server.starttls()
            if config.smtp_user:
                server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)
        logger.info("Email alert sent to %s for %s at %d%%", to_email, crossing["user_name"], threshold)
        return True
    except smtplib.SMTPException as e:
        logger.error("SMTP failed for %s: %s", to_email, e)
    return False
