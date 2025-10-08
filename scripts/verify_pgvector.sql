-- Accept overrides via `psql -v expected_pgvector_dimension=1536 -v expected_pgvector_lists=50 ...`
\set ON_ERROR_STOP on

\if :{?expected_pgvector_dimension}
\else
  \set expected_pgvector_dimension 3072
\endif

\if :{?expected_pgvector_lists}
\else
  \set expected_pgvector_lists 100
\endif

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
    RAISE EXCEPTION 'pgvector extension not installed';
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'atticus_documents') THEN
    RAISE EXCEPTION 'atticus_documents table missing';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'atticus_chunks') THEN
    RAISE EXCEPTION 'atticus_chunks table missing';
  END IF;
END$$;

-- Validate embedding dimension matches expected setting (defaults to 3072).
DO $$
DECLARE
  dimension integer;
  expected integer := :expected_pgvector_dimension;
BEGIN
  SELECT atttypmod INTO dimension
  FROM pg_attribute
  WHERE attrelid = 'atticus_chunks'::regclass
    AND attname = 'embedding'
    AND NOT attisdropped;

  IF dimension IS NULL THEN
    RAISE EXCEPTION 'atticus_chunks.embedding column missing';
  END IF;

  IF dimension <> expected THEN
    RAISE EXCEPTION 'atticus_chunks.embedding dimension is %, expected %', dimension, expected;
  END IF;
END$$;

-- Confirm IVFFlat index exists for cosine search.
DO $$
DECLARE
  idx_record TEXT;
  expected_lists INTEGER := :expected_pgvector_lists;
  dimension INTEGER;
BEGIN
  SELECT atttypmod INTO dimension
  FROM pg_attribute
  WHERE attrelid = 'atticus_chunks'::regclass
    AND attname = 'embedding'
    AND NOT attisdropped;

  IF dimension IS NULL THEN
    RAISE EXCEPTION 'atticus_chunks.embedding column missing';
  END IF;

  IF dimension > 2000 THEN
    RAISE NOTICE 'Skipping IVFFlat verification because dimension % exceeds 2000. Install a pgvector build with higher INDEX_MAX_DIMENSIONS to enable ANN indexing.', dimension;
    RETURN;
  END IF;

  SELECT indexdef INTO idx_record
  FROM pg_indexes
  WHERE tablename = 'atticus_chunks'
    AND indexname = 'idx_atticus_chunks_embedding';

  IF idx_record IS NULL THEN
    RAISE EXCEPTION 'IVFFlat index missing on atticus_chunks';
  END IF;

  IF position(lower(format('lists = %s', expected_lists)) IN lower(idx_record)) = 0 THEN
    RAISE EXCEPTION 'idx_atticus_chunks_embedding lists mismatch. Expected lists=% with index definition: %', expected_lists, idx_record;
  END IF;
END$$;

-- Confirm metadata defaults are applied so ingestion can omit the column explicitly.
DO $$
DECLARE
  doc_default TEXT;
  chunk_default TEXT;
BEGIN
  SELECT column_default INTO doc_default
  FROM information_schema.columns
  WHERE table_name = 'atticus_documents' AND column_name = 'metadata';

  IF doc_default IS DISTINCT FROM '\''{}\''::jsonb' THEN
    RAISE NOTICE 'atticus_documents.metadata default is %, expected {}::jsonb', doc_default;
  END IF;

  SELECT column_default INTO chunk_default
  FROM information_schema.columns
  WHERE table_name = 'atticus_chunks' AND column_name = 'metadata';

  IF chunk_default IS DISTINCT FROM '\''{}\''::jsonb' THEN
    RAISE NOTICE 'atticus_chunks.metadata default is %, expected {}::jsonb', chunk_default;
  END IF;
END$$;

SELECT 'pgvector verification completed successfully.' AS status;
