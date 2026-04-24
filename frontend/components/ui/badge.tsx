import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700",
  archived: "bg-slate-100 text-slate-700",
  draft: "bg-slate-100 text-slate-700",
  confirmed: "bg-blue-50 text-blue-700",
  processing: "bg-violet-50 text-violet-700",
  shipped: "bg-cyan-50 text-cyan-700",
  completed: "bg-emerald-50 text-emerald-700",
  cancelled: "bg-rose-50 text-rose-700",
  open: "bg-amber-50 text-amber-700",
  resolved: "bg-emerald-50 text-emerald-700",
  dismissed: "bg-slate-100 text-slate-700",
  critical: "bg-rose-50 text-rose-700",
  warning: "bg-amber-50 text-amber-700",
  info: "bg-blue-50 text-blue-700",
  sales: "bg-blue-50 text-blue-700",
  purchase: "bg-emerald-50 text-emerald-700",
  low_stock: "bg-amber-50 text-amber-700",
  reorder_suggestion: "bg-blue-50 text-blue-700",
  stale_order: "bg-amber-50 text-amber-700",
  stuck_processing: "bg-rose-50 text-rose-700",
  stock_in: "bg-emerald-50 text-emerald-700",
  stock_out: "bg-rose-50 text-rose-700",
  transfer_out: "bg-amber-50 text-amber-700",
  transfer_in: "bg-blue-50 text-blue-700",
  adjustment: "bg-slate-100 text-slate-700",
  reservation: "bg-violet-50 text-violet-700",
  reservation_release: "bg-cyan-50 text-cyan-700",
  order_deduction: "bg-rose-50 text-rose-700"
};

export function Badge({ children, tone, className }: { children: string; tone?: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize",
        tone ? styles[tone] ?? "bg-slate-100 text-slate-700" : "bg-slate-100 text-slate-700",
        className
      )}
    >
      {children}
    </span>
  );
}
