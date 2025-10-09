"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";
import { Menu, X } from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import type { Role } from "@prisma/client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NavLink = {
  href: string;
  label: string;
  roles?: readonly Role[];
};

const links: readonly NavLink[] = [
  { href: "/", label: "Chat" },
  { href: "/admin", label: "Admin", roles: ["ADMIN"] as readonly Role[] },
  { href: "/settings", label: "Settings" },
  { href: "/contact", label: "Contact" },
  { href: "/apps", label: "Apps" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const { data: session, status } = useSession();

  const role = useMemo(() => {
    const userWithRole = session?.user as { role?: Role } | undefined;
    return userWithRole?.role ?? null;
  }, [session?.user]);

  const visibleLinks = useMemo(() => {
    return links.filter((link) => {
      if (link.href === "/settings" && status !== "authenticated") {
        return false;
      }
      if (!role) {
        return !link.roles;
      }
      return !link.roles || link.roles.includes(role);
    });
  }, [role, status]);

  const activeHref = useMemo(() => {
    if (!pathname) {
      return "/";
    }
    return (
      visibleLinks.find((link) => pathname === link.href || pathname.startsWith(`${link.href}/`))?.href ?? "/"
    );
  }, [pathname, visibleLinks]);

  const isAuthenticated = status === "authenticated";
  const userLabel = session?.user?.email ?? session?.user?.name ?? "Account";

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur dark:border-slate-800/80 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between p-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-base font-semibold">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-white shadow-sm">
            A
          </span>
          <span className="hidden sm:inline">Atticus</span>
        </Link>
        <nav
          aria-label="Primary"
          className="hidden items-center gap-1 rounded-full border border-slate-200 bg-white/60 p-1 text-sm font-medium dark:border-slate-800 dark:bg-slate-900/60 sm:flex"
        >
          {visibleLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-3 py-1.5 transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-500/10",
                activeHref === link.href
                  ? "bg-indigo-600 text-white shadow-sm hover:bg-indigo-600"
                  : "text-slate-600 dark:text-slate-300"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="hidden rounded-full sm:inline-flex"
              onClick={() => signOut({ callbackUrl: "/" })}
            >
              Sign out
            </Button>
          ) : (
            <Button
              asChild
              variant="secondary"
              size="sm"
              className="hidden rounded-full sm:inline-flex"
            >
              <Link href="/signin">Sign in</Link>
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="sm:hidden"
            onClick={() => setIsOpen((prev) => !prev)}
            aria-expanded={isOpen}
            aria-controls="mobile-nav"
          >
            {isOpen ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
            <span className="sr-only">Toggle navigation</span>
          </Button>
        </div>
      </div>
      <div
        id="mobile-nav"
        className={cn(
          "border-t border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950 sm:hidden",
          isOpen ? "block" : "hidden"
        )}
      >
        <div className="flex flex-col gap-3">
          <nav className="flex flex-col gap-2 text-base font-medium">
            {visibleLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-xl px-3 py-2 hover:bg-indigo-50 dark:hover:bg-indigo-500/10",
                  activeHref === link.href
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-700 dark:text-slate-300"
                )}
                onClick={() => setIsOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="border-t border-slate-200 pt-3 text-sm dark:border-slate-800">
            {isAuthenticated ? (
              <Button
                type="button"
                className="w-full"
                onClick={() => {
                  setIsOpen(false);
                  signOut({ callbackUrl: "/" });
                }}
              >
                Sign out ({userLabel})
              </Button>
            ) : (
              <Button asChild className="w-full" onClick={() => setIsOpen(false)}>
                <Link href="/signin">Sign in</Link>
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
