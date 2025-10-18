import { fetchReviewQueue } from "../lib/atticus-client";
import { logPhaseTwoError } from "../lib/logging";
import { ChatReviewBoard } from "../components/chat-review-board";
import type { ReviewChat } from "../lib/types";

export const dynamic = "force-dynamic";

export default async function AdminHome() {
  let chats: ReviewChat[] = [];
  try {
    chats = await fetchReviewQueue();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load escalation queue.";
    await logPhaseTwoError(`Admin service failed to load queue: ${message}`);
  }

  return (
    <main>
      <ChatReviewBoard initialChats={chats} />
    </main>
  );
}
