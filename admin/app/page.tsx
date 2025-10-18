import { ChatReviewBoard } from "../components/chat-review-board";
import { DocumentIngestionPanel } from "../components/document-ingestion-panel";
import { EvalSeedManager } from "../components/eval-seed-manager";
import { GlossaryViewer } from "../components/glossary-viewer";
import { fetchEvalSeeds, fetchGlossaryEntries, fetchReviewQueue } from "../lib/atticus-client";
import { logPhaseTwoError } from "../lib/logging";
import type { EvalSeed, GlossaryEntry, ReviewChat } from "../lib/types";

export const dynamic = "force-dynamic";

export default async function AdminHome() {
  let chats: ReviewChat[] = [];
  let glossary: GlossaryEntry[] = [];
  let seeds: EvalSeed[] = [];
  try {
    chats = await fetchReviewQueue();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load escalation queue.";
    await logPhaseTwoError(`Admin service failed to load queue: ${message}`);
  }

  try {
    glossary = await fetchGlossaryEntries();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load glossary entries.";
    await logPhaseTwoError(`Admin service failed to load glossary: ${message}`);
  }

  try {
    seeds = await fetchEvalSeeds();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load evaluation seeds.";
    await logPhaseTwoError(`Admin service failed to load eval seeds: ${message}`);
  }

  return (
    <main
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
        padding: "1.5rem",
        background: "#f1f5f9",
        minHeight: "100vh",
      }}
    >
      <header style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
        <h1 style={{ fontSize: "2rem", margin: 0 }}>Atticus Admin Console</h1>
        <p style={{ margin: 0, color: "#475569", maxWidth: "720px" }}>
          Curate escalated chats, trigger ingestion, and keep evaluation seeds aligned with the latest corpus.
        </p>
      </header>
      <DocumentIngestionPanel />
      <ChatReviewBoard initialChats={chats} />
      <GlossaryViewer entries={glossary} />
      <EvalSeedManager initialSeeds={seeds} />
    </main>
  );
}
