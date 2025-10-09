-- Phase 6: Admin Ops Console support tables
CREATE TABLE "Chat" (
  "id" TEXT PRIMARY KEY,
  "orgId" TEXT NOT NULL,
  "userId" TEXT,
  "question" TEXT NOT NULL,
  "answer" TEXT,
  "confidence" DOUBLE PRECISION NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'ok',
  "topSources" JSONB,
  "requestId" TEXT,
  "reviewedById" TEXT,
  "reviewedAt" TIMESTAMPTZ,
  "followUpPrompt" TEXT,
  "auditLog" JSONB,
  "createdAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Ticket" (
  "id" TEXT PRIMARY KEY,
  "orgId" TEXT NOT NULL,
  "key" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "assignee" TEXT,
  "lastActivity" TIMESTAMPTZ,
  "summary" TEXT,
  "chatId" TEXT,
  "auditLog" JSONB,
  "createdAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE "Chat"
  ADD CONSTRAINT "Chat_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Chat"
  ADD CONSTRAINT "Chat_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "Chat"
  ADD CONSTRAINT "Chat_reviewedById_fkey" FOREIGN KEY ("reviewedById") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "Ticket"
  ADD CONSTRAINT "Ticket_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Ticket"
  ADD CONSTRAINT "Ticket_chatId_fkey" FOREIGN KEY ("chatId") REFERENCES "Chat"("id") ON DELETE SET NULL ON UPDATE CASCADE;

CREATE UNIQUE INDEX "Ticket_orgId_key_key" ON "Ticket" ("orgId", "key");
CREATE INDEX "Chat_orgId_status_idx" ON "Chat" ("orgId", "status");
CREATE INDEX "Chat_status_reviewedAt_idx" ON "Chat" ("status", "reviewedAt");
CREATE INDEX "Ticket_status_assignee_idx" ON "Ticket" ("status", "assignee");
