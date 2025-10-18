"use client";

import { useState, useTransition } from "react";
import { GlossaryStatus } from "@prisma/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  aliases: string[];
  units: string[];
  productFamilies: string[];
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
  canEdit?: boolean;
}

const statusOptions: GlossaryStatus[] = [
  GlossaryStatus.PENDING,
  GlossaryStatus.APPROVED,
  GlossaryStatus.REJECTED,
];

export function GlossaryAdminPanel({ initialEntries, canEdit = true }: GlossaryAdminPanelProps) {
  const [entries, setEntries] = useState(initialEntries);
  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [synonyms, setSynonyms] = useState("");
  const [aliases, setAliases] = useState("");
  const [units, setUnits] = useState("");
  const [families, setFamilies] = useState("");
  const [status, setStatus] = useState<GlossaryStatus>(GlossaryStatus.PENDING);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [definitionDraft, setDefinitionDraft] = useState("");
  const [synonymsDraft, setSynonymsDraft] = useState("");
  const [aliasesDraft, setAliasesDraft] = useState("");
  const [unitsDraft, setUnitsDraft] = useState("");
  const [familiesDraft, setFamiliesDraft] = useState("");

  function parseList(value: string): string[] {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }

  async function createEntry() {
    if (!canEdit) {
      return;
    }
    setFeedback(null);
    startTransition(async () => {
      const response = await fetch("/api/glossary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          term,
          definition,
          status,
          synonyms: parseList(synonyms),
          aliases: parseList(aliases),
          units: parseList(units),
          productFamilies: parseList(families),
        }),
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
      setAliases("");
      setUnits("");
      setFamilies("");
      setStatus(GlossaryStatus.PENDING);
      setFeedback("Entry created successfully.");
    });
  }

  function beginEditing(entry: GlossaryEntryDto) {
    setEditingId(entry.id);
    setDefinitionDraft(entry.definition);
    setSynonymsDraft(entry.synonyms.join(", "));
    setAliasesDraft(entry.aliases.join(", "));
    setUnitsDraft(entry.units.join(", "));
    setFamiliesDraft(entry.productFamilies.join(", "));
    setFeedback(null);
  }

  function cancelEditing() {
    setEditingId(null);
    setDefinitionDraft("");
    setSynonymsDraft("");
    setAliasesDraft("");
    setUnitsDraft("");
    setFamiliesDraft("");
  }

  async function saveEntryUpdate(
    entry: GlossaryEntryDto,
    overrides: Partial<{
      definition: string;
      synonyms: string[];
      aliases: string[];
      units: string[];
      productFamilies: string[];
      status: GlossaryStatus;
      reviewNotes: string | null;
    }>
  ) {
    if (!canEdit) {
      return null;
    }
    const payload = {
      term: entry.term,
      definition: overrides.definition ?? entry.definition,
      synonyms: overrides.synonyms ?? entry.synonyms,
      aliases: overrides.aliases ?? entry.aliases,
      units: overrides.units ?? entry.units,
      productFamilies: overrides.productFamilies ?? entry.productFamilies,
      status: overrides.status ?? entry.status,
      reviewNotes: overrides.reviewNotes ?? entry.reviewNotes,
    };
    const response = await fetch(`/api/glossary/${entry.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setFeedback(body.detail ?? "Unable to update entry.");
      return null;
    }
    const updated: GlossaryEntryDto = await response.json();
    setEntries((prev) => prev.map((item) => (item.id === entry.id ? updated : item)));
    return updated;
  }

  async function updateStatus(entry: GlossaryEntryDto, nextStatus: GlossaryStatus) {
    if (!canEdit) {
      return;
    }
    startTransition(async () => {
      let reviewNotes: string | null | undefined;
      if (nextStatus !== GlossaryStatus.PENDING) {
        reviewNotes =
          window.prompt("Add review notes (optional)", entry.reviewNotes ?? "") ?? undefined;
      }
      const updated = await saveEntryUpdate(entry, {
        status: nextStatus,
        reviewNotes: reviewNotes === undefined ? entry.reviewNotes : reviewNotes ?? null,
      });
      if (updated) {
        setFeedback(`Status updated to ${nextStatus.toLowerCase()}.`);
      }
    });
  }

  async function deleteEntry(entryId: string) {
    if (!canEdit) {
      return;
    }
    startTransition(async () => {
      const response = await fetch(`/api/glossary/${entryId}`, { method: "DELETE" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
      setFeedback(body.detail ?? "Unable to delete entry.");
      return;
      }
      setEntries((prev) => prev.filter((item) => item.id !== entryId));
      setFeedback("Entry deleted.");
      if (editingId === entryId) {
        cancelEditing();
      }
    });
  }

  function submitDraft(entry: GlossaryEntryDto) {
    if (!canEdit) {
      return;
    }
    const trimmedDefinition = definitionDraft.trim();
    if (!trimmedDefinition) {
      setFeedback("Definition is required.");
      return;
    }
    setFeedback(null);
    startTransition(async () => {
      const updated = await saveEntryUpdate(entry, {
        definition: trimmedDefinition,
        synonyms: parseList(synonymsDraft),
        aliases: parseList(aliasesDraft),
        units: parseList(unitsDraft),
        productFamilies: parseList(familiesDraft),
      });
      if (updated) {
        setFeedback("Entry updated.");
        cancelEditing();
      }
    });
  }

  return (
    <section className="space-y-6">
      <Card>
        <CardHeader className="pb-4">
          <CardTitle>Add glossary entry</CardTitle>
          <CardDescription>
            Approved terms appear instantly in chat responses. Pending entries stay private until
            promoted.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="term">Term</Label>
            <Input
              id="term"
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              placeholder="Consumables"
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select
              id="status"
              value={status}
              onChange={(event) => setStatus(event.target.value as GlossaryStatus)}
              disabled={!canEdit}
            >
              {statusOptions.map((option) => (
                <option key={option} value={option}>
                  {option.toLowerCase()}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="synonyms">Synonyms</Label>
            <Input
              id="synonyms"
              value={synonyms}
              onChange={(event) => setSynonyms(event.target.value)}
              placeholder="Comma-separated list"
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="aliases">Aliases</Label>
            <Input
              id="aliases"
              value={aliases}
              onChange={(event) => setAliases(event.target.value)}
              placeholder="Alternate spellings or nicknames"
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="units">Units</Label>
            <Input
              id="units"
              value={units}
              onChange={(event) => setUnits(event.target.value)}
              placeholder="Comma-separated units (e.g., ppm, g/m²)"
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="families">Product families</Label>
            <Input
              id="families"
              value={families}
              onChange={(event) => setFamilies(event.target.value)}
              placeholder="Canonical product families"
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="definition">Definition</Label>
            <Textarea
              id="definition"
              value={definition}
              onChange={(event) => setDefinition(event.target.value)}
              rows={4}
              placeholder="How the team uses this term..."
              disabled={!canEdit}
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <Button type="button" disabled={isPending || !term || !definition || !canEdit} onClick={createEntry}>
            {isPending ? "Saving…" : "Save entry"}
          </Button>
          <div className="flex flex-1 items-center justify-end gap-2">
            {!canEdit ? (
              <Badge variant="outline" className="normal-case">
                Reviewer access is read-only
              </Badge>
            ) : null}
            {feedback ? (
              <Badge variant="subtle" className="normal-case">
                {feedback}
              </Badge>
            ) : null}
          </div>
        </CardFooter>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle>Glossary entries</CardTitle>
          <CardDescription>
            Review pending definitions, promote approved terms, and prune duplicates in one place.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
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
                    {editingId === entry.id ? (
                      <div className="space-y-3">
                        <Textarea
                          value={definitionDraft}
                          onChange={(event) => setDefinitionDraft(event.target.value)}
                          rows={4}
                          disabled={!canEdit || isPending}
                        />
                        <Input
                          value={synonymsDraft}
                          onChange={(event) => setSynonymsDraft(event.target.value)}
                          placeholder="Comma-separated synonyms"
                          disabled={!canEdit || isPending}
                        />
                        <Input
                          value={aliasesDraft}
                          onChange={(event) => setAliasesDraft(event.target.value)}
                          placeholder="Comma-separated aliases"
                          disabled={!canEdit || isPending}
                        />
                        <Input
                          value={unitsDraft}
                          onChange={(event) => setUnitsDraft(event.target.value)}
                          placeholder="Comma-separated units"
                          disabled={!canEdit || isPending}
                        />
                        <Input
                          value={familiesDraft}
                          onChange={(event) => setFamiliesDraft(event.target.value)}
                          placeholder="Comma-separated product families"
                          disabled={!canEdit || isPending}
                        />
                      </div>
                    ) : (
                      <>
                        <p>{entry.definition}</p>
                        {entry.synonyms.length ? (
                          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                            Synonyms: {entry.synonyms.join(", ")}
                          </p>
                        ) : null}
                        {entry.aliases.length ? (
                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            Aliases: {entry.aliases.join(", ")}
                          </p>
                        ) : null}
                        {entry.units.length ? (
                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            Units: {entry.units.join(", ")}
                          </p>
                        ) : null}
                        {entry.productFamilies.length ? (
                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            Product families: {entry.productFamilies.join(", ")}
                          </p>
                        ) : null}
                        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                          Added by {entry.author?.name ?? entry.author?.email ?? "unknown"}
                        </p>
                      </>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        entry.status === GlossaryStatus.APPROVED
                          ? "success"
                          : entry.status === GlossaryStatus.REJECTED
                          ? "destructive"
                          : "warning"
                      }
                    >
                      {entry.status.toLowerCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <p>{new Date(entry.updatedAt).toLocaleString()}</p>
                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                      By {entry.updatedBy?.name ?? entry.updatedBy?.email ?? "system"}
                    </p>
                    {entry.reviewedAt ? (
                      <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                        Reviewed {new Date(entry.reviewedAt).toLocaleString()} by {" "}
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
                    <div className="flex flex-wrap justify-end gap-2">
                      {editingId === entry.id ? (
                        <>
                          <Button
                            type="button"
                            size="sm"
                            onClick={() => submitDraft(entry)}
                            disabled={isPending || !canEdit}
                          >
                            Save
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={cancelEditing}
                            disabled={isPending}
                          >
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => beginEditing(entry)}
                          disabled={isPending || !canEdit}
                        >
                          Edit
                        </Button>
                      )}
                      {statusOptions.map((option) => (
                        <Button
                          key={option}
                          type="button"
                          size="sm"
                          variant={option === entry.status ? "secondary" : "outline"}
                          disabled={
                            option === entry.status || isPending || !canEdit || editingId === entry.id
                          }
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
                        disabled={isPending || !canEdit}
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
        </CardContent>
      </Card>
    </section>
  );
}
