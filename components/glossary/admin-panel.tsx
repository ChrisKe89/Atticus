'use client';

import { useState, useTransition } from 'react';
import { GlossaryStatus } from '@prisma/client';

export interface GlossaryEntryDto {
  id: string;
  term: string;
  definition: string;
  status: GlossaryStatus;
  createdAt: string;
  updatedAt: string;
  author: { id: string; email: string | null; name: string | null } | null;
  updatedBy: { id: string; email: string | null; name: string | null } | null;
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
  const [term, setTerm] = useState('');
  const [definition, setDefinition] = useState('');
  const [status, setStatus] = useState<GlossaryStatus>(GlossaryStatus.PENDING);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function createEntry() {
    setFeedback(null);
    startTransition(async () => {
      const response = await fetch('/api/glossary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ term, definition, status }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? 'Unable to create entry.');
        return;
      }
      const created: GlossaryEntryDto = await response.json();
      setEntries((prev) => [...prev, created].sort((a, b) => a.term.localeCompare(b.term)));
      setTerm('');
      setDefinition('');
      setStatus(GlossaryStatus.PENDING);
      setFeedback('Entry created successfully.');
    });
  }

  async function updateStatus(entryId: string, nextStatus: GlossaryStatus) {
    startTransition(async () => {
      const response = await fetch(`/api/glossary/${entryId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? 'Unable to update entry.');
        return;
      }
      const updated: GlossaryEntryDto = await response.json();
      setEntries((prev) => prev.map((item) => (item.id === entryId ? updated : item)));
      setFeedback(`Status updated to ${nextStatus.toLowerCase()}.`);
    });
  }

  async function deleteEntry(entryId: string) {
    startTransition(async () => {
      const response = await fetch(`/api/glossary/${entryId}`, { method: 'DELETE' });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? 'Unable to delete entry.');
        return;
      }
      setEntries((prev) => prev.filter((item) => item.id !== entryId));
      setFeedback('Entry deleted.');
    });
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Add glossary entry</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Approved terms appear instantly in chat responses. Pending entries stay private until promoted.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm">
            <span className="font-medium text-slate-700 dark:text-slate-200">Term</span>
            <input
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              placeholder="Consumables"
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-slate-700 dark:text-slate-200">Status</span>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value as GlossaryStatus)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              {statusOptions.map((option) => (
                <option key={option} value={option}>
                  {option.toLowerCase()}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="mt-4 block space-y-2 text-sm">
          <span className="font-medium text-slate-700 dark:text-slate-200">Definition</span>
          <textarea
            value={definition}
            onChange={(event) => setDefinition(event.target.value)}
            rows={4}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            placeholder="How the team uses this term..."
          />
        </label>
        <div className="mt-4 flex items-center justify-between">
          <button
            type="button"
            disabled={isPending || !term || !definition}
            onClick={createEntry}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-400"
          >
            {isPending ? 'Saving…' : 'Save entry'}
          </button>
          {feedback ? <p className="text-xs text-slate-500 dark:text-slate-400">{feedback}</p> : null}
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-900/60">
            <tr>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200">
                Term
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200">
                Definition
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200">
                Status
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200">
                Updated
              </th>
              <th scope="col" className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-200">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {entries.map((entry) => (
              <tr key={entry.id} className="align-top">
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{entry.term}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                  <p>{entry.definition}</p>
                  <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                    Added by {entry.author?.name ?? entry.author?.email ?? 'unknown'}
                  </p>
                </td>
                <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{entry.status.toLowerCase()}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                  <p>{new Date(entry.updatedAt).toLocaleString()}</p>
                  <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                    By {entry.updatedBy?.name ?? entry.updatedBy?.email ?? 'system'}
                  </p>
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    {statusOptions.map((option) => (
                      <button
                        key={option}
                        type="button"
                        className={
                          option === entry.status
                            ? 'rounded-full border border-indigo-200 bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700'
                            : 'rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:border-indigo-300 hover:text-indigo-600'
                        }
                        disabled={option === entry.status || isPending}
                        onClick={() => updateStatus(entry.id, option)}
                      >
                        {option.toLowerCase()}
                      </button>
                    ))}
                    <button
                      type="button"
                      className="rounded-full border border-rose-200 px-3 py-1 text-xs text-rose-600 hover:bg-rose-50"
                      onClick={() => deleteEntry(entry.id)}
                      disabled={isPending}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {entries.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-500 dark:text-slate-400">
                  No glossary entries yet. Create one above to seed the knowledge base.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
