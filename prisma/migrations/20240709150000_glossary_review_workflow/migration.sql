-- Extend glossary entries with review metadata and synonym support.

ALTER TABLE "GlossaryEntry"
  ADD COLUMN "synonyms" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN "reviewNotes" TEXT,
  ADD COLUMN "reviewedAt" TIMESTAMP(3),
  ADD COLUMN "reviewerId" TEXT;

ALTER TABLE "GlossaryEntry"
  ADD CONSTRAINT "GlossaryEntry_reviewerId_fkey"
  FOREIGN KEY ("reviewerId") REFERENCES "User"("id") ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS "GlossaryEntry_status_reviewedAt_idx"
  ON "GlossaryEntry" ("status", "reviewedAt");
