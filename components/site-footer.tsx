import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white/70 dark:border-slate-800 dark:bg-slate-950/70">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>&copy; {new Date().getFullYear()} Atticus. All rights reserved.</p>
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/contact" className="hover:text-indigo-500">
            Escalations
          </Link>
          <Link href="/apps" className="hover:text-indigo-500">
            Integrations
          </Link>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            className="hover:text-indigo-500"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
