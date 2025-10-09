"use client";

import { useMemo, useState, useTransition } from "react";
import { Role } from "@prisma/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GlossaryAdminPanel, GlossaryEntryDto } from "@/components/glossary/admin-panel";

export type SourceSummary = {
  path: string;
  score?: number;
};

export type UncertainChat = {
  id: string;
  question: string;
  confidence: number;
  status: string;
  requestId: string | null;
  createdAt: string;
  topSources: SourceSummary[];
  author: { id: string; email: string | null; name: string | null } | null;
  reviewer: { id: string; email: string | null; name: string | null } | null;
  tickets: Array<{
    id: string;
    key: string;
    status: string;
    assignee: string | null;
    lastActivity: string | null;
  }>;
};

export type TicketSummary = {
  id: string;
  key: string;
  status: string;
  assignee: string | null;
  lastActivity: string | null;
  summary: string | null;
};

interface AdminOpsConsoleProps {
  role: Role;
  uncertain: UncertainChat[];
  tickets: TicketSummary[];
  glossaryEntries: GlossaryEntryDto[];
}

function confidenceVariant(confidence: number): "success" | "warning" | "destructive" {
  if (confidence >= 0.75) {
    return "success";
  }
  if (confidence >= 0.45) {
    return "warning";
  }
  return "destructive";
}

export function AdminOpsConsole({ role, uncertain, tickets, glossaryEntries }: AdminOpsConsoleProps) {
  const [uncertainChats, setUncertainChats] = useState(uncertain);
  const [ticketSummaries, setTicketSummaries] = useState(tickets);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const canApprove = role === Role.ADMIN || role === Role.REVIEWER;
  const canEscalate = role === Role.ADMIN;
  const canManageGlossary = role === Role.ADMIN;
  const defaultTab = role === Role.ADMIN ? "uncertain" : "glossary";

  async function handleApprove(chatId: string) {
    if (!canApprove) {
      return;
    }
    setFeedback(null);
    startTransition(async () => {
      const response = await fetch(`/api/admin/uncertain/${chatId}/approve`, { method: "POST" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? "Unable to approve chat.");
        return;
      }
      setUncertainChats((prev) => prev.filter((chat) => chat.id !== chatId));
      setFeedback("Chat approved and removed from the uncertain queue.");
    });
  }

  async function handleEscalate(chat: UncertainChat) {
    if (!canEscalate) {
      return;
    }
    setFeedback(null);
    startTransition(async () => {
      const response = await fetch(`/api/admin/uncertain/${chat.id}/escalate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary: chat.question, assignee: chat.tickets.at(0)?.assignee ?? null }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setFeedback(body.detail ?? "Unable to escalate chat.");
        return;
      }
      const ticket = (await response.json()) as TicketSummary;
      setUncertainChats((prev) => prev.filter((item) => item.id !== chat.id));
      setTicketSummaries((prev) => [{ ...ticket, summary: chat.question }, ...prev]);
      setFeedback(`Escalated to ticket ${ticket.key}.`);
    });
  }

  const ticketCount = ticketSummaries.length;
  const pendingCount = uncertainChats.length;

  const ticketCards = useMemo(
    () =>
      ticketSummaries.map((ticket) => {
        const lastActivity = ticket.lastActivity ? new Date(ticket.lastActivity).toLocaleString() : "N/A";
        return (
          <Card key={ticket.id} className="border-slate-200 dark:border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span>{ticket.key}</span>
                <Badge variant="outline" className="capitalize">
                  {ticket.status}
                </Badge>
              </CardTitle>
              <CardDescription>Assigned to {ticket.assignee ?? "Unassigned"}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
              <p>{ticket.summary ?? "No summary provided."}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Last activity: {lastActivity}</p>
            </CardContent>
          </Card>
        );
      }),
    [ticketSummaries]
  );

  return (
    <Tabs defaultValue={defaultTab} className="space-y-6">
      <TabsList>
        <TabsTrigger value="uncertain">Uncertain ({pendingCount})</TabsTrigger>
        <TabsTrigger value="tickets">Tickets ({ticketCount})</TabsTrigger>
        <TabsTrigger value="glossary">Glossary</TabsTrigger>
      </TabsList>
      {feedback ? (
        <Badge variant="subtle" className="normal-case">
          {feedback}
        </Badge>
      ) : null}
      <TabsContent value="uncertain">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Question</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Top sources</TableHead>
                <TableHead>Requester</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {uncertainChats.map((chat) => (
                <TableRow key={chat.id}>
                  <TableCell className="max-w-xs align-top">
                    <p className="font-medium text-slate-900 dark:text-white">{chat.question}</p>
                    {chat.requestId ? (
                      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Request {chat.requestId}</p>
                    ) : null}
                  </TableCell>
                  <TableCell className="align-top">
                    <Badge variant={confidenceVariant(chat.confidence)}>
                      {(chat.confidence * 100).toFixed(0)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="align-top text-sm text-slate-600 dark:text-slate-300">
                    <ul className="space-y-1">
                      {chat.topSources.length ? (
                        chat.topSources.map((source, index) => (
                          <li key={`${chat.id}-source-${index}`} className="flex flex-col">
                            <span className="truncate text-xs text-slate-500 dark:text-slate-400">
                              {source.path}
                            </span>
                            {source.score != null ? (
                              <span className="text-xs text-slate-400 dark:text-slate-500">
                                Score {(source.score * 100).toFixed(1)}%
                              </span>
                            ) : null}
                          </li>
                        ))
                      ) : (
                        <li className="text-xs text-slate-500 dark:text-slate-400">No sources captured.</li>
                      )}
                    </ul>
                  </TableCell>
                  <TableCell className="align-top text-sm text-slate-600 dark:text-slate-300">
                    <p>{chat.author?.name ?? chat.author?.email ?? "Unknown"}</p>
                  </TableCell>
                  <TableCell className="align-top text-sm text-slate-600 dark:text-slate-300">
                    {new Date(chat.createdAt).toLocaleString()}
                  </TableCell>
                  <TableCell className="align-top text-right">
                    <div className="flex flex-col items-end gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={!canApprove || isPending}
                        onClick={() => handleApprove(chat.id)}
                      >
                        Approve
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={!canEscalate || isPending}
                        onClick={() => handleEscalate(chat)}
                      >
                        Escalate
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {uncertainChats.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                    All caught up. Pending review chats will appear here automatically.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </div>
      </TabsContent>
      <TabsContent value="tickets">
        <div className="grid gap-4 md:grid-cols-2">{ticketCards}</div>
        {ticketSummaries.length === 0 ? (
          <Card className="mt-4 border-dashed">
            <CardHeader>
              <CardTitle>No escalations yet</CardTitle>
              <CardDescription>
                Approve chats or escalate them to create AE tickets that appear in this queue.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : null}
      </TabsContent>
      <TabsContent value="glossary" className="p-0">
        <GlossaryAdminPanel initialEntries={glossaryEntries} canEdit={canManageGlossary} />
      </TabsContent>
    </Tabs>
  );
}
