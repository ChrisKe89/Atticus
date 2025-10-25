"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { createId } from "@/lib/id";
import { streamAsk } from "@/lib/ask-client";
import type { AskRequest, AskResponse, AskSource } from "@/lib/ask-contract";

type BatchHistoryStatus = "complete" | "stopped";

interface BatchRunRow extends BatchQuestionRow {
  status: "pending" | "processing" | "complete" | "error";
  answer: string;
  citations: string[];
  confidence: number | null;
  error?: string;
}

interface StoredBatch {
  id: string;
  name: string;
  createdAt: number;
  updatedAt: number;
  rows: BatchQuestionRow[];
  results: BatchRunRow[];
  processedCount: number;
  status: BatchHistoryStatus;
}

const BATCH_HISTORY_STORAGE_KEY = "atticus.batch.history.v1";
const MAX_STORED_BATCHES = 15;

function cloneBatchRows(rows: BatchQuestionRow[]): BatchQuestionRow[] {
  return rows.map((row) => ({ ...row }));
}

function cloneRunRows(rows: BatchRunRow[]): BatchRunRow[] {
  return rows.map((row) => ({ ...row, citations: [...row.citations] }));
}

function sanitizeBatchQuestionRow(value: unknown): BatchQuestionRow | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const { id, product, question } = value as Partial<BatchQuestionRow>;
  if (typeof question !== "string") {
    return null;
  }
  return {
    id: typeof id === "string" ? id : "",
    product: typeof product === "string" ? product : "",
    question,
  } satisfies BatchQuestionRow;
}

function sanitizeBatchRunRow(value: unknown): BatchRunRow | null {
  const base = sanitizeBatchQuestionRow(value);
  if (!base) {
    return null;
  }
  const { status, answer, citations, confidence, error } = value as Partial<BatchRunRow>;
  if (status !== "pending" && status !== "processing" && status !== "complete" && status !== "error") {
    return null;
  }
  return {
    ...base,
    status,
    answer: typeof answer === "string" ? answer : "",
    citations: Array.isArray(citations)
      ? citations.filter((entry): entry is string => typeof entry === "string")
      : [],
    confidence: typeof confidence === "number" && Number.isFinite(confidence) ? confidence : null,
    error: typeof error === "string" ? error : undefined,
  } satisfies BatchRunRow;
}

function sanitizeStoredBatches(value: unknown): StoredBatch[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const { id, name, createdAt, updatedAt, rows, results, processedCount, status } = entry as Partial<StoredBatch> & {
        rows?: unknown;
        results?: unknown;
      };
      if (typeof id !== "string" || typeof name !== "string") {
        return null;
      }
      if (typeof createdAt !== "number" || typeof updatedAt !== "number") {
        return null;
      }
      if (status !== "complete" && status !== "stopped") {
        return null;
      }
      if (!Array.isArray(rows) || !Array.isArray(results)) {
        return null;
      }
      const sanitizedRows = rows
        .map((row) => sanitizeBatchQuestionRow(row))
        .filter((row): row is BatchQuestionRow => Boolean(row));
      if (!sanitizedRows.length) {
        return null;
      }
      const sanitizedResults = results
        .map((row) => sanitizeBatchRunRow(row))
        .filter((row): row is BatchRunRow => Boolean(row));
      const count =
        typeof processedCount === "number" && Number.isFinite(processedCount) && processedCount >= 0
          ? processedCount
          : sanitizedResults.filter((row) => row.status === "complete" || row.status === "error").length;
      return {
        id,
        name,
        createdAt,
        updatedAt,
        rows: sanitizedRows,
        results: sanitizedResults,
        processedCount: count,
        status,
      } satisfies StoredBatch;
    })
    .filter((entry): entry is StoredBatch => Boolean(entry))
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .slice(0, MAX_STORED_BATCHES);
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

