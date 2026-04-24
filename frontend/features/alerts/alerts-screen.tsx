"use client";

import { useApi } from "@/lib/use-api";
import { apiRequest } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatLabel } from "@/lib/utils";

type AlertItem = {
  id: string;
  alert_type: string;
  severity: string;
  status: string;
  title: string;
  message: string;
  created_at: string;
};

export function AlertsScreen() {
  const alerts = useApi<{ items: AlertItem[] }>(() => apiRequest("/alerts?page_size=100"), []);
  const summary = useApi<{ items: Array<{ alert_type: string; severity: string; status: string; count: number }> }>(() => apiRequest("/alerts/summary"), []);

  const runAction = async (id: string, action: "resolve" | "dismiss") => {
    await apiRequest(`/alerts/${id}/${action}`, { method: "POST" });
    await alerts.refresh();
    await summary.refresh();
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Signals" title="Alerts" description="Track low-stock pressure, stuck workflows, and operational exceptions." action={{ label: "Recalculate alerts", onClick: async () => { await apiRequest("/alerts/recalculate", { method: "POST" }); await alerts.refresh(); await summary.refresh(); } }} />

      <div className="grid gap-4 md:grid-cols-3">
        {(summary.data?.items ?? []).slice(0, 3).map((item) => (
          <Card key={`${item.alert_type}-${item.status}-${item.severity}`}>
            <CardContent className="space-y-2 p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted">{formatLabel(item.alert_type)}</p>
                <Badge tone={item.severity}>{item.severity}</Badge>
              </div>
              <p className="text-3xl font-semibold text-foreground">{item.count}</p>
              <p className="text-xs text-muted">Status: {item.status}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {alerts.loading ? (
        <Skeleton className="h-[460px] rounded-xl" />
      ) : alerts.error ? (
        <ErrorState title="Could not load alerts" message={alerts.error} onRetry={alerts.refresh} />
      ) : !(alerts.data?.items.length ?? 0) ? (
        <EmptyState title="No alerts" description="This workspace does not currently have active operational alerts." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Alert</Th>
                    <Th>Type</Th>
                    <Th>Severity</Th>
                    <Th>Status</Th>
                    <Th>Created</Th>
                    <Th>Actions</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {alerts.data?.items.map((item) => (
                    <tr key={item.id}>
                      <Td>
                        <div className="font-medium text-foreground">{item.title}</div>
                        <div className="mt-1 text-xs text-muted">{item.message}</div>
                      </Td>
                      <Td><Badge tone={item.alert_type}>{formatLabel(item.alert_type)}</Badge></Td>
                      <Td><Badge tone={item.severity}>{item.severity}</Badge></Td>
                      <Td><Badge tone={item.status}>{item.status}</Badge></Td>
                      <Td>{new Date(item.created_at).toLocaleDateString()}</Td>
                      <Td>
                        <div className="flex gap-2">
                          <Button variant="secondary" onClick={() => runAction(item.id, "resolve")}>Resolve</Button>
                          <Button variant="ghost" onClick={() => runAction(item.id, "dismiss")}>Dismiss</Button>
                        </div>
                      </Td>
                    </tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
