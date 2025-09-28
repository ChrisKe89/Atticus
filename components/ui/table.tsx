import * as React from "react";
import { cn } from "@/lib/utils";

type TableProps = React.HTMLAttributes<HTMLTableElement>;
type TableSectionProps = React.HTMLAttributes<HTMLTableSectionElement>;
type TableRowProps = React.HTMLAttributes<HTMLTableRowElement>;
type TableHeadProps = React.ThHTMLAttributes<HTMLTableCellElement>;
type TableCellProps = React.TdHTMLAttributes<HTMLTableCellElement>;

export const Table = React.forwardRef<HTMLTableElement, TableProps>(function Table(
  { className, ...props },
  ref
) {
  return <table ref={ref} className={cn("w-full caption-bottom text-sm", className)} {...props} />;
});

export const TableHeader = React.forwardRef<HTMLTableSectionElement, TableSectionProps>(
  function TableHeader({ className, ...props }, ref) {
    return (
      <thead
        ref={ref}
        className={cn(
          "bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400",
          className
        )}
        {...props}
      />
    );
  }
);

export const TableBody = React.forwardRef<HTMLTableSectionElement, TableSectionProps>(
  function TableBody({ className, ...props }, ref) {
    return (
      <tbody
        ref={ref}
        className={cn("divide-y divide-slate-200 dark:divide-slate-800", className)}
        {...props}
      />
    );
  }
);

export const TableRow = React.forwardRef<HTMLTableRowElement, TableRowProps>(function TableRow(
  { className, ...props },
  ref
) {
  return (
    <tr
      ref={ref}
      className={cn("transition hover:bg-slate-50/50 dark:hover:bg-slate-900/40", className)}
      {...props}
    />
  );
});

export const TableHead = React.forwardRef<HTMLTableCellElement, TableHeadProps>(function TableHead(
  { className, ...props },
  ref
) {
  return (
    <th
      ref={ref}
      className={cn(
        "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300",
        className
      )}
      {...props}
    />
  );
});

export const TableCell = React.forwardRef<HTMLTableCellElement, TableCellProps>(function TableCell(
  { className, ...props },
  ref
) {
  return (
    <td
      ref={ref}
      className={cn("px-4 py-3 align-top text-sm text-slate-600 dark:text-slate-300", className)}
      {...props}
    />
  );
});
