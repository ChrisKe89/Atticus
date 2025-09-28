"""Admin endpoints for dictionary and error logs."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from atticus.logging import log_event

from ..dependencies import AdminGuard, LoggerDep, MetricsDep, SettingsDep
from ..schemas import (
    DictionaryEntry,
    DictionaryPayload,
    ErrorLogEntry,
    MetricsDashboard,
    MetricsHistogram,
    SessionLogEntry,
    SessionLogResponse,
)
from ..utils import load_dictionary, load_error_logs, load_session_logs, save_dictionary

router = APIRouter(prefix="/admin")


@router.get("/dictionary", response_model=DictionaryPayload)
async def read_dictionary(_: AdminGuard, settings: SettingsDep) -> DictionaryPayload:
    try:
        entries = [DictionaryEntry(**item) for item in load_dictionary(settings.dictionary_path)]
    except ValueError as exc:  # pragma: no cover - corrupted file path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return DictionaryPayload(entries=entries)


@router.post("/dictionary", response_model=DictionaryPayload)
async def write_dictionary(
    _: AdminGuard,
    payload: DictionaryPayload,
    settings: SettingsDep,
    logger: LoggerDep,
) -> DictionaryPayload:
    save_dictionary(settings.dictionary_path, [entry.model_dump() for entry in payload.entries])
    log_event(logger, "dictionary_updated", entries=len(payload.entries))
    return payload


@router.get("/errors", response_model=list[ErrorLogEntry])
async def get_errors(
    _: AdminGuard,
    settings: SettingsDep,
    since: str | None = Query(default=None, description="Return errors since ISO timestamp"),
) -> list[ErrorLogEntry]:
    entries = load_error_logs(settings.errors_path, limit=100)
    filtered: list[ErrorLogEntry] = []
    cutoff = None
    if since:
        try:
            cutoff = datetime.fromisoformat(since)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid ISO timestamp") from exc
    for entry in entries:
        timestamp = entry.get("time") or entry.get("timestamp")
        if cutoff and timestamp:
            try:
                entry_time = datetime.fromisoformat(str(timestamp))
            except ValueError:
                continue
            if entry_time < cutoff:
                continue
        filtered.append(
            ErrorLogEntry(
                time=str(timestamp),
                message=str(entry.get("message", "")),
                details={k: str(v) for k, v in entry.items() if k not in {"time", "message"}},
            )
        )
    return filtered


def _render_session_html(entries: list[dict[str, object]]) -> str:
    rows = []
    for entry in entries:
        filters = entry.get("filters")
        filters_str = json.dumps(filters, indent=2) if isinstance(filters, dict) else str(filters)
        rows.append(
            "<tr>"
            f"<td>{entry.get('time', '')}</td>"
            f"<td>{entry.get('request_id', '')}</td>"
            f"<td>{entry.get('method', '')}</td>"
            f"<td>{entry.get('path', '')}</td>"
            f"<td>{entry.get('status', '')}</td>"
            f"<td>{entry.get('latency_ms', '')}</td>"
            f"<td>{entry.get('confidence', '')}</td>"
            f"<td>{entry.get('escalate', '')}</td>"
            f"<td><pre>{filters_str}</pre></td>"
            "</tr>"
        )
    table_rows = "\n".join(rows)
    return (
        "<html><head><title>Session Logs</title>"
        "<style>table{border-collapse:collapse;width:100%;}"
        "th,td{border:1px solid #ccc;padding:8px;text-align:left;}"
        "pre{margin:0;white-space:pre-wrap;}</style></head><body>"
        "<h1>Recent Sessions</h1>"
        "<table>"
        "<thead><tr><th>Time</th><th>Request ID</th><th>Method</th><th>Path</th><th>Status</th>"
        "<th>Latency (ms)</th><th>Confidence</th><th>Escalate</th><th>Filters</th></tr></thead>"
        f"<tbody>{table_rows}</tbody></table></body></html>"
    )


@router.get(
    "/sessions", response_model=SessionLogResponse, responses={200: {"content": {"text/html": {}}}}
)
async def get_sessions(
    _: AdminGuard,
    settings: SettingsDep,
    format: str = Query("json", pattern="^(json|html)$", description="Return JSON or HTML"),
    limit: int = Query(20, ge=1, le=200),
) -> SessionLogResponse | HTMLResponse:
    entries = load_session_logs(settings.logs_path, limit=limit)
    if format.lower() == "html":
        html = _render_session_html(entries)
        return HTMLResponse(html)
    payload = [SessionLogEntry(**entry) for entry in entries]
    return SessionLogResponse(sessions=payload)


@router.get("/metrics", response_model=MetricsDashboard)
async def get_metrics_dashboard(
    _: AdminGuard,
    metrics: MetricsDep,
    request: Request,
) -> MetricsDashboard:
    data = metrics.dashboard()
    histogram = [
        MetricsHistogram(bucket=bucket, count=int(count))
        for bucket, count in data.get("latency_histogram", {}).items()
    ]
    limiter = getattr(request.app.state, "rate_limiter", None)
    rate_limit = limiter.snapshot() if limiter else None
    return MetricsDashboard(
        queries=int(data.get("queries", 0)),
        avg_confidence=float(data.get("avg_confidence", 0.0)),
        escalations=int(data.get("escalations", 0)),
        avg_latency_ms=float(data.get("avg_latency_ms", 0.0)),
        p95_latency_ms=float(data.get("p95_latency_ms", 0.0)),
        histogram=histogram,
        recent_trace_ids=list(data.get("recent_trace_ids", [])),
        rate_limit=rate_limit,
    )
