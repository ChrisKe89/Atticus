import type { Metadata } from "next";
import { MailCheck } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export const metadata: Metadata = {
  title: "Contact · Atticus",
};

export default function ContactPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-10">
      <PageHeader
        eyebrow="Escalations"
        title="Raise an escalation"
        description="Submit production issues or low-confidence answers and the Atticus team will receive the full trace payload."
      />

      <form className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" name="name" placeholder="Alex Finnegan" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" name="email" type="email" placeholder="alex@contoso.com" required />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="summary">Issue summary</Label>
          <Input
            id="summary"
            name="summary"
            placeholder="Low confidence response for Managed Print RFP"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="details">Details</Label>
          <Textarea
            id="details"
            name="details"
            rows={5}
            placeholder="Share the question, customer, and any attachments that should be included in the follow-up."
            required
          />
        </div>
        <Button type="submit" className="inline-flex items-center gap-2 rounded-full px-5 py-2.5">
          Submit escalation
          <MailCheck className="h-4 w-4" aria-hidden="true" />
        </Button>
      </form>
    </div>
  );
}
