export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gradient-to-br from-background via-background to-secondary/40 px-6 py-12">
      <div className="flex max-w-2xl flex-col items-center gap-4 rounded-lg border bg-card/80 p-8 text-center shadow-sm backdrop-blur">
        <span className="inline-flex items-center rounded-full bg-primary/15 px-4 py-1 text-sm font-medium text-primary">
          Wynstan setup complete
        </span>
        <h1 className="text-4xl font-semibold text-foreground sm:text-5xl">
          GC Root-Cause Chat baseline ready
        </h1>
        <p className="text-base text-muted-foreground sm:text-lg">
          Tailwind CSS utilities are active. This placeholder screen will be replaced in Stage 1 with the diagnostic workspace
          layout.
        </p>
      </div>
      <div className="flex items-center gap-3 rounded-lg border border-dashed bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden />
        Dev server: run <code className="rounded bg-background px-2 py-1 font-mono text-xs">pnpm dev</code> and open
        <span className="font-medium text-foreground">http://localhost:3000</span>
      </div>
    </main>
  );
}
