import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-[120px] w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-foreground shadow-sm outline-none transition",
        "placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10",
        className
      )}
      {...props}
    />
  )
);

Textarea.displayName = "Textarea";

