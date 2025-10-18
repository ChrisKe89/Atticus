import type { Metadata } from "next";
import { listContent } from "@/lib/content-manager";
import { ContentManager } from "@/components/admin/content-manager";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Content Manager - Atticus",
  description: "Manage source documents and trigger ingestion updates.",
};

export default async function ContentManagerPage() {
  const entries = await listContent(".");

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <ContentManager initialPath="." initialEntries={entries} />
    </div>
  );
}
