import type React from "react";

import { cn } from "@/lib/utils";

export function FormField({
  label,
  hint,
  error,
  children,
  className
}: React.PropsWithChildren<{ label: string; hint?: string; error?: string; className?: string }>) {
  return (
    <label className={cn("grid gap-2", className)}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        {hint ? <span className="text-xs text-slate-400">{hint}</span> : null}
      </div>
      {children}
      {error ? <span className="text-xs text-danger">{error}</span> : null}
    </label>
  );
}
