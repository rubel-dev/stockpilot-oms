import { Box, SearchX } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function EmptyState({
  title,
  description,
  icon = "box"
}: {
  title: string;
  description: string;
  icon?: "box" | "search";
}) {
  const Icon = icon === "search" ? SearchX : Box;
  return (
    <Card>
      <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-3 text-center">
        <div className="rounded-full bg-slate-100 p-3 text-slate-500">
          <Icon className="h-5 w-5" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          <p className="max-w-md text-sm text-muted">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}

