"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { MetricCard } from "@/components/data-display/metric-card";
import { ChartCard } from "@/components/charts/chart-card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { apiRequest } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import { formatLabel } from "@/lib/utils";

type Metric = { key: string; value: number };
type WarehouseRow = { warehouse_id: string; warehouse_name: string; warehouse_code: string; total_available: number };
type AlertSummary = { items: Array<{ alert_type: string; severity: string; status: string; count: number }> };
type Movements = {
  items: Array<{
    id: string;
    product_name: string;
    warehouse_name: string;
    movement_type: string;
    quantity: number;
    created_at: string;
  }>;
};

export function DashboardScreen() {
  const metrics = useApi<{ items: Metric[] }>(() => apiRequest("/analytics/overview"), []);
  const warehouses = useApi<{ items: WarehouseRow[] }>(() => apiRequest("/analytics/stock-by-warehouse"), []);
  const alerts = useApi<AlertSummary>(() => apiRequest("/alerts/summary"), []);
  const movements = useApi<Movements>(() => apiRequest("/inventory/movements?page_size=6"), []);

  const loading = metrics.loading || warehouses.loading || alerts.loading || movements.loading;
  const error = metrics.error || warehouses.error || alerts.error || movements.error;

  const metricMap = new Map(metrics.data?.items.map((item) => [item.key, item.value]) ?? []);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="Dashboard"
        description="Monitor stock posture, open work, alerts, and warehouse performance from a single operational surface."
      />

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-36 rounded-xl" />
          ))}
        </div>
      ) : error ? (
        <ErrorState title="Dashboard unavailable" message={error} />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Products" value={formatNumber(metricMap.get("total_products") ?? 0)} helper="Catalog items currently tracked" />
            <MetricCard label="Units on hand" value={formatNumber(metricMap.get("total_units") ?? 0)} helper="Aggregate inventory across warehouses" />
            <MetricCard label="Low stock items" value={formatNumber(metricMap.get("low_stock_count") ?? 0)} helper="Products at or below reorder point" />
            <MetricCard label="Pending alerts" value={formatNumber(metricMap.get("pending_alerts") ?? 0)} helper="Open operational notifications" />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.4fr,1fr]">
            <ChartCard
              title="Available stock by warehouse"
              description="Current available inventory by warehouse location."
              data={(warehouses.data?.items ?? []).map((item) => ({
                name: item.warehouse_code,
                available: item.total_available
              }))}
              xKey="name"
              yKey="available"
              type="bar"
            />
            <Card>
              <CardHeader>
                <h3 className="text-base font-semibold text-foreground">Alert mix</h3>
                <p className="mt-1 text-sm text-muted">Severity and type distribution across open and resolved alerts.</p>
              </CardHeader>
              <CardContent className="space-y-3">
                {(alerts.data?.items ?? []).length ? (
                  alerts.data?.items.map((item) => (
                    <div key={`${item.alert_type}-${item.severity}-${item.status}`} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">{formatLabel(item.alert_type)}</p>
                        <p className="mt-1 text-xs text-muted">Status: {item.status}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge tone={item.severity}>{item.severity}</Badge>
                        <span className="text-sm font-semibold text-foreground">{item.count}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No alerts yet" description="This workspace has not generated any alert activity." />
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <h3 className="text-base font-semibold text-foreground">Recent inventory movements</h3>
              <p className="mt-1 text-sm text-muted">Latest stock changes across warehouses and order workflows.</p>
            </CardHeader>
            <CardContent className="p-0">
              {(movements.data?.items ?? []).length ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHead>
                      <tr>
                        <Th>Product</Th>
                        <Th>Warehouse</Th>
                        <Th>Movement</Th>
                        <Th>Quantity</Th>
                        <Th>Timestamp</Th>
                      </tr>
                    </TableHead>
                    <TableBody>
                      {movements.data?.items.map((item) => (
                        <tr key={item.id}>
                          <Td className="font-medium text-foreground">{item.product_name}</Td>
                          <Td>{item.warehouse_name}</Td>
                          <Td>
                            <Badge tone={item.movement_type}>{formatLabel(item.movement_type)}</Badge>
                          </Td>
                          <Td>{formatNumber(item.quantity)}</Td>
                          <Td>{new Date(item.created_at).toLocaleString()}</Td>
                        </tr>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="p-5">
                  <EmptyState title="No movement history" description="Stock changes will appear here once inventory activity begins." />
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
