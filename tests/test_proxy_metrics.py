import importlib


def test_proxy_metrics_track_requests_hits_and_misses(temp_env):
    proxy_cache = importlib.import_module("proxy.cache")
    proxy_cache.init_cache_db()

    proxy_cache.record_proxy_request(cache_hit=False)
    proxy_cache.record_proxy_request(cache_hit=True, tokens_saved=120, cost_saved=0.42)

    stats = proxy_cache.get_cache_stats()

    assert stats["request_count"] == 2
    assert stats["cache_hit_events"] == 1
    assert stats["cache_miss_events"] == 1
    assert stats["runtime_tokens_saved"] == 120
    assert stats["runtime_cost_saved"] == 0.42
