"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from atticus.config import load_manifest

from ..dependencies import SettingsDep
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: SettingsDep) -> HealthResponse:
    manifest = load_manifest(settings.manifest_path)
    return HealthResponse(
        status="ok",
        manifest_present=manifest is not None,
        document_count=manifest.document_count if manifest else 0,
        chunk_count=manifest.chunk_count if manifest else 0,
        embedding_model=(manifest.embedding_model if manifest else settings.embed_model),
    )
