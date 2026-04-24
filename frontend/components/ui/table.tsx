import type React from "react";

import { cn } from "@/lib/utils";

export function Table({ children }: React.PropsWithChildren) {
  return <table className="min-w-full divide-y divide-slate-100">{children}</table>;
}

export function TableHead({ children }: React.PropsWithChildren) {
  return <thead className="sticky top-0 z-10 bg-slate-50/90 backdrop-blur">{children}</thead>;
}

export function TableBody({ children }: React.PropsWithChildren) {
  return <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>;
}

export function Th({ children, className }: React.PropsWithChildren<{ className?: string }>) {
  return <th className={cn("px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500", className)}>{children}</th>;
}

export function Td({ children, className }: React.PropsWithChildren<{ className?: string }>) {
  return <td className={cn("px-5 py-4 text-sm text-slate-700", className)}>{children}</td>;
}
