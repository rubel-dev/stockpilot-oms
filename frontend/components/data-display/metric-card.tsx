import { ArrowUpRight } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function MetricCard({
  label,
  value,
  helper
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <div className="rounded-full bg-slate-50 p-2 text-slate-500">
            <ArrowUpRight className="h-4 w-4" />
          </div>
        </div>
        <div>
          <p className="text-3xl font-semibold tracking-tight text-foreground">{value}</p>
          <p className="mt-1 text-sm text-muted">{helper}</p>
        </div>
      </CardContent>
    </Card>
  );
}

