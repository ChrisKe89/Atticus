"""Admin endpoints for dictionary and error logs."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from atticus.logging import log_event

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import DictionaryEntry, DictionaryPayload, ErrorLogEntry
from ..utils import load_dictionary, load_error_logs, save_dictionary

router = APIRouter(prefix="/admin")


@router.get("/dictionary", response_model=DictionaryPayload)
async def read_dictionary(settings: SettingsDep) -> DictionaryPayload:
    try:
        entries = [DictionaryEntry(**item) for item in load_dictionary(settings.dictionary_path)]
    except ValueError as exc:  # pragma: no cover - corrupted file path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return DictionaryPayload(entries=entries)


@router.post("/dictionary", response_model=DictionaryPayload)
async def write_dictionary(
    payload: DictionaryPayload,
    settings: SettingsDep,
    logger: LoggerDep,
) -> DictionaryPayload:
    save_dictionary(settings.dictionary_path, [entry.model_dump() for entry in payload.entries])
    log_event(logger, "dictionary_updated", entries=len(payload.entries))
    return payload


@router.get("/errors", response_model=list[ErrorLogEntry])
async def get_errors(
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

