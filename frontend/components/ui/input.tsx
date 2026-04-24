import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-lg border border-border bg-white px-3 text-sm text-foreground shadow-sm outline-none transition",
        "placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10",
        className
      )}
      {...props}
    />
  )
);

Input.displayName = "Input";

