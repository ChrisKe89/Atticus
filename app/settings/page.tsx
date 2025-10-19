import type { Metadata } from "next";
import { Shield, Zap } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const toggles = [
  {
    id: "escalations",
    label: "Escalate low-confidence answers",
    description:
      "Automatically open an escalation email when answer confidence drops below the policy threshold.",
    defaultChecked: true,
  },
  {
    id: "request-logging",
    label: "Attach anonymised request logs",
    description:
      "Include hashed user IDs and request IDs so admins can correlate tickets with chat sessions.",
    defaultChecked: true,
  },
  {
    id: "typing-preview",
    label: "Streaming responses",
    description: "Show tokens as they are generated for faster operator feedback.",
    defaultChecked: false,
  },
];

export const metadata: Metadata = {
  title: "Settings - Atticus",
};

export default function SettingsPage() {
  const adminUrl = (process.env.NEXT_PUBLIC_ADMIN_URL?.trim() || "http://localhost:9000").replace(
    /\/+$/,
    ""
  );

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-10">
      <PageHeader
        eyebrow="Settings"
        title="Workspace preferences"
        description="Configure escalation behaviour, logging guardrails, and chat defaults."
        actions={
          <Button variant="outline" className="rounded-full" asChild>
            <a href={adminUrl} target="_blank" rel="noreferrer">
              Open admin console
            </a>
          </Button>
        }
      />

      <section className="space-y-6">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500">Policies</h2>
        <Card>
          <CardContent className="space-y-4">
            {toggles.map((toggle) => (
              <label
                key={toggle.id}
                htmlFor={toggle.id}
                className="flex flex-col gap-2 rounded-2xl border border-transparent p-4 transition hover:border-indigo-200 dark:hover:border-indigo-500/40"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {toggle.label}
                    </p>
                    <p
                      id={`${toggle.id}-description`}
                      className="text-xs text-slate-500 dark:text-slate-400"
                    >
                      {toggle.description}
                    </p>
                  </div>
                  <input
                    id={toggle.id}
                    type="checkbox"
                    defaultChecked={toggle.defaultChecked}
                    className="h-5 w-10 cursor-pointer appearance-none rounded-full border border-slate-300 bg-slate-200 transition before:block before:h-4 before:w-4 before:translate-x-0 before:rounded-full before:bg-white before:shadow before:transition checked:border-indigo-400 checked:bg-indigo-500 checked:before:translate-x-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:checked:border-indigo-400 dark:checked:bg-indigo-500"
                    aria-describedby={`${toggle.id}-description`}
                  />
                </div>
              </label>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="gap-3 pb-0">
            <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
              <Shield className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>Safety guardrails</CardTitle>
            <CardDescription>
              Escalation allow-lists keep sensitive documents inside your tenant while the gateway
              perimeter enforces identity and TLS.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="gap-3 pb-0">
            <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
              <Zap className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>Performance tuning</CardTitle>
            <CardDescription>
              Adjust search probes, reranker policies, and streaming defaults to match your
              team&apos;s workflow.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    </div>
  );
}
