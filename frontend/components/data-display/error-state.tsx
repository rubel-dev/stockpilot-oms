import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ErrorState({ title, message, onRetry }: { title: string; message: string; onRetry?: () => void }) {
  return (
    <Card>
      <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-4 text-center">
        <div className="rounded-full bg-rose-50 p-3 text-rose-600">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          <p className="max-w-md text-sm text-muted">{message}</p>
        </div>
        {onRetry ? <Button variant="secondary" onClick={onRetry}>Try again</Button> : null}
      </CardContent>
    </Card>
  );
}