function processedEntriesCount(rows: BatchRunRow[]): number {
  return rows.filter((row) => row.status === "complete" || row.status === "error").length;
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

  const [batchHistory, setBatchHistory] = useState<StoredBatch[]>([]);
  const [historyReady, setHistoryReady] = useState(false);
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null);
  const [pendingReprocessId, setPendingReprocessId] = useState<string | null>(null);

  const rowsRef = useRef(rows);
  const runRowsRef = useRef(runRows);
  const fileNameRef = useRef(fileName);

  useEffect(() => {
    rowsRef.current = rows;
  }, [rows]);

  useEffect(() => {
    runRowsRef.current = runRows;
  }, [runRows]);

  useEffect(() => {
    fileNameRef.current = fileName;
  }, [fileName]);

  useEffect(() => {
    if (historyReady) {
      return;
    }
    if (typeof window === "undefined") {
      return;
    }
    try {
      const raw = window.localStorage.getItem(BATCH_HISTORY_STORAGE_KEY);
      if (!raw) {
        setHistoryReady(true);
        return;
      }
      const parsed = JSON.parse(raw) as unknown;
      const sanitized = sanitizeStoredBatches(parsed);
      setBatchHistory(sanitized);
    } catch (error) {
      console.error("Failed to load batch history", error);
      setBatchHistory([]);
    } finally {
      setHistoryReady(true);
    }
  }, [historyReady]);

  useEffect(() => {
    if (!historyReady || typeof window === "undefined") {
      return;
    }
    try {
      window.localStorage.setItem(BATCH_HISTORY_STORAGE_KEY, JSON.stringify(batchHistory));
    } catch (error) {
      console.error("Failed to persist batch history", error);
    }
  }, [batchHistory, historyReady]);

  const persistBatchHistory = useCallback(
    (batchId: string, results: BatchRunRow[], status: BatchHistoryStatus) => {
      const timestamp = Date.now();
      const name = fileNameRef.current ?? `Batch ${new Date(timestamp).toLocaleString()}`;
      const processed = processedEntriesCount(results);
      const clonedResults = cloneRunRows(results);
      const clonedRows = cloneBatchRows(rowsRef.current);
      setBatchHistory((current) => {
        const index = current.findIndex((entry) => entry.id === batchId);
        if (index === -1) {
          const entry: StoredBatch = {
            id: batchId,
            name,
            createdAt: timestamp,
            updatedAt: timestamp,
            rows: clonedRows,
            results: clonedResults,
            processedCount: processed,
            status,
          };
          const next = [entry, ...current];
          next.sort((a, b) => b.updatedAt - a.updatedAt);
          return next.slice(0, MAX_STORED_BATCHES);
        }
        const next = [...current];
        const existing = next[index];
        next[index] = {
          ...existing,
          name,
          updatedAt: timestamp,
          rows: clonedRows,
          results: clonedResults,
          processedCount: processed,
          status,
        };
        next.sort((a, b) => b.updatedAt - a.updatedAt);
        return next.slice(0, MAX_STORED_BATCHES);
      });
    },
    []
  );

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
          setActiveBatchId(createId("batch"));
          setPendingReprocessId(null);
          return;
        }
        const batchId = createId("batch");
        setActiveBatchId(batchId);
        setRows(parsedRows);
        setRunRows(
          parsedRows.map((row) => ({
            ...row,
            status: "pending" as const,
            answer: "",
            citations: [] as string[],
            confidence: null,
            error: undefined,
          }))
        );
        setParseErrors([]);
        setFileName(file.name);
        setStatusMessage(null);
        setProcessedCount(0);
        setPendingReprocessId(null);
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
        setActiveBatchId(createId("batch"));
        setPendingReprocessId(null);
      }
    };
    reader.onerror = () => {
      setParseErrors(["Failed to read the selected file. Please try again."]);
      setRows([]);
      setRunRows([]);
      setFileName(file.name);
      setStatusMessage(null);
      setProcessedCount(0);
      setActiveBatchId(createId("batch"));
      setPendingReprocessId(null);
    };
    reader.readAsText(file);
  }, []);

  const handleProcess = useCallback(async () => {
    if (!rows.length || isProcessing) {
      return;
    }
    const batchId = activeBatchId ?? createId("batch");
    if (!activeBatchId) {
      setActiveBatchId(batchId);
    }
    setIsProcessing(true);
    setStopRequested(false);
    stopRequestedRef.current = false;
    setStatusMessage(null);
    setProcessedCount(0);
    setPendingReprocessId(null);
    let latestResults: BatchRunRow[] = [];
    setRunRows((current) => {
      const reset = current.map((entry) => ({
        ...entry,
        status: "pending" as const,
        answer: "",
        citations: [] as string[],
        confidence: null,
        error: undefined,
      }));
      latestResults = reset;
      return reset;
    });

    try {
      for (let index = 0; index < rows.length; index += 1) {
        if (stopRequestedRef.current) {
          break;
        }
        const questionRow = rows[index];
        setRunRows((current) => {
          const next = current.map((entry, position) =>
            position === index
              ? {
                  ...entry,
                  status: "processing" as const,
                  answer: entry.answer,
                  citations: entry.citations,
                  error: undefined,
                }
              : entry
          );
          latestResults = next;
          return next;
        });

        try {
          const response = await resolveQuestion(questionRow.question, questionRow.product);
          const answer = extractAnswer(response);
          const citations = extractCitations(response);
          const confidence = extractConfidence(response);

          setRunRows((current) => {
            const next = current.map((entry, position) =>
            position === index
              ? {
                  ...entry,
                  status: "complete" as const,
                  answer,
                  citations,
                  confidence,
                  error: undefined,
                  }
                : entry
            );
            latestResults = next;
            return next;
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : "Unknown error";
          setRunRows((current) => {
            const next = current.map((entry, position) =>
            position === index
              ? {
                  ...entry,
                  status: "error" as const,
                  answer: "",
                  citations: [] as string[],
                  confidence: null,
                  error: message,
                }
                : entry
            );
            latestResults = next;
            return next;
          });
        }

        setProcessedCount(index + 1);
      }

      const historyResults = latestResults.length ? latestResults : runRowsRef.current;
      if (stopRequestedRef.current) {
        setStatusMessage("Batch processing stopped.");
        persistBatchHistory(batchId, historyResults, "stopped");
      } else {
        setStatusMessage("Batch processing complete.");
        persistBatchHistory(batchId, historyResults, "complete");
      }
    } finally {
      setIsProcessing(false);
    }
  }, [rows, isProcessing, activeBatchId, persistBatchHistory]);

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

  const handleLoadBatch = useCallback(
    (entry: StoredBatch, options?: { reprocess?: boolean }) => {
      if (isProcessing) {
        return;
      }
      setActiveBatchId(entry.id);
      setRows(cloneBatchRows(entry.rows));
      const baseResults = entry.results.length
        ? entry.results
        : entry.rows.map((row) => ({
            ...row,
            status: "pending" as const,
            answer: "",
            citations: [] as string[],
            confidence: null,
            error: undefined,
          }));
      setRunRows(cloneRunRows(baseResults));
      setParseErrors([]);
      setFileName(entry.name);
      setProcessedCount(entry.processedCount);
      setStatusMessage(
        entry.status === "complete"
          ? `Last processed on ${new Date(entry.updatedAt).toLocaleString()}.`
          : `Processing stopped on ${new Date(entry.updatedAt).toLocaleString()}.`
      );
      setStopRequested(false);
      stopRequestedRef.current = false;
      setPendingReprocessId(options?.reprocess ? entry.id : null);
    },
    [isProcessing]
  );

  useEffect(() => {
    if (!pendingReprocessId) {
      return;
    }
    if (pendingReprocessId !== activeBatchId) {
      return;
    }
    if (isProcessing) {
      return;
    }
    if (!rows.length) {
      return;
    }
    handleProcess().catch((error) => {
      console.error("Failed to reprocess batch", error);
    });
    setPendingReprocessId(null);
  }, [pendingReprocessId, activeBatchId, isProcessing, rows.length, handleProcess]);

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

      {batchHistory.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Previous batches</CardTitle>
            <CardDescription>Reload a prior CSV run or reprocess it with the latest answers.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {batchHistory.map((entry) => (
              <div
                key={entry.id}
                className="flex flex-col gap-3 rounded-xl border border-slate-200 p-4 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{entry.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {entry.rows.length} questions • {entry.status === "complete" ? "Completed" : "Stopped"} {" "}
                    {new Date(entry.updatedAt).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => handleLoadBatch(entry)}
                    disabled={isProcessing}
                  >
                    View
                  </Button>
                  <Button
                    type="button"
                    onClick={() => handleLoadBatch(entry, { reprocess: true })}
                    disabled={isProcessing}
                    className="gap-2"
                  >
                    Process again
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
