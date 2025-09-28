import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { ChatPanel } from "@/components/chat/chat-panel";

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12">
      <PageHeader
        eyebrow="Chat"
        title="Your Atticus workspace"
        description="Respond to tenders, proposals, and in-flight escalations with grounded answers."
        actions={
          <Link
            href="/apps"
            className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500"
          >
            Explore integrations
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        }
      />

      <ChatPanel />
    </div>
  );
}
