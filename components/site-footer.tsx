export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white/70 dark:border-slate-800 dark:bg-slate-950/70">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>&copy; {new Date().getFullYear()} Atticus. All rights reserved.</p>
        <div className="flex flex-wrap items-center gap-3" aria-hidden="true" />
      </div>
    </footer>
  );
}
