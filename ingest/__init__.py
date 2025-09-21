"""Ingestion pipeline entrypoints."""

from .pipeline import ingest_corpus, IngestionOptions, IngestionSummary

__all__ = ["ingest_corpus", "IngestionOptions", "IngestionSummary"]
