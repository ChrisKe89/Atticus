"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { Loader2, UploadCloud } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { downloadTextFile } from "@/lib/browser-download";
import {
  BATCH_UPLOAD_LIMIT,
  type BatchQuestionRow,
  BatchParseError,
  generateBatchResultsCsv,
  parseBatchCsv,
  type BatchResultExportRow,
} from "@/lib/batch-csv";
import { streamAsk } from "@/lib/ask-client";
import type { AskRequest, AskResponse, AskSource } from "@/lib/ask-contract";

interface BatchRunRow extends BatchQuestionRow {
  status: "pending" | "processing" | "complete" | "error";
  answer: string;
  citations: string[];
  confidence: number | null;
  error?: string;
}

function formatCitation(source: AskSource): string {
  const path = source.path?.trim() ?? "";
  const page = typeof source.page === "number" ? source.page : null;
  const heading = source.heading?.trim() ?? "";
  const segments = [path];
  if (page !== null) {
    segments.push(`page ${page}`);
  }
  if (heading) {
    segments.push(heading);
  }
  return segments.filter(Boolean).join(" · ");
}

function extractCitations(response: AskResponse): string[] {
  const fromResponse = response.sources ?? [];
  const fromAnswers = response.answers?.flatMap((answer) => answer.sources ?? []) ?? [];
  const combined: AskSource[] = [...fromResponse, ...fromAnswers];
  const seen = new Set<string>();
  const formatted: string[] = [];
  for (const source of combined) {
    const citation = formatCitation(source);
    if (!citation) {
      continue;
    }
    if (seen.has(citation)) {
      continue;
    }
    seen.add(citation);
    formatted.push(citation);
  }
  return formatted;
}

function extractAnswer(response: AskResponse): string {
  if (response.answer && response.answer.trim()) {
    return response.answer.trim();
  }
  if (response.answers?.length) {
    return response.answers.map((entry) => entry.answer).filter(Boolean).join("\n\n").trim();
  }
  if (response.clarification) {
    return response.clarification.message;
  }
  return "";
}

function extractConfidence(response: AskResponse): number | null {
  if (typeof response.confidence === "number") {
    return response.confidence;
  }
  if (response.answers?.length) {
    const confidences = response.answers
      .map((entry) => entry.confidence)
      .filter((value): value is number => typeof value === "number");
    if (confidences.length) {
      return Math.min(...confidences);
    }
  }
  return null;
}

async function resolveQuestion(question: string, product?: string): Promise<AskResponse> {
  const normalizedProduct = product?.trim();
  const batchHints: string[] = [
    "These questions originated from the batch uploader. Provide concise, grounded answers suitable for a CSV export.",
  ];
  if (normalizedProduct) {
    batchHints.push(
      `Focus exclusively on the ${normalizedProduct} product or family. Ignore specifications for other models even if they appear in the retrieved context.`
    );
  }
  const scopedQuestion =
    normalizedProduct && !question.toLowerCase().includes(normalizedProduct.toLowerCase())
      ? `${question.trim()} (Answer strictly for ${normalizedProduct} and do not mention other products.)`
      : question.trim();
  const explicitModels = normalizedProduct ? [normalizedProduct] : undefined;
  const baseRequest: AskRequest = {
    question: scopedQuestion,
    filters: undefined,
    contextHints: batchHints,
    topK: undefined,
    models: explicitModels,
  };
  const primary = await streamAsk(baseRequest);
  if (!primary.clarification?.options?.length) {
    return primary;
  }
  for (const option of primary.clarification.options) {
    const followUp = await streamAsk({ ...baseRequest, models: [option.id] });
    if (!followUp.clarification) {
      return followUp;
    }
  }
  return primary;
}

function buildExportRows(rows: BatchRunRow[]): BatchResultExportRow[] {
  return rows.map((row) => ({
    id: row.id,
    product: row.product,
    question: row.question,
    answer: row.status === "error" ? `Error: ${row.error ?? "Unable to generate answer."}` : row.answer,
    citation: row.citations.join("; "),
    confidence:
      row.status === "complete" && row.confidence !== null
        ? Number.isFinite(row.confidence)
          ? row.confidence.toFixed(3)
          : ""
        : row.status === "error"
          ? ""
          : row.confidence,
  }));
}

