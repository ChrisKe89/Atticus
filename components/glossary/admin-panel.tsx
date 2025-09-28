"use client";

import { useState, useTransition } from "react";
import { GlossaryStatus } from "@prisma/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";

export interface GlossaryEntryDto {
  id: string;
  term: string;
  definition: string;
  synonyms: string[];
  status: GlossaryStatus;
  createdAt: string;
  updatedAt: string;
  reviewedAt: string | null;
  author: { id: string; email: string | null; name: string | null } | null;
  updatedBy: { id: string; email: string | null; name: string | null } | null;
  reviewer: { id: string; email: string | null; name: string | null } | null;
  reviewNotes: string | null;
}

interface GlossaryAdminPanelProps {
  initialEntries: GlossaryEntryDto[];
}

const statusOptions: GlossaryStatus[] = [
  GlossaryStatus.PENDING,
  GlossaryStatus.APPROVED,
  GlossaryStatus.REJECTED,
];

export function GlossaryAdminPanel({ initialEntries }: GlossaryAdminPanelProps) {
  const [entries, setEntries] = useState(initialEntries);
  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [synonyms, setSynonyms] = useState("");
  const [status, setStatus] = useState<GlossaryStatus>(GlossaryStatus.PENDING);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function parseSynonyms(value: string): string[] {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }

  async function createEntry() {
    setFeedback(null);
    startTransition(async () => {
      const response = await fetch("/api/glossary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ term, definition, status, synonyms: parseSynonyms(synonyms) }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? "Unable to create entry.");
        return;
      }
      const created: GlossaryEntryDto = await response.json();
      setEntries((prev) => [...prev, created].sort((a, b) => a.term.localeCompare(b.term)));
      setTerm("");
      setDefinition("");
      setSynonyms("");
      setStatus(GlossaryStatus.PENDING);
      setFeedback("Entry created successfully.");
    });
  }

  async function updateStatus(entry: GlossaryEntryDto, nextStatus: GlossaryStatus) {
    startTransition(async () => {
      let reviewNotes: string | null | undefined;
      if (nextStatus !== GlossaryStatus.PENDING) {
        reviewNotes =
          window.prompt("Add review notes (optional)", entry.reviewNotes ?? "") ?? undefined;
      }
      const response = await fetch(`/api/glossary/${entry.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus, reviewNotes }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? "Unable to update entry.");
        return;
      }
      const updated: GlossaryEntryDto = await response.json();
      setEntries((prev) => prev.map((item) => (item.id === entry.id ? updated : item)));
      setFeedback(`Status updated to ${nextStatus.toLowerCase()}.`);
    });
  }

  async function deleteEntry(entryId: string) {
    startTransition(async () => {
      const response = await fetch(`/api/glossary/${entryId}`, { method: "DELETE" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? "Unable to delete entry.");
        return;
      }
      setEntries((prev) => prev.filter((item) => item.id !== entryId));
      setFeedback("Entry deleted.");
    });
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Add glossary entry</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Approved terms appear instantly in chat responses. Pending entries stay private until
          promoted.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="term">Term</Label>
            <Input
              id="term"
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              placeholder="Consumables"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select
              id="status"
              value={status}
              onChange={(event) => setStatus(event.target.value as GlossaryStatus)}
            >
              {statusOptions.map((option) => (
                <option key={option} value={option}>
                  {option.toLowerCase()}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="synonyms">Synonyms</Label>
          <Input
            id="synonyms"
            value={synonyms}
            onChange={(event) => setSynonyms(event.target.value)}
            placeholder="Comma-separated list"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="definition">Definition</Label>
          <Textarea
            id="definition"
            value={definition}
            onChange={(event) => setDefinition(event.target.value)}
            rows={4}
            placeholder="How the team uses this term..."
          />
        </div>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <Button type="button" disabled={isPending || !term || !definition} onClick={createEntry}>
            {isPending ? "Saving…" : "Save entry"}
          </Button>
          {feedback ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">{feedback}</p>
          ) : null}
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Term</TableHead>
              <TableHead>Definition</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell className="font-medium text-slate-900 dark:text-white">
                  {entry.term}
                </TableCell>
                <TableCell>
                  <p>{entry.definition}</p>
                  {entry.synonyms.length ? (
                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                      Synonyms: {entry.synonyms.join(", ")}
                    </p>
                  ) : null}
                  <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                    Added by {entry.author?.name ?? entry.author?.email ?? "unknown"}
                  </p>
                </TableCell>
                <TableCell className="capitalize">{entry.status.toLowerCase()}</TableCell>
                <TableCell>
                  <p>{new Date(entry.updatedAt).toLocaleString()}</p>
                  <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                    By {entry.updatedBy?.name ?? entry.updatedBy?.email ?? "system"}
                  </p>
                  {entry.reviewedAt ? (
                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                      Reviewed {new Date(entry.reviewedAt).toLocaleString()} by{" "}
                      {entry.reviewer?.name ?? entry.reviewer?.email ?? "admin"}
                    </p>
                  ) : null}
                  {entry.reviewNotes ? (
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      Notes: {entry.reviewNotes}
                    </p>
                  ) : null}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    {statusOptions.map((option) => (
                      <Button
                        key={option}
                        type="button"
                        size="sm"
                        variant={option === entry.status ? "secondary" : "outline"}
                        disabled={option === entry.status || isPending}
                        onClick={() => updateStatus(entry, option)}
                      >
                        {option.toLowerCase()}
                      </Button>
                    ))}
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      onClick={() => deleteEntry(entry.id)}
                      disabled={isPending}
                    >
                      Delete
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {entries.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="py-6 text-center text-sm text-slate-500 dark:text-slate-400"
                >
                  No glossary entries yet. Create one above to seed the knowledge base.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
