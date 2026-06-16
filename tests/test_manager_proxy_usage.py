import importlib

from fastapi.testclient import TestClient


def test_internal_proxy_usage_endpoint_records_user_usage(temp_env):
    database = importlib.import_module("manager.database")
    models = importlib.import_module("manager.models")
    server = importlib.import_module("manager.server")

    database.init_db()
    user = database.create_user(
        models.UserCreate(name="Alice", email="alice@example.com", monthly_budget=100.0)
    )

    client = TestClient(server.app)
    response = client.post(
        "/manager/api/proxy/usage",
        headers={"x-tokensaver-internal-token": "test-internal-token"},
        json={
            "user_api_key": user.api_key,
            "model": "gpt-4o",
            "provider": "openai",
            "endpoint": "/v1/chat/completions",
            "tokens_before": 1400,
            "tokens_after": 900,
            "tokens_saved": 500,
            "cost_estimated": 0.12,
            "cache_hits": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user.id

    usage = database.get_all_usage(days=30)
    assert len(usage) == 1
    assert usage[0]["user_id"] == user.id
    assert usage[0]["tokens_saved"] == 500
    assert usage[0]["cost_estimated"] == 0.12
