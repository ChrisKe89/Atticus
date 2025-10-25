import Papa, { type ParseError, type ParseResult } from "papaparse";

export const BATCH_TEMPLATE_HEADERS = ["ID", "Product", "Question"] as const;
export const BATCH_RESULT_HEADERS = [
  "ID",
  "Product",
  "Question",
  "Answer",
  "Citation",
  "Confidence",
] as const;
export const BATCH_UPLOAD_LIMIT = 100;

export interface BatchQuestionRow {
  id: string;
  product: string;
  question: string;
}

export interface BatchResultExportRow extends BatchQuestionRow {
  answer: string;
  citation: string;
  confidence: number | string | null | undefined;
}

export class BatchParseError extends Error {
  readonly details: string[];

  constructor(message: string, details: string[]) {
    super(message);
    this.name = "BatchParseError";
    this.details = details;
  }
}

function normaliseHeader(value: string): string {
  return value.replace(/^\ufeff/, "").trim().toLowerCase();
}

function normaliseCell(value: unknown): string {
  if (typeof value !== "string") {
    return String(value ?? "").trim();
  }
  return value.trim();
}

export function parseBatchCsv(csvText: string): BatchQuestionRow[] {
  const result: ParseResult<string[]> = Papa.parse<string[]>(csvText, {
    skipEmptyLines: "greedy",
  });

  if (result.errors.length) {
    const errorMessages = result.errors.map((error: ParseError) => {
      const rowNumber = typeof error.row === "number" ? error.row + 1 : "unknown";
      return `Row ${rowNumber}: ${error.message}`;
    });
    throw new BatchParseError("Failed to parse CSV.", errorMessages);
  }

  const rows = result.data as string[][];
  const [rawHeader, ...dataRows] = rows;
  if (!rawHeader || rawHeader.length === 0) {
    throw new BatchParseError("The CSV file is missing the header row.", [
      "Expected columns: ID, Product, Question.",
    ]);
  }

  const expectedHeaders = BATCH_TEMPLATE_HEADERS.map((header) => header.toLowerCase());
  const parsedHeaders = rawHeader.slice(0, expectedHeaders.length).map(normaliseHeader);

  const headerMismatch = expectedHeaders.some((expected, index) => parsedHeaders[index] !== expected);
  if (headerMismatch) {
    throw new BatchParseError("The CSV header does not match the expected template.", [
      `Found header: ${rawHeader.join(", ") || "<empty>"}`,
      "Expected header: ID, Product, Question",
    ]);
  }

  if (!dataRows.length) {
    throw new BatchParseError("No data rows were found in the CSV file.", [
      "Add at least one question row before uploading.",
    ]);
  }

  const errors: string[] = [];
  const questions: BatchQuestionRow[] = [];

  dataRows.forEach((row: string[], index: number) => {
    const rowNumber = index + 2; // account for header row
    const [rawId, rawProduct, rawQuestion, ...rest] = row;
    const id = normaliseCell(rawId);
    const product = normaliseCell(rawProduct);
    const question = normaliseCell(rawQuestion);
    const extraValues = rest.map(normaliseCell).join(" ").trim();

    if (!question) {
      errors.push(`Row ${rowNumber}: question is required.`);
      return;
    }

    if (extraValues) {
      errors.push(`Row ${rowNumber}: unexpected extra column values detected.`);
      return;
    }

    questions.push({
      id,
      product,
      question,
    });
  });

  if (errors.length) {
    throw new BatchParseError("Some rows in the CSV are invalid.", errors);
  }

  return questions;
}

export function generateBatchTemplateCsv(): string {
  return Papa.unparse({
    fields: [...BATCH_TEMPLATE_HEADERS],
    data: [],
  });
}

export function generateBatchResultsCsv(rows: BatchResultExportRow[]): string {
  const data = rows.map((row) => ({
    ID: row.id,
    Product: row.product,
    Question: row.question,
    Answer: row.answer,
    Citation: row.citation,
    Confidence:
      row.confidence === null || row.confidence === undefined
        ? ""
        : typeof row.confidence === "number"
          ? row.confidence.toString()
          : row.confidence,
  }));

  return Papa.unparse({
    fields: [...BATCH_RESULT_HEADERS],
    data: data.map((row) => [row.ID, row.Product, row.Question, row.Answer, row.Citation, row.Confidence]),
  });
}
