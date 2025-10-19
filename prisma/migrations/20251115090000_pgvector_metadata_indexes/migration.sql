-- Ensure pgvector probe GUC and metadata indexes exist for filtered retrieval.
DO $$
DECLARE
  existing text;
BEGIN
  existing := current_setting('app.pgvector_probes', true);
  IF existing IS NULL OR length(trim(existing)) = 0 THEN
    existing := '4';
  END IF;
  PERFORM set_config('app.pgvector_probes', existing, true);
  EXECUTE format('ALTER DATABASE %I SET app.pgvector_probes = %L', current_database(), existing);
END $$;

CREATE INDEX IF NOT EXISTS idx_atticus_chunks_metadata_category
  ON atticus_chunks ((metadata ->> 'category'));
CREATE INDEX IF NOT EXISTS idx_atticus_chunks_metadata_product
  ON atticus_chunks ((metadata ->> 'product'));
CREATE INDEX IF NOT EXISTS idx_atticus_chunks_metadata_product_family
  ON atticus_chunks ((metadata ->> 'product_family'));
CREATE INDEX IF NOT EXISTS idx_atticus_chunks_metadata_version
  ON atticus_chunks ((metadata ->> 'version'));
CREATE INDEX IF NOT EXISTS idx_atticus_chunks_metadata_org
  ON atticus_chunks ((metadata ->> 'org_id'));
CREATE INDEX IF NOT EXISTS idx_atticus_chunks_metadata_acl
  ON atticus_chunks ((metadata ->> 'acl'));
