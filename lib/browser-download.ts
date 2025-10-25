"use client";

interface DownloadOptions {
  content: string;
  filename: string;
  mimeType?: string;
}

export function downloadTextFile({ content, filename, mimeType = "text/plain" }: DownloadOptions) {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.style.display = "none";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}
