"use client";

import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { AskAnswer, AskResponse, AskSource, GlossaryHit } from "@/lib/ask-contract";
import { Badge } from "@/components/ui/badge";
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

function AnswerPanel({ answer, requestId }: { answer: AskAnswer; requestId?: string }) {
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
      {answer.sources?.length ? (
        <div className="mt-4 space-y-1 text-xs text-slate-600 dark:text-slate-300">
          <p className="font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Citations:
          </p>
          {answer.sources.map((source, index) => (
            <p key={`${source.path}-${index}`} className="truncate">
              {source.path}
            </p>
          ))}
        </div>
      ) : null}
      <div className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
        <p>
          Confidence: {formatConfidence(answer.confidence)} · Escalate:{" "}
          {answer.should_escalate ? "Yes" : "No"}
        </p>
        {requestId ? <p className="truncate">Request ID: {requestId}</p> : null}
      </div>
    </section>
  );
}

export default function AnswerRenderer({ text, response, disabled, onClarify }: AnswerRendererProps) {
  const families = useMemo(() => modelCatalog.families ?? [], []);

  const glossaryHighlights = useMemo(() => {
    if (!response?.glossaryHits?.length) {
      return null;
    }
    return (
      <section className="rounded-2xl border border-amber-200 bg-amber-50/80 p-4 shadow-sm dark:border-amber-900/60 dark:bg-amber-950/40">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100">Glossary highlights</h3>
            <p className="text-xs text-amber-800/80 dark:text-amber-200/80">
              Definitions were pulled from the enterprise glossary for matched terms.
            </p>
          </div>
        </header>
        <ul className="mt-3 space-y-3">
          {response.glossaryHits.map((hit) => (
            <GlossaryHighlightItem key={`${hit.term}-${hit.matchedValue}`} hit={hit} />
          ))}
        </ul>
      </section>
    );
  }, [response?.glossaryHits]);

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
          <AnswerPanel
            key={`${answer.model ?? answer.family ?? "answer"}-${answer.answer.slice(0, 16)}`}
            answer={answer}
            requestId={response?.request_id}
          />
        ))}
      </div>
    );
  }, [response?.answers, response?.request_id]);

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
      {glossaryHighlights}
      {clarificationCard}
      {clarificationCard ? null : answerSections ?? fallbackMarkdown}
    </div>
  );
}

function GlossaryHighlightItem({ hit }: { hit: GlossaryHit }) {
  return (
    <li className="rounded-xl border border-amber-200/80 bg-white/80 p-3 dark:border-amber-900/60 dark:bg-slate-900/60">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{hit.term}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Matched “{hit.matchedValue}”</p>
        </div>
        <Badge variant="subtle" className="text-xs capitalize">
          Glossary term
        </Badge>
      </div>
      <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">{hit.definition}</p>
      <dl className="mt-3 grid gap-2 text-xs text-slate-600 dark:text-slate-300 sm:grid-cols-3">
        {hit.aliases.length ? (
          <div>
            <dt className="font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Aliases
            </dt>
            <dd>{hit.aliases.join(", ")}</dd>
          </div>
        ) : null}
        {hit.units.length ? (
          <div>
            <dt className="font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Units</dt>
            <dd>{hit.units.join(", ")}</dd>
          </div>
        ) : null}
        {hit.productFamilies.length ? (
          <div>
            <dt className="font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Product families
            </dt>
            <dd>{hit.productFamilies.join(", ")}</dd>
          </div>
        ) : null}
      </dl>
    </li>
  );
}
