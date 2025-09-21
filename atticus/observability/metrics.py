"""Observability utilities for Atticus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ..logging_utils import log_event


@dataclass(slots=True)
class MetricsRecorder:
    """Tracks high-level usage metrics for Atticus."""

    queries: int = 0
    total_confidence: float = 0.0
    escalations: int = 0
    total_latency_ms: float = 0.0

    def record(self, confidence: float, latency_ms: float, escalated: bool) -> None:
        self.queries += 1
        self.total_confidence += confidence
        self.total_latency_ms += latency_ms
        if escalated:
            self.escalations += 1

    def snapshot(self) -> Dict[str, float]:
        if self.queries == 0:
            return {
                "queries_per_day": 0,
                "avg_confidence": 0.0,
                "escalations_per_day": 0,
                "avg_latency_ms": 0.0,
            }
        return {
            "queries_per_day": self.queries,
            "avg_confidence": round(self.total_confidence / self.queries, 2),
            "escalations_per_day": self.escalations,
            "avg_latency_ms": round(self.total_latency_ms / self.queries, 2),
        }

    def emit(self, logger) -> None:
        payload = self.snapshot()
        log_event(logger, "observability_metrics", **payload)
        self.reset()

    def reset(self) -> None:
        self.queries = 0
        self.total_confidence = 0.0
        self.escalations = 0
        self.total_latency_ms = 0.0
