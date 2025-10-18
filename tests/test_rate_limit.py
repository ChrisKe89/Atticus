from api.rate_limit import RateLimiter


def test_rate_limiter_allows_and_blocks(monkeypatch) -> None:
    times = iter([100.0, 100.2, 101.5])

    def _monotonic():
        return next(times)

    limiter = RateLimiter(limit=1, window_seconds=1)
    monkeypatch.setattr("api.rate_limit.time.monotonic", _monotonic)

    first_decision = limiter.allow("user")
    assert first_decision.allowed
    assert first_decision.remaining == 0

    second_decision = limiter.allow("user")
    assert not second_decision.allowed
    assert second_decision.retry_after is not None
    assert second_decision.retry_after >= 1
    assert limiter.blocked == 1

    third_decision = limiter.allow("user")
    assert third_decision.allowed
    assert third_decision.remaining == 0

    snapshot = limiter.snapshot()
    assert snapshot["active_keys"] == 1

    # Ensure reset clears counters and buckets.
    limiter.reset()
    assert limiter.blocked == 0
    assert limiter._buckets == {}
