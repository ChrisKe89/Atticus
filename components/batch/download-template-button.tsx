"use client";

import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { downloadTextFile } from "@/lib/browser-download";
import { generateBatchTemplateCsv } from "@/lib/batch-csv";

export function DownloadTemplateButton() {
  const handleClick = () => {
    const csv = generateBatchTemplateCsv();
    downloadTextFile({
      content: csv,
      filename: "atticus-batch-template.csv",
      mimeType: "text/csv",
    });
  };

  return (
    <Button type="button" variant="outline" onClick={handleClick} className="gap-2">
      <Download className="h-4 w-4" aria-hidden="true" />
      Download template
    </Button>
  );
}