export function BatchUploadWorkspace() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [rows, setRows] = useState<BatchQuestionRow[]>([]);
  const [runRows, setRunRows] = useState<BatchRunRow[]>([]);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedCount, setProcessedCount] = useState(0);
  const [stopRequested, setStopRequested] = useState(false);
  const stopRequestedRef = useRef(false);

  const hasRows = rows.length > 0;
  const completedRows = runRows.filter((row) => row.status === "complete" || row.status === "error");
  const progressLabel = useMemo(() => {
    if (!runRows.length) {
      return null;
    }
    return `${processedCount}/${runRows.length} processed`;
  }, [processedCount, runRows.length]);

  const handleFile = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const [file] = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const text = String(reader.result ?? "");
        const parsedRows = parseBatchCsv(text);
        if (parsedRows.length > BATCH_UPLOAD_LIMIT) {
          setParseErrors([`The file contains ${parsedRows.length} questions, exceeding the limit of ${BATCH_UPLOAD_LIMIT}.`]);
          setRows([]);
          setRunRows([]);
          setFileName(file.name);
          setStatusMessage(null);
          setProcessedCount(0);
          return;
        }
        setRows(parsedRows);
        setRunRows(
          parsedRows.map((row) => ({
            ...row,
            status: "pending",
            answer: "",
            citations: [],
            confidence: null,
            error: undefined,
          }))
        );
        setParseErrors([]);
        setFileName(file.name);
        setStatusMessage(null);
        setProcessedCount(0);
      } catch (error) {
        if (error instanceof BatchParseError) {
          setParseErrors(error.details);
        } else if (error instanceof Error) {
          setParseErrors([error.message]);
        } else {
          setParseErrors(["Unable to read the provided file."]);
        }
        setRows([]);
        setRunRows([]);
        setFileName(file.name);
        setStatusMessage(null);
        setProcessedCount(0);
      }
    };
    reader.onerror = () => {
      setParseErrors(["Failed to read the selected file. Please try again."]);
      setRows([]);
      setRunRows([]);
      setFileName(file.name);
      setStatusMessage(null);
      setProcessedCount(0);
    };
    reader.readAsText(file);
  }, []);

  const handleProcess = useCallback(async () => {
    if (!rows.length || isProcessing) {
      return;
    }
    setIsProcessing(true);
    setStopRequested(false);
    stopRequestedRef.current = false;
    setStatusMessage(null);
    setProcessedCount(0);
    setRunRows((current) =>
      current.map((entry) => ({
        ...entry,
        status: "pending",
        answer: "",
        citations: [],
        confidence: null,
        error: undefined,
      }))
    );

    try {
      for (let index = 0; index < rows.length; index += 1) {
        if (stopRequestedRef.current) {
          break;
        }
        const questionRow = rows[index];
        setRunRows((current) =>
          current.map((entry, position) =>
            position === index
              ? {
                  ...entry,
                  status: "processing",
                  answer: entry.answer,
                  citations: entry.citations,
                  error: undefined,
                }
              : entry
          )
        );

        try {
          const response = await resolveQuestion(questionRow.question, questionRow.product);
          const answer = extractAnswer(response);
          const citations = extractCitations(response);
          const confidence = extractConfidence(response);

          setRunRows((current) =>
            current.map((entry, position) =>
              position === index
                ? {
                    ...entry,
                    status: "complete",
                    answer,
                    citations,
                    confidence,
                    error: undefined,
                  }
                : entry
            )
          );
        } catch (error) {
          const message = error instanceof Error ? error.message : "Unknown error";
          setRunRows((current) =>
            current.map((entry, position) =>
              position === index
                ? {
                    ...entry,
                    status: "error",
                    answer: "",
                    citations: [],
                    confidence: null,
                    error: message,
                  }
                : entry
            )
          );
        }

        setProcessedCount(index + 1);
      }

      if (stopRequestedRef.current) {
        setStatusMessage("Batch processing stopped.");
      } else {
        setStatusMessage("Batch processing complete.");
      }
    } finally {
      setIsProcessing(false);
    }
  }, [isProcessing, rows]);

  const handleStopProcessing = useCallback(() => {
    if (!isProcessing) {
      return;
    }
    stopRequestedRef.current = true;
    setStopRequested(true);
  }, [isProcessing]);

  const handleDownloadResults = useCallback(() => {
    if (!completedRows.length) {
      return;
    }
    const csv = generateBatchResultsCsv(buildExportRows(completedRows));
    downloadTextFile({
      content: csv,
      filename: `atticus-batch-results-${Date.now()}.csv`,
      mimeType: "text/csv",
    });
  }, [completedRows]);

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Upload batch CSV</CardTitle>
          <CardDescription>
            Import up to {BATCH_UPLOAD_LIMIT} questions per batch. The file must include the ID, Product, and Question columns.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
              <p>
                {fileName ? (
                  <>
                    <span className="font-medium text-slate-900 dark:text-slate-100">Selected file:</span> {fileName}
                  </>
                ) : (
                  "No file selected."
                )}
              </p>
              {hasRows ? <p>{rows.length} questions queued.</p> : null}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button type="button" variant="outline" asChild>
                <label className="flex cursor-pointer items-center gap-2">
                  <UploadCloud className="h-4 w-4" aria-hidden="true" />
                  {fileName ? "Replace CSV" : "Choose CSV"}
                  <input type="file" accept=".csv" className="sr-only" onChange={handleFile} />
                </label>
              </Button>
              <Button type="button" onClick={handleProcess} disabled={!hasRows || isProcessing} className="gap-2">
                {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
                {isProcessing ? "Processing" : "Process batch"}
              </Button>
              <Button
                type="button"
                variant="destructive"
                onClick={handleStopProcessing}
                disabled={!isProcessing || stopRequested}
              >
                Stop processing
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleDownloadResults}
                disabled={!completedRows.length}
                className="gap-2"
              >
                Download results
              </Button>
            </div>
          </div>

          {parseErrors.length ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
              <p className="font-semibold">We found some issues with your file:</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {parseErrors.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {statusMessage ? (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-950/40 dark:text-emerald-200">
              {statusMessage}
            </div>
          ) : null}

          {progressLabel ? (
            <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{progressLabel}</p>
          ) : null}
        </CardContent>
      </Card>

      {runRows.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Batch results</CardTitle>
            <CardDescription>
              Track progress and review generated answers. Download the CSV once processing completes.
            </CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[120px]">ID</TableHead>
                  <TableHead className="min-w-[160px]">Product</TableHead>
                  <TableHead className="min-w-[200px]">Question</TableHead>
                  <TableHead className="min-w-[240px]">Answer</TableHead>
                  <TableHead className="min-w-[200px]">Citations</TableHead>
                  <TableHead className="min-w-[120px]">Confidence</TableHead>
                  <TableHead className="min-w-[120px]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runRows.map((row, index) => (
                  <TableRow key={`${row.id || "row"}-${index}`}>
                    <TableCell className="font-medium text-slate-900 dark:text-slate-100">{row.id || "—"}</TableCell>
                    <TableCell>{row.product || "—"}</TableCell>
                    <TableCell className="whitespace-pre-wrap">{row.question}</TableCell>
                    <TableCell className="whitespace-pre-wrap">
                      {row.status === "error" ? (
                        <span className="text-rose-600 dark:text-rose-300">{row.error ?? "Unable to generate answer."}</span>
                      ) : (
                        row.answer || "—"
                      )}
                    </TableCell>
                    <TableCell className="whitespace-pre-wrap">
                      {row.citations.length ? row.citations.join("\n") : "—"}
                    </TableCell>
                    <TableCell>
                      {row.status === "complete"
                        ? row.confidence !== null && Number.isFinite(row.confidence)
                          ? `${(row.confidence * 100).toFixed(1)}%`
                          : "—"
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          row.status === "complete"
                            ? "success"
                            : row.status === "processing"
                              ? "default"
                              : row.status === "error"
                                ? "destructive"
                                : "subtle"
                        }
                      >
                        {row.status === "pending"
                          ? "Queued"
                          : row.status === "processing"
                            ? "Processing"
                            : row.status === "complete"
                              ? "Complete"
                              : "Error"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
