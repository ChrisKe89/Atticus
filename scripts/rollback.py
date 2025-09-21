"""Restore the Atticus index to a previous snapshot."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from atticus import AppSettings
from atticus.config import Manifest, load_manifest, write_manifest
from atticus.logging import configure_logging, log_event
from atticus.utils import sha256_text
from eval.runner import load_gold_set
from retriever.vector_store import VectorStore

SNAPSHOT_INDEX = "index.faiss"
SNAPSHOT_METADATA = "index_metadata.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rollback Atticus vector index")
    parser.add_argument("--snapshot", type=Path, default=None, help="Specific snapshot directory to restore")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke tests after rollback")
    parser.add_argument("--limit", type=int, default=20, help="Number of gold queries for smoke testing")
    return parser.parse_args()


def _latest_snapshot_dir(directory: Path) -> Path:
    candidates = sorted([path for path in directory.iterdir() if path.is_dir()])
    if not candidates:
        raise FileNotFoundError(f"No snapshots found in {directory}")
    return candidates[-1]


def _load_metadata_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    return len(payload)


def _run_smoke_tests(settings: AppSettings, logger, limit: int) -> list[str]:
    store = VectorStore(settings, logger)
    gold_examples = load_gold_set(settings.gold_set_path)[:limit]
    missing: list[str] = []
    for example in gold_examples:
        results = store.search(example.question, top_k=5)
        if not results:
            missing.append(example.question)
    return missing


def main() -> None:
    args = parse_args()
    settings = AppSettings()
    logger = configure_logging(settings)

    snapshot_dir = args.snapshot or _latest_snapshot_dir(settings.snapshots_dir)
    index_path = snapshot_dir / SNAPSHOT_INDEX
    metadata_path = snapshot_dir / SNAPSHOT_METADATA
    if not index_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(f"Snapshot {snapshot_dir} is missing required files")

    shutil.copy2(index_path, settings.faiss_index_path)
    shutil.copy2(metadata_path, settings.metadata_path)

    manifest = load_manifest(settings.manifest_path)
    documents = manifest.documents if manifest else {}
    chunk_count = _load_metadata_count(settings.metadata_path)
    updated_manifest = Manifest(
        embedding_model=settings.embed_model,
        embedding_dimensions=settings.embed_dimensions,
        chunk_size=settings.chunk_size,
        chunk_overlap_ratio=settings.chunk_overlap_ratio,
        corpus_hash=sha256_text(f"rollback:{snapshot_dir.name}"),
        document_count=len(documents),
        chunk_count=chunk_count,
        created_at=settings.timestamp(),
        metadata_path=settings.metadata_path,
        index_path=settings.faiss_index_path,
        snapshot_path=index_path,
        documents=documents,
    )
    write_manifest(settings.manifest_path, updated_manifest)

    log_event(
        logger,
        "rollback_restored",
        snapshot=str(snapshot_dir),
        chunk_count=chunk_count,
        document_count=len(documents),
    )

    if args.skip_smoke:
        print("Rollback complete. Smoke tests skipped.")
        return

    missing = _run_smoke_tests(settings, logger, args.limit)
    if missing:
        print("Rollback completed, but some queries returned no results:")
        for query in missing:
            print(f"  - {query}")
        print("Investigate the restored index before releasing.")
    else:
        print("Rollback validated successfully. All smoke tests returned results.")
    print("Tag the rollback commit and update CHANGELOG.md with details.")


if __name__ == "__main__":
    main()

