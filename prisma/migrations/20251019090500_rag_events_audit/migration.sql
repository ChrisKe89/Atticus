-- Capture glossary/chat audit events for administrator actions.
CREATE TABLE "RagEvent" (
    "id" TEXT NOT NULL,
    "orgId" TEXT NOT NULL,
    "actorId" TEXT,
    "actorRole" "Role",
    "action" TEXT NOT NULL,
    "entity" TEXT NOT NULL,
    "glossaryId" TEXT,
    "chatId" TEXT,
    "requestId" TEXT,
    "before" JSONB,
    "after" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "RagEvent_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "RagEvent_orgId_action_createdAt_idx" ON "RagEvent"("orgId", "action", "createdAt");
CREATE INDEX "RagEvent_glossaryId_idx" ON "RagEvent"("glossaryId");
CREATE INDEX "RagEvent_chatId_idx" ON "RagEvent"("chatId");

ALTER TABLE "RagEvent"
  ADD CONSTRAINT "RagEvent_orgId_fkey"
  FOREIGN KEY ("orgId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "RagEvent"
  ADD CONSTRAINT "RagEvent_actorId_fkey"
  FOREIGN KEY ("actorId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "RagEvent"
  ADD CONSTRAINT "RagEvent_glossaryId_fkey"
  FOREIGN KEY ("glossaryId") REFERENCES "GlossaryEntry"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "RagEvent"
  ADD CONSTRAINT "RagEvent_chatId_fkey"
  FOREIGN KEY ("chatId") REFERENCES "Chat"("id") ON DELETE SET NULL ON UPDATE CASCADE;
