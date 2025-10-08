-- Ensure app.pgvector_lists is set for fresh environments.
-- Idempotent: only sets a default if not already configured.
DO $$
BEGIN
  -- current_setting(..., true) returns NULL if not set
  IF current_setting('app.pgvector_lists', true) IS NULL THEN
    PERFORM set_config('app.pgvector_lists', '100', true);
    RAISE NOTICE 'Set app.pgvector_lists to 100';
  ELSE
    RAISE NOTICE 'app.pgvector_lists already set to %', current_setting('app.pgvector_lists', true);
  END IF;
END $$;
