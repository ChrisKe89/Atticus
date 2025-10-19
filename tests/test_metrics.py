from pathlib import Path

from atticus.metrics import MetricsRecorder
from core.config import AppSettings


class _StubLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict | None]] = []

    def info(self, message: str, *, extra: dict | None = None) -> None:  # type: ignore[override]
        self.events.append((message, extra))


def test_metrics_recorder_tracks_tokens_and_cost(tmp_path: Path):
    settings = AppSettings()
    recorder = MetricsRecorder(settings=settings, store_path=tmp_path / "metrics.csv")
    logger = _StubLogger()

    for _ in range(100):
        recorder.record(
            confidence=0.85,
            latency_ms=120.0,
            escalated=False,
            prompt_tokens=150,
            answer_tokens=75,
            logger=logger,
        )

    assert recorder.prompt_tokens_total == 150 * 100
    assert recorder.answer_tokens_total == 75 * 100
    assert recorder.window_queries == 0
    assert recorder.window_prompt_tokens == 0
    assert recorder.window_answer_tokens == 0
    assert logger.events, "Expected window cost log event"
    name, payload = logger.events[0]
    assert name == "query_window_cost"
    assert payload is not None and "extra_payload" in payload
    extra = payload["extra_payload"]
    assert extra["prompt_tokens"] == 150 * 100
    assert extra["answer_tokens"] == 75 * 100
    expected_cost = ((150 * 100) / 1000.0) * settings.prompt_token_cost_per_1k
    expected_cost += ((75 * 100) / 1000.0) * settings.answer_token_cost_per_1k
    assert extra["estimated_cost_usd"] == round(expected_cost, 6)
