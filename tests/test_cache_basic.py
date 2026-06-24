import pytest
from pathlib import Path

import proxy.cache as cache


def test_cache_put_get(tmp_path):
    # Use an isolated temporary DB so tests don't touch any real DB
    dbfile = tmp_path / "test_cache.db"
    cache.DB_PATH = dbfile
    # initialize DB schema
    cache.init_cache_db()

    messages = [{"role": "user", "content": "Hello world"}]
    model = "gpt-3.5-turbo"

    messages_hash = cache.hash_messages(messages)
    cache_key = cache.get_cache_key(messages, model)

    cache.set_cache(cache_key, messages_hash, model, "my-response", 10, 20, ttl_hours=1)

    row = cache.check_cache(cache_key)
    assert row is not None
    assert row["response"] == "my-response"
    assert row["model"] == model
