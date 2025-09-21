"""Simple metrics aggregator for Atticus."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict

from .config import AppSettings


@dataclass(slots=True)
class MetricsRecorder:
    settings: AppSettings
    queries: int = 0
    total_confidence: float = 0.0
    escalations: int = 0
    total_latency_ms: float = 0.0
    store_path: Path = field(default_factory=lambda: Path("logs/metrics.csv"))

    def record(self, confidence: float, latency_ms: float, escalated: bool) -> None:
        self.queries += 1
        self.total_confidence += confidence
        self.total_latency_ms += latency_ms
        if escalated:
            self.escalations += 1

    def snapshot(self) -> Dict[str, float]:
        if self.queries == 0:
            return {
                "queries": 0,
                "avg_confidence": 0.0,
                "escalations": 0,
                "avg_latency_ms": 0.0,
            }
        return {
            "queries": self.queries,
            "avg_confidence": round(self.total_confidence / self.queries, 2),
            "escalations": self.escalations,
            "avg_latency_ms": round(self.total_latency_ms / self.queries, 2),
        }

    def flush(self) -> None:
        if self.queries == 0:
            return
        snapshot = self.snapshot()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.store_path.exists()
        with self.store_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["timestamp", "queries", "avg_confidence", "escalations", "avg_latency_ms"])
            if write_header:
                writer.writeheader()
            writer.writerow({"timestamp": datetime.now(tz=self.settings.tzinfo).isoformat(timespec="seconds"), **snapshot})
        self.reset()

    def reset(self) -> None:
        self.queries = 0
        self.total_confidence = 0.0
        self.escalations = 0
        self.total_latency_ms = 0.0

