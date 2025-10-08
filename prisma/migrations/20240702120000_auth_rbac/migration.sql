-- Prisma migration for Auth.js + RBAC + glossary storage
-- Phase 3 rollout. Applies tables, enums, triggers, and RLS policies.

CREATE SCHEMA IF NOT EXISTS app_private;

DO $$
DECLARE
  db_name text := current_database();
BEGIN
  EXECUTE format('ALTER DATABASE %I SET app.current_user_role = %L', db_name, 'SERVICE');
  EXECUTE format('ALTER DATABASE %I SET app.current_org_id = %L', db_name, '');
  EXECUTE format('ALTER DATABASE %I SET app.current_user_id = %L', db_name, '');
  EXECUTE format('ALTER DATABASE %I SET app.pgvector_lists = %L', db_name, '100');
  EXECUTE format('ALTER DATABASE %I SET app.pgvector_dimension = %L', db_name, '3072');
END
$$;

CREATE OR REPLACE FUNCTION app_private.update_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW."updatedAt" = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TYPE "Role" AS ENUM ('USER', 'REVIEWER', 'ADMIN');
CREATE TYPE "GlossaryStatus" AS ENUM ('PENDING', 'APPROVED', 'REJECTED');

CREATE TABLE "Organization" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX "Organization_name_key" ON "Organization" ("name");

CREATE TABLE "User" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT,
  "email" TEXT NOT NULL,
  "emailVerified" TIMESTAMP(3),
  "image" TEXT,
  "role" "Role" NOT NULL DEFAULT 'USER',
  "orgId" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "User_email_key" UNIQUE ("email"),
  CONSTRAINT "User_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization" ("id") ON DELETE CASCADE
);

CREATE TABLE "Account" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "provider" TEXT NOT NULL,
  "providerAccountId" TEXT NOT NULL,
  "refresh_token" TEXT,
  "access_token" TEXT,
  "expires_at" INTEGER,
  "token_type" TEXT,
  "scope" TEXT,
  "id_token" TEXT,
  "session_state" TEXT,
  "oauth_token_secret" TEXT,
  "oauth_token" TEXT,
  CONSTRAINT "Account_provider_providerAccountId_key" UNIQUE ("provider", "providerAccountId"),
  CONSTRAINT "Account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE
);

CREATE TABLE "Session" (
  "id" TEXT PRIMARY KEY,
  "sessionToken" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "expires" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "Session_sessionToken_key" UNIQUE ("sessionToken"),
  CONSTRAINT "Session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE
);

CREATE TABLE "VerificationToken" (
  "identifier" TEXT NOT NULL,
  "token" TEXT NOT NULL,
  "expires" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "VerificationToken_token_key" UNIQUE ("token"),
  CONSTRAINT "VerificationToken_identifier_token_key" UNIQUE ("identifier", "token")
);

CREATE TABLE "GlossaryEntry" (
  "id" TEXT PRIMARY KEY,
  "term" TEXT NOT NULL,
  "definition" TEXT NOT NULL,
  "status" "GlossaryStatus" NOT NULL DEFAULT 'PENDING',
  "orgId" TEXT NOT NULL,
  "authorId" TEXT NOT NULL,
  "updatedById" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "GlossaryEntry_orgId_term_key" UNIQUE ("orgId", "term"),
  CONSTRAINT "GlossaryEntry_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization" ("id") ON DELETE CASCADE,
  CONSTRAINT "GlossaryEntry_authorId_fkey" FOREIGN KEY ("authorId") REFERENCES "User" ("id") ON DELETE RESTRICT,
  CONSTRAINT "GlossaryEntry_updatedById_fkey" FOREIGN KEY ("updatedById") REFERENCES "User" ("id") ON DELETE SET NULL
);

CREATE INDEX "GlossaryEntry_orgId_status_idx" ON "GlossaryEntry" ("orgId", "status");

CREATE TRIGGER set_updated_at_organization
BEFORE UPDATE ON "Organization"
FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at();

CREATE TRIGGER set_updated_at_user
BEFORE UPDATE ON "User"
FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at();

CREATE TRIGGER set_updated_at_glossary
BEFORE UPDATE ON "GlossaryEntry"
FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at();

ALTER TABLE "Organization" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "User" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Account" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Session" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "GlossaryEntry" ENABLE ROW LEVEL SECURITY;

-- Helper comment: we intentionally leave VerificationToken without RLS because it contains short-lived tokens only.

CREATE POLICY "Organization_same_org_read" ON "Organization"
  FOR SELECT USING (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "id" = current_setting('app.current_org_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Organization_admin_update" ON "Organization"
  FOR UPDATE USING (
    current_setting('app.current_org_id', true) IS NOT NULL
    AND "id" = current_setting('app.current_org_id')
    AND current_setting('app.current_user_role', true) = 'ADMIN'
  ) WITH CHECK (
    current_setting('app.current_org_id', true) IS NOT NULL
    AND "id" = current_setting('app.current_org_id')
  );

CREATE POLICY "User_same_org_select" ON "User"
  FOR SELECT USING (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "User_self_update" ON "User"
  FOR UPDATE USING (
    (
      current_setting('app.current_user_id', true) IS NOT NULL
      AND "id" = current_setting('app.current_user_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  ) WITH CHECK (
    (
      current_setting('app.current_user_id', true) IS NOT NULL
      AND "id" = current_setting('app.current_user_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "User_admin_update" ON "User"
  FOR UPDATE USING (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
      AND current_setting('app.current_user_role', true) = 'ADMIN'
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  ) WITH CHECK (
    (
      "orgId" = current_setting('app.current_org_id')
      AND current_setting('app.current_user_role', true) = 'ADMIN'
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "User_admin_insert" ON "User"
  FOR INSERT WITH CHECK (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
      AND current_setting('app.current_user_role', true) = 'ADMIN'
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Account_same_user" ON "Account"
  USING (
    (
      current_setting('app.current_user_id', true) IS NOT NULL
      AND "userId" = current_setting('app.current_user_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  ) WITH CHECK (
    (
      current_setting('app.current_user_id', true) IS NOT NULL
      AND "userId" = current_setting('app.current_user_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Session_same_user" ON "Session"
  USING (
    (
      current_setting('app.current_user_id', true) IS NOT NULL
      AND "userId" = current_setting('app.current_user_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  ) WITH CHECK (
    (
      current_setting('app.current_user_id', true) IS NOT NULL
      AND "userId" = current_setting('app.current_user_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Glossary_same_org_read" ON "GlossaryEntry"
  FOR SELECT USING (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Glossary_admin_write" ON "GlossaryEntry"
  FOR INSERT WITH CHECK (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
      AND current_setting('app.current_user_role', true) = 'ADMIN'
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Glossary_admin_update" ON "GlossaryEntry"
  FOR UPDATE USING (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
      AND current_setting('app.current_user_role', true) = 'ADMIN'
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  ) WITH CHECK (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );

CREATE POLICY "Glossary_admin_delete" ON "GlossaryEntry"
  FOR DELETE USING (
    (
      current_setting('app.current_org_id', true) IS NOT NULL
      AND "orgId" = current_setting('app.current_org_id')
      AND current_setting('app.current_user_role', true) = 'ADMIN'
    )
    OR current_setting('app.current_user_role', true) = 'SERVICE'
  );
