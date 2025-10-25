import { describe, expect, it } from "vitest";

import {
  BatchParseError,
  generateBatchResultsCsv,
  generateBatchTemplateCsv,
  parseBatchCsv,
} from "@/lib/batch-csv";

describe("parseBatchCsv", () => {
  it("parses a valid CSV into question rows", () => {
    const csv = "ID,Product,Question\n123,Printer," +
      '"What is the duty cycle?"\n';
    const rows = parseBatchCsv(csv);
    expect(rows).toEqual([
      { id: "123", product: "Printer", question: "What is the duty cycle?" },
    ]);
  });

  it("throws BatchParseError when header is invalid", () => {
    const csv = "Wrong,Header,Values\n1,Prod,Question?\n";
    expect(() => parseBatchCsv(csv)).toThrowError(BatchParseError);
  });

  it("throws BatchParseError when question is blank", () => {
    const csv = "ID,Product,Question\n1,Prod,\n";
    expect(() => parseBatchCsv(csv)).toThrowError(BatchParseError);
  });
});

describe("generateBatchTemplateCsv", () => {
  it("produces a header-only CSV", () => {
    const csv = generateBatchTemplateCsv();
    expect(csv.trim()).toBe("ID,Product,Question");
  });
});

describe("generateBatchResultsCsv", () => {
  it("renders export rows with confidence", () => {
    const csv = generateBatchResultsCsv([
      {
        id: "row-1",
        product: "Apeos",
        question: "What is the toner yield?",
        answer: "The toner yields 5K pages.",
        citation: "manual.pdf · page 5",
        confidence: 0.87,
      },
      {
        id: "row-2",
        product: "",
        question: "",
        answer: "Error: Unable to generate answer.",
        citation: "",
        confidence: "",
      },
    ]);

    const lines = csv.split(/\r?\n/).filter((line) => line.length > 0);
    expect(lines[0]).toBe("ID,Product,Question,Answer,Citation,Confidence");
    expect(lines[1]).toContain("row-1");
    expect(lines[1]).toContain("0.87");
    expect(lines[2]).toContain("Error: Unable to generate answer.");
  });
});
