import hashlib
from datetime import datetime, timezone
from typing import Optional

from .config import config
from .database import get_license, set_license as db_set_license

_SECRET_KEY = config.license_public_key

def generate_key(email: str, max_users: int = 5) -> str:
    """Generate a license key for a customer email."""
    raw = f"{email.lower().strip()}:{max_users}:{_SECRET_KEY}"
    key = hashlib.sha256(raw.encode()).hexdigest()[:32].upper()
    formatted = "-".join([key[i:i+8] for i in range(0, 32, 8)])
    return f"TS-{formatted}"

def validate_key(license_key: str, customer_email: str = "") -> dict:
    """Validate a license key. Returns dict with is_valid and info."""
    if not license_key:
        return {"is_valid": False, "max_users": 5, "reason": "No license key provided"}

    # Dev mode: any TS-DEV-xxxxx format key works
    if license_key.startswith("TS-DEV-"):
        return {"is_valid": True, "max_users": 999, "customer_email": "dev-mode"}

    # Check stored license in DB (for re-validation)
    stored = get_license()
    if stored:
        if stored.get("license_key") == license_key:
            return {
                "is_valid": True,
                "max_users": stored.get("max_users", 5),
                "customer_email": stored.get("customer_email", ""),
                "expires_at": stored.get("expires_at")
            }

    # Verify against the secret key for fresh activations
    if customer_email:
        expected = generate_key(customer_email, 25)  # Default 25, will be overridden on save
        if license_key == expected:
            return {"is_valid": True, "max_users": 25, "customer_email": customer_email}
        # Also try common user counts
        for users in (5, 10, 50, 99, 999):
            if license_key == generate_key(customer_email, users):
                return {"is_valid": True, "max_users": users, "customer_email": customer_email}

    return {"is_valid": False, "max_users": 5, "reason": "Invalid license key"}

def save_license(key: str, email: str, max_users: int = 5):
    """Save a valid license to the database."""
    db_set_license(key, email, max_users)

def get_license_info() -> dict:
    """Get current license status."""
    stored = get_license()
    if stored:
        return validate_key(stored["license_key"])
    return {"is_valid": False, "max_users": 5, "customer_email": "", "reason": "No license installed"}

def check_user_limit(current_users: int) -> bool:
    """Check if we can add another user within license limit."""
    info = get_license_info()
    max_users = info.get("max_users", 5)
    return current_users < max_users
