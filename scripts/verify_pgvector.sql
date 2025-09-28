-- Verifies pgvector extension, atticus chunk schema, and IVFFlat index health.
\set ON_ERROR_STOP on

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
    RAISE EXCEPTION 'pgvector extension not installed';
  END IF;
END$$;

-- Ensure atticus_chunks table exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'atticus_chunks') THEN
    RAISE EXCEPTION 'atticus_chunks table missing';
  END IF;
END$$;

-- Validate embedding dimension matches expected setting (defaults to 3072).
DO $$
DECLARE
  dimension integer;
BEGIN
  SELECT atttypmod - 4 INTO dimension
  FROM pg_attribute
  WHERE attrelid = 'atticus_chunks'::regclass
    AND attname = 'embedding'
    AND NOT attisdropped;

  IF dimension IS NULL THEN
    RAISE EXCEPTION 'atticus_chunks.embedding column missing';
  END IF;

  IF dimension <> 3072 THEN
    RAISE NOTICE 'atticus_chunks.embedding dimension is %, expected 3072', dimension;
  END IF;
END$$;

-- Confirm IVFFlat index exists for cosine search.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE tablename = 'atticus_chunks'
      AND indexdef ILIKE '%ivfflat%'
  ) THEN
    RAISE EXCEPTION 'IVFFlat index missing on atticus_chunks';
  END IF;
END$$;

SELECT 'pgvector verification completed successfully.' AS status;
