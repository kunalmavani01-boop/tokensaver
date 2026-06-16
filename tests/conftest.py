import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def temp_env(tmp_path, monkeypatch):
    db_dir = tmp_path / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "savings.db"
    cache_path = db_dir / "cache.db"

    monkeypatch.setenv("TOKENSAVER_DB_PATH", str(db_path))
    monkeypatch.setenv("TOKENSAVER_PROXY_DB", str(cache_path))
    monkeypatch.setenv("TOKENSAVER_MANAGER_URL", "http://127.0.0.1:3001")
    monkeypatch.setenv("TOKENSAVER_INTERNAL_TOKEN", "test-internal-token")
    monkeypatch.setenv("TOKENSAVER_LICENSE_KEY", "dev-mode")
    monkeypatch.setenv("HEADROOM_REQUIRE_RUST_CORE", "false")
    monkeypatch.setenv("HEADROOM_TELEMETRY", "off")

    module_names = [
        "manager.config",
        "manager.database",
        "manager.license",
        "manager.reports",
        "manager.server",
        "proxy.config",
        "proxy.cache",
        "proxy.server",
    ]
    for name in module_names:
        if name in sys.modules:
            importlib.reload(sys.modules[name])

    return {
        "db_path": db_path,
        "cache_path": cache_path,
    }
