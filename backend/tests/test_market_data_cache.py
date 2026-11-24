
import threading
from concurrent.futures import ThreadPoolExecutor

import app.services.market_data as market_data


def test_cache_uses_lru_eviction(monkeypatch):
    market_data.clear_market_data_cache()
    monkeypatch.setattr(market_data, "MAX_CACHE_ENTRIES", 2)

    fetch = lambda value: lambda: {"value": value}

    market_data._get_or_fetch_cached("A", 60, fetch(1))
    market_data._get_or_fetch_cached("B", 60, fetch(2))

    # Make A the most recently used entry.
    market_data._get_or_fetch_cached("A", 60, fetch(1))

    # C should evict B, not A.
    market_data._get_or_fetch_cached("C", 60, fetch(3))

    assert "A" in market_data._market_data_cache
    assert "B" not in market_data._market_data_cache
    assert "C" in market_data._market_data_cache

    market_data.clear_market_data_cache()


def test_cache_prevents_duplicate_concurrent_fetches():
    market_data.clear_market_data_cache()

    fetch_started = threading.Event()
    allow_fetch = threading.Event()
    call_count = 0
    count_lock = threading.Lock()

    def fetch():
        nonlocal call_count

        with count_lock:
            call_count += 1

        fetch_started.set()

        assert allow_fetch.wait(timeout=5)

        return {"value": 100}

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(
                market_data._get_or_fetch_cached,
                "concurrent-key",
                60,
                fetch
            )

            assert fetch_started.wait(timeout=5)

            second = executor.submit(
                market_data._get_or_fetch_cached,
                "concurrent-key",
                60,
                fetch
            )

            allow_fetch.set()

            assert first.result(timeout=5) == {"value": 100}
            assert second.result(timeout=5) == {"value": 100}

        assert call_count == 1

    finally:
        allow_fetch.set()
        market_data.clear_market_data_cache()


def test_cache_returns_independent_copies():
    market_data.clear_market_data_cache()

    original = {
        "records": [
            {"close": 100}
        ]
    }

    first = market_data._get_or_fetch_cached(
        "copy-key",
        60,
        lambda: original
    )

    first["records"][0]["close"] = 999

    second = market_data._get_or_fetch_cached(
        "copy-key",
        60,
        lambda: original
    )

    assert second["records"][0]["close"] == 100

    market_data.clear_market_data_cache()

def test_cache_expires_after_ttl(monkeypatch):
    market_data.clear_market_data_cache()

    current_time = [100.0]
    call_count = 0

    monkeypatch.setattr(
        market_data.time,
        "monotonic",
        lambda: current_time[0]
    )

    def fetch():
        nonlocal call_count
        call_count += 1
        return {"value": call_count}

    first = market_data._get_or_fetch_cached(
        "ttl-key",
        10,
        fetch
    )

    assert first == {"value": 1}

    # Cache should still be valid before expiration.
    current_time[0] = 109.0

    second = market_data._get_or_fetch_cached(
        "ttl-key",
        10,
        fetch
    )

    assert second == {"value": 1}
    assert call_count == 1

    # Cache should expire at the TTL boundary.
    current_time[0] = 110.0

    third = market_data._get_or_fetch_cached(
        "ttl-key",
        10,
        fetch
    )

    assert third == {"value": 2}
    assert call_count == 2

    market_data.clear_market_data_cache()

