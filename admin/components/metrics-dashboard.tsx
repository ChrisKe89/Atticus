"use client";

import { useState } from "react";
import type { MetricsDashboard } from "../lib/types";

interface MetricsDashboardPanelProps {
  initialMetrics: MetricsDashboard | null;
}

function formatNumber(value: number, fractionDigits = 2): string {
  return Number.isFinite(value) ? value.toFixed(fractionDigits) : "0.00";
}

export function MetricsDashboardPanel({ initialMetrics }: MetricsDashboardPanelProps) {
  const [metrics, setMetrics] = useState<MetricsDashboard | null>(initialMetrics);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsRefreshing(true);
    setError(null);
    try {
      const response = await fetch("/api/metrics");
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof payload.detail === "string" ? payload.detail : "Unable to load metrics.";
        throw new Error(detail);
      }
      setMetrics(payload as MetricsDashboard);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load metrics.");
    } finally {
      setIsRefreshing(false);
    }
  }

  return (
    <section
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        borderRadius: "1.5rem",
        border: "1px solid rgba(59, 130, 246, 0.25)",
        background: "linear-gradient(135deg, rgba(219, 234, 254, 0.4), rgba(191, 219, 254, 0.2))",
        padding: "1.5rem",
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 600, color: "#1d4ed8" }}>
            Service metrics
          </h2>
          <p style={{ margin: "0.25rem 0 0", color: "#1e3a8a", fontSize: "0.95rem" }}>
            Snapshot of recent chat activity and rate limiting from the retrieval service.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={isRefreshing}
          style={{
            borderRadius: "999px",
            border: "1px solid rgba(37, 99, 235, 0.4)",
            background: "#ffffff",
            color: "#1d4ed8",
            padding: "0.5rem 1.2rem",
            fontWeight: 600,
            cursor: isRefreshing ? "wait" : "pointer",
          }}
        >
          {isRefreshing ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {error ? (
        <div
          role="status"
          style={{
            borderRadius: "1rem",
            padding: "0.85rem 1rem",
            background: "#fee2e2",
            border: "1px solid rgba(248, 113, 113, 0.35)",
            color: "#b91c1c",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      ) : null}

      {metrics ? (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
              gap: "1rem",
            }}
          >
            <MetricCard label="Queries" value={metrics.queries.toLocaleString()} />
            <MetricCard label="Escalations" value={metrics.escalations.toLocaleString()} />
            <MetricCard label="Avg confidence" value={`${formatNumber(metrics.avg_confidence * 100, 1)}%`} />
            <MetricCard label="Avg latency" value={`${formatNumber(metrics.avg_latency_ms, 1)} ms`} />
            <MetricCard label="P95 latency" value={`${formatNumber(metrics.p95_latency_ms, 1)} ms`} />
          </div>

          <div
            style={{
              display: "grid",
              gap: "1rem",
              gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1fr)",
            }}
          >
            <div
              style={{
                borderRadius: "1.25rem",
                background: "#ffffff",
                padding: "1rem",
                border: "1px solid rgba(148, 163, 184, 0.25)",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600, color: "#1e293b" }}>
                Latency histogram
              </h3>
              <ul style={{ margin: "0.75rem 0 0", padding: 0, listStyle: "none", display: "grid", gap: "0.5rem" }}>
                {metrics.histogram.length === 0 ? (
                  <li style={{ color: "#64748b", fontSize: "0.85rem" }}>No latency observations recorded yet.</li>
                ) : (
                  metrics.histogram.map((bucket) => (
                    <li
                      key={bucket.bucket}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        background: "rgba(37, 99, 235, 0.06)",
                        borderRadius: "0.75rem",
                        padding: "0.5rem 0.75rem",
                        color: "#1e3a8a",
                        fontSize: "0.85rem",
                      }}
                    >
                      <span>{bucket.bucket}</span>
                      <span style={{ fontWeight: 600 }}>{bucket.count}</span>
                    </li>
                  ))
                )}
              </ul>
            </div>
            <div
              style={{
                borderRadius: "1.25rem",
                background: "#ffffff",
                padding: "1rem",
                border: "1px solid rgba(148, 163, 184, 0.25)",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600, color: "#1e293b" }}>
                  Rate limit
                </h3>
                {metrics.rate_limit ? (
                  <ul style={{ margin: "0.5rem 0 0", padding: 0, listStyle: "none", fontSize: "0.85rem", color: "#475569" }}>
                    {Object.entries(metrics.rate_limit).map(([key, value]) => (
                      <li key={key} style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>{key}</span>
                        <span style={{ fontWeight: 600 }}>{value}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ margin: "0.5rem 0 0", color: "#64748b", fontSize: "0.85rem" }}>
                    No rate limit snapshots reported.
                  </p>
                )}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600, color: "#1e293b" }}>
                  Recent trace IDs
                </h3>
                {metrics.recent_trace_ids.length ? (
                  <ul style={{ margin: "0.5rem 0 0", padding: 0, listStyle: "none", fontSize: "0.85rem", color: "#475569" }}>
                    {metrics.recent_trace_ids.slice(0, 6).map((trace) => (
                      <li key={trace} style={{ overflowWrap: "anywhere" }}>
                        {trace}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ margin: "0.5rem 0 0", color: "#64748b", fontSize: "0.85rem" }}>
                    No trace IDs reported yet.
                  </p>
                )}
              </div>
            </div>
          </div>
        </>
      ) : (
        <p style={{ margin: 0, color: "#1e3a8a", fontSize: "0.9rem" }}>
          No metrics available yet. Trigger a refresh once the retrieval service records activity.
        </p>
      )}
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        borderRadius: "1.25rem",
        background: "#ffffff",
        padding: "1rem",
        border: "1px solid rgba(148, 163, 184, 0.25)",
        display: "flex",
        flexDirection: "column",
        gap: "0.35rem",
      }}
    >
      <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "#64748b", fontWeight: 600 }}>
        {label}
      </span>
      <span style={{ fontSize: "1.4rem", fontWeight: 700, color: "#1d4ed8" }}>{value}</span>
    </div>
  );
}
