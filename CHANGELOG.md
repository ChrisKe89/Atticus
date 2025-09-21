# Changelog

## [0.1.0] - 2025-09-20
### Added
- Seeded content taxonomy (`content/model`, `content/software`, `content/service`) with AC7070 collateral.
- Implemented ingestion pipeline with deterministic embeddings, JSON logging, and index snapshotting.
- Added retrieval helpers, observability metrics recorder, and ingestion CLI (`scripts/run_ingestion.py`).
- Delivered pytest evaluation harness with gold set, baseline metrics, and daily run exports.

### Evaluation
- nDCG@10: **1.00** (Δ +0.00)
- Recall@50: **1.00** (Δ +0.00)
- MRR: **1.00** (Δ +0.00)
- Artifacts: `evaluation/runs/20250920/235132/`

### Models
- Embeddings: `text-embedding-3-large`
- LLM: `gpt-4.1`
