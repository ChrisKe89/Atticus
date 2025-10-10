"use client";

import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { AskAnswer, AskResponse, AskSource } from "@/lib/ask-contract";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import catalog from "@/indices/model_catalog.json";

type AnswerRendererProps = {
  text: string;
  response?: AskResponse;
  disabled?: boolean;
  onClarify?: (models: string[]) => void;
};

type CatalogModel = {
  canonical: string;
  aliases?: string[];
};

type CatalogFamily = {
  id: string;
  label: string;
  aliases?: string[];
  models: CatalogModel[];
};

type ModelCatalog = {
  families: CatalogFamily[];
};

const modelCatalog = catalog as ModelCatalog;

function formatConfidence(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

function SourcesList({ sources }: { sources: AskSource[] }) {
  if (!sources.length) {
    return null;
  }
  return (
    <div className="mt-3 space-y-1 text-xs text-slate-600 dark:text-slate-300">
      {sources.map((source, index) => (
        <div key={`${source.path}-${index}`} className="flex gap-2">
          <span className="mt-1 h-1.5 w-1.5 flex-none rounded-full bg-indigo-500" aria-hidden="true" />
          <span>
            {source.path}
            {typeof source.page === "number" ? ` · page ${source.page}` : ""}
            {source.heading ? ` · ${source.heading}` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

function AnswerPanel({ answer }: { answer: AskAnswer }) {
  const title = answer.model ?? answer.family_label ?? answer.family ?? "Answer";
  return (
    <section className="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/70">
      <header className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{title}</h3>
          {answer.family && answer.model ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">Family {answer.family}</p>
          ) : null}
        </div>
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
          Confidence {formatConfidence(answer.confidence)}
        </span>
      </header>
      <div className="prose prose-sm max-w-none dark:prose-invert">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ node, ...props }) => <p className="my-2 leading-relaxed" {...props} />,
            ul: ({ node, ...props }) => <ul className="my-2 ml-5 list-disc" {...props} />,
            ol: ({ node, ...props }) => <ol className="my-2 ml-5 list-decimal" {...props} />,
            li: ({ node, ...props }) => <li className="my-1" {...props} />,
            strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
          }}
        >
          {answer.answer}
        </ReactMarkdown>
      </div>
      <SourcesList sources={answer.sources ?? []} />
    </section>
  );
}

export default function AnswerRenderer({ text, response, disabled, onClarify }: AnswerRendererProps) {
  const families = useMemo(() => modelCatalog.families ?? [], []);

  const clarificationCard = useMemo(() => {
    if (!response?.clarification) {
      return null;
    }
    return (
      <Card className="border border-indigo-200 bg-indigo-50/60 shadow-sm dark:border-indigo-900/70 dark:bg-indigo-950/50">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-indigo-900 dark:text-indigo-100">Need a little more detail</CardTitle>
          <CardDescription className="text-sm text-indigo-800 dark:text-indigo-200">
            {response.clarification.message}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {response.clarification.options.map((option) => (
            <Button
              key={option.id}
              size="sm"
              variant="secondary"
              disabled={disabled}
              onClick={() => onClarify?.([option.id])}
            >
              {option.label}
            </Button>
          ))}
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm" variant="outline" disabled={disabled}>
                Show list of models
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Select a model family</DialogTitle>
                <DialogDescription>
                  Review the available families and their representative models.
                </DialogDescription>
              </DialogHeader>
              <div className="max-h-64 space-y-4 overflow-y-auto pr-1">
                {families.map((family) => (
                  <div
                    key={family.id}
                    className="rounded-lg border border-slate-200 bg-slate-50/60 p-3 dark:border-slate-700 dark:bg-slate-800/70"
                  >
                    <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                      {family.label}
                    </h4>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-300">Models:</p>
                    <ul className="mt-1 space-y-0.5 text-xs text-slate-600 dark:text-slate-300">
                      {family.models.map((model) => (
                        <li key={`${family.id}-${model.canonical}`}>{model.canonical}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="secondary">Close</Button>
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    );
  }, [disabled, families, onClarify, response?.clarification]);

  const answerSections = useMemo(() => {
    if (!response?.answers || response.answers.length === 0) {
      return null;
    }
    return (
      <div className="space-y-4">
        {response.answers.map((answer) => (
          <AnswerPanel key={`${answer.model ?? answer.family ?? "answer"}-${answer.answer.slice(0, 16)}`} answer={answer} />
        ))}
      </div>
    );
  }, [response?.answers]);

  const fallbackMarkdown = useMemo(() => {
    const content = response?.answer ?? text;
    if (!content) {
      return null;
    }
    return (
      <div className="prose prose-sm max-w-none dark:prose-invert">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ node, ...props }) => <p className="my-2 leading-relaxed" {...props} />,
            ul: ({ node, ...props }) => <ul className="my-2 ml-5 list-disc" {...props} />,
            ol: ({ node, ...props }) => <ol className="my-2 ml-5 list-decimal" {...props} />,
            li: ({ node, ...props }) => <li className="my-1" {...props} />,
            strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  }, [response?.answer, text]);

  return (
    <div className="space-y-4">
      {clarificationCard}
      {clarificationCard ? null : answerSections ?? fallbackMarkdown}
    </div>
  );
}
