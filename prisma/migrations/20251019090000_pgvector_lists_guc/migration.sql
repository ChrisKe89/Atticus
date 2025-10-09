-- Ensure the app.pgvector_lists GUC is set consistently for ANN queries.
DO $$
DECLARE
  existing text;
BEGIN
  existing := current_setting('app.pgvector_lists', true);
  IF existing IS NULL OR length(trim(existing)) = 0 THEN
    existing := '100';
  END IF;
  PERFORM set_config('app.pgvector_lists', existing, true);
  EXECUTE format('ALTER DATABASE %I SET app.pgvector_lists = %L', current_database(), existing);
END $$;
