import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    port: int = int(os.environ.get("TOKENSAVER_MANAGER_PORT", "3001"))
    headroom_url: str = os.environ.get("HEADROOM_URL", "http://127.0.0.1:8787")
    db_path: Path = Path(os.environ.get("TOKENSAVER_DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "savings.db")))
    slack_webhook_default: str = os.environ.get("SLACK_WEBHOOK_URL", "")
    poll_interval_seconds: int = int(os.environ.get("TOKENSAVER_POLL_INTERVAL", "60"))
    license_public_key: str = os.environ.get("TOKENSAVER_LICENSE_KEY", "dev-mode")
    standalone_mode: bool = os.environ.get("TOKENSAVER_STANDALONE", "false").lower() == "true"

    smtp_host: str = os.environ.get("TOKENSAVER_SMTP_HOST", "")
    smtp_port: int = int(os.environ.get("TOKENSAVER_SMTP_PORT", "587"))
    smtp_user: str = os.environ.get("TOKENSAVER_SMTP_USER", "")
    smtp_password: str = os.environ.get("TOKENSAVER_SMTP_PASSWORD", "")
    smtp_from: str = os.environ.get("TOKENSAVER_SMTP_FROM", "tokensaver@localhost")

    def __post_init__(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

config = Config()
