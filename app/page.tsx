import { PageHeader } from "@/components/page-header";
import { ChatPanel } from "@/components/chat/chat-panel";

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12">
      <PageHeader
        eyebrow="Chat"
        title="Your Atticus workspace"
        description="Respond to tenders, proposals, and in-flight escalations with grounded answers."
      />

      <ChatPanel />
    </div>
  );
}
