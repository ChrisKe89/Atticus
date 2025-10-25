import type { Metadata } from "next";

import { BatchUploadWorkspace } from "@/components/batch/batch-upload-workspace";
import { DownloadTemplateButton } from "@/components/batch/download-template-button";
import { PageHeader } from "@/components/page-header";

export const metadata: Metadata = {
  title: "Batch upload · Atticus",
};

export default function BatchUploadPage() {
  return (
    <div className="pb-16">
      <div className="px-4 pb-6 pt-10 sm:px-6 lg:px-8">
        <PageHeader
          title="Batch upload"
          description="Upload a CSV to generate answers for up to 100 questions at once."
          actions={<DownloadTemplateButton />}
        />
      </div>
      <div className="mx-auto w-full max-w-[1600px] px-4 sm:px-6 lg:px-12">
        <BatchUploadWorkspace />
      </div>
    </div>
  );
}
