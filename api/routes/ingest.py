from __future__ import annotations

from fastapi import APIRouter

from atticus.logging import log_event
from ingest import IngestionOptions, ingest_corpus

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import IngestRequest, IngestResponse

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingestion(
    payload: IngestRequest,
    settings: SettingsDep,
    logger: LoggerDep,
) -> IngestResponse:
    options = IngestionOptions(full_refresh=payload.full_refresh, paths=payload.paths)
    summary = ingest_corpus(settings=settings, options=options)
    log_event(
        logger,
        "ingest_api_complete",
        documents_processed=summary.documents_processed,
        documents_skipped=summary.documents_skipped,
        chunks_indexed=summary.chunks_indexed,
    )
    return IngestResponse(
        documents_processed=summary.documents_processed,
        documents_skipped=summary.documents_skipped,
        chunks_indexed=summary.chunks_indexed,
        elapsed_seconds=summary.elapsed_seconds,
        manifest_path=str(summary.manifest_path),
        index_path=str(summary.index_path),
        snapshot_path=str(summary.snapshot_path),
        ingested_at=summary.ingested_at,
        embedding_model=summary.embedding_model,
        embedding_model_version=summary.embedding_model_version,
    )
