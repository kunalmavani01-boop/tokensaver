import os
from dataclasses import dataclass

@dataclass
class ProxyConfig:
    port: int = int(os.environ.get("TOKENSAVER_PROXY_PORT", "8788"))
    upstream_url: str = os.environ.get("TOKENSAVER_PROXY_UPSTREAM", "https://api.openai.com")
    db_path: str = os.environ.get("TOKENSAVER_PROXY_DB", "")
    manager_db_path: str = os.environ.get("TOKENSAVER_DB_PATH", "")
    cache_ttl_hours: int = int(os.environ.get("TOKENSAVER_CACHE_TTL", "24"))
    semantic_threshold: float = float(os.environ.get("TOKENSAVER_SEMANTIC_THRESHOLD", "0.92"))
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")

    rate_limit_requests: int = int(os.environ.get("TOKENSAVER_RATE_LIMIT_REQUESTS", "0"))
    rate_limit_window_seconds: int = int(os.environ.get("TOKENSAVER_RATE_LIMIT_WINDOW", "60"))

    def __post_init__(self):
        if not self.db_path:
            self.db_path = os.path.join(os.path.dirname(__file__), "..", "data", "cache.db")

config = ProxyConfig()
