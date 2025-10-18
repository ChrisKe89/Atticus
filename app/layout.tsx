import type { Metadata } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { Providers } from "@/app/providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "Atticus",
  description: "Grounded AI assistance for Sales teams with enterprise guardrails.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="flex min-h-screen flex-col bg-slate-50 font-sans text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <Providers>
          <SiteHeader />
          <main className="flex-1 overflow-hidden">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
