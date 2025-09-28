-- Prisma migration for pgvector document + chunk storage
-- Phase 1: Data Layer First

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS atticus_documents (
    document_id TEXT PRIMARY KEY,
    source_path TEXT UNIQUE NOT NULL,
    sha256 TEXT NOT NULL,
    source_type TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atticus_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES atticus_documents(document_id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    position INTEGER NOT NULL,
    text TEXT NOT NULL,
    section TEXT,
    page_number INTEGER,
    token_count INTEGER,
    start_token INTEGER,
    end_token INTEGER,
    sha256 TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(3072) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_atticus_chunks_document ON atticus_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_atticus_chunks_source_path ON atticus_chunks(source_path);
CREATE UNIQUE INDEX IF NOT EXISTS idx_atticus_chunks_doc_sha ON atticus_chunks(document_id, sha256);

DO $$
DECLARE
    desired_lists INTEGER;
BEGIN
    BEGIN
        desired_lists := current_setting('app.pgvector_lists', true)::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        desired_lists := 100;
    END;

    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_atticus_chunks_embedding ON atticus_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = %s)',
        desired_lists
    );

    BEGIN
        EXECUTE format(
            'ALTER INDEX idx_atticus_chunks_embedding SET (lists = %s)',
            desired_lists
        );
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
END$$;

ALTER TABLE atticus_documents
    ALTER COLUMN metadata SET DEFAULT '{}'::jsonb,
    ALTER COLUMN chunk_count SET DEFAULT 0,
    ALTER COLUMN ingested_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE atticus_chunks
    ALTER COLUMN metadata SET DEFAULT '{}'::jsonb,
    ALTER COLUMN ingested_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN embedding TYPE vector(3072);

DROP TRIGGER IF EXISTS set_updated_at_atticus_documents ON atticus_documents;
CREATE TRIGGER set_updated_at_atticus_documents
BEFORE UPDATE ON atticus_documents
FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_atticus_chunks ON atticus_chunks;
CREATE TRIGGER set_updated_at_atticus_chunks
BEFORE UPDATE ON atticus_chunks
FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at();
