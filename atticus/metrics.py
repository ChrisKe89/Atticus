"""Simple metrics aggregator for Atticus."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import AppSettings
from .logging import log_event


@dataclass(slots=True)
class MetricsRecorder:
    settings: AppSettings
    store_path: Path = field(default_factory=lambda: Path("logs/metrics/metrics.csv"))
    queries: int = 0
    total_confidence: float = 0.0
    escalations: int = 0
    total_latency_ms: float = 0.0
    latency_samples: list[float] = field(default_factory=list)
    recent_trace_ids: list[str] = field(default_factory=list)
    trace_id_limit: int = 50
    prompt_tokens_total: int = 0
    answer_tokens_total: int = 0
    window_prompt_tokens: int = 0
    window_answer_tokens: int = 0
    window_queries: int = 0

    def record(
        self,
        confidence: float,
        latency_ms: float,
        escalated: bool,
        *,
        trace_id: str | None = None,
        prompt_tokens: int = 0,
        answer_tokens: int = 0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.queries += 1
        self.total_confidence += confidence
        self.total_latency_ms += latency_ms
        self.latency_samples.append(latency_ms)
        if len(self.latency_samples) > 500:
            self.latency_samples = self.latency_samples[-500:]
        if escalated:
            self.escalations += 1
        if trace_id:
            self.recent_trace_ids.append(trace_id)
            if len(self.recent_trace_ids) > self.trace_id_limit:
                self.recent_trace_ids = self.recent_trace_ids[-self.trace_id_limit :]

        safe_prompt_tokens = max(0, int(prompt_tokens))
        safe_answer_tokens = max(0, int(answer_tokens))
        self.prompt_tokens_total += safe_prompt_tokens
        self.answer_tokens_total += safe_answer_tokens
        self.window_prompt_tokens += safe_prompt_tokens
        self.window_answer_tokens += safe_answer_tokens
        self.window_queries += 1

        if self.window_queries >= 100:
            if logger is not None:
                log_event(
                    logger,
                    "query_window_cost",
                    window_queries=self.window_queries,
                    prompt_tokens=self.window_prompt_tokens,
                    answer_tokens=self.window_answer_tokens,
                    estimated_cost_usd=round(
                        self._estimate_cost(self.window_prompt_tokens, self.window_answer_tokens),
                        6,
                    ),
                )
            self.window_queries = 0
            self.window_prompt_tokens = 0
            self.window_answer_tokens = 0

    def _latency_percentile(self, percentile: float) -> float:
        if not self.latency_samples:
            return 0.0
        ordered = sorted(self.latency_samples)
        index = int(round((percentile / 100.0) * (len(ordered) - 1)))
        return float(ordered[index])

    def latency_histogram(self) -> dict[str, int]:
        buckets = {"0-250": 0, "250-500": 0, "500-1000": 0, "1000+": 0}
        for value in self.latency_samples:
            if value < 250:
                buckets["0-250"] += 1
            elif value < 500:
                buckets["250-500"] += 1
            elif value < 1000:
                buckets["500-1000"] += 1
            else:
                buckets["1000+"] += 1
        return buckets

    def snapshot(self) -> dict[str, float | int]:
        if self.queries == 0:
            return {
                "queries": 0,
                "avg_confidence": 0.0,
                "escalations": 0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "prompt_tokens": 0,
                "answer_tokens": 0,
                "estimated_cost_usd": 0.0,
            }
        return {
            "queries": self.queries,
            "avg_confidence": round(self.total_confidence / self.queries, 3),
            "escalations": self.escalations,
            "avg_latency_ms": round(self.total_latency_ms / self.queries, 2),
            "p95_latency_ms": round(self._latency_percentile(95), 2),
            "prompt_tokens": self.prompt_tokens_total,
            "answer_tokens": self.answer_tokens_total,
            "estimated_cost_usd": round(
                self._estimate_cost(self.prompt_tokens_total, self.answer_tokens_total), 6
            ),
        }

    def dashboard(self) -> dict[str, object]:
        return {
            **self.snapshot(),
            "latency_histogram": self.latency_histogram(),
            "recent_trace_ids": list(self.recent_trace_ids),
        }

    def _estimate_cost(self, prompt_tokens: int, answer_tokens: int) -> float:
        prompt_cost = (prompt_tokens / 1000.0) * self.settings.prompt_token_cost_per_1k
        answer_cost = (answer_tokens / 1000.0) * self.settings.answer_token_cost_per_1k
        return prompt_cost + answer_cost

    def flush(self) -> None:
        if self.queries == 0:
            return
        snapshot = self.snapshot()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.store_path.exists()
        with self.store_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "timestamp",
                    "queries",
                    "avg_confidence",
                    "escalations",
                    "avg_latency_ms",
                    "p95_latency_ms",
                    "prompt_tokens",
                    "answer_tokens",
                    "estimated_cost_usd",
                ],
            )
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "timestamp": datetime.now(tz=self.settings.tzinfo).isoformat(
                        timespec="seconds"
                    ),
                    **snapshot,
                }
            )
        self.reset()

    def reset(self) -> None:
        self.queries = 0
        self.total_confidence = 0.0
        self.escalations = 0
        self.total_latency_ms = 0.0
        self.latency_samples.clear()
        self.recent_trace_ids.clear()
        self.prompt_tokens_total = 0
        self.answer_tokens_total = 0
        self.window_prompt_tokens = 0
        self.window_answer_tokens = 0
        self.window_queries = 0
