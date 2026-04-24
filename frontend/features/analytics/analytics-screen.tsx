"use client";

import { ChartCard } from "@/components/charts/chart-card";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { MetricCard } from "@/components/data-display/metric-card";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { apiRequest } from "@/lib/api";
import { formatCurrency, formatMonth, formatNumber } from "@/lib/format";
import { useApi } from "@/lib/use-api";

export function AnalyticsScreen() {
  const overview = useApi<{ items: Array<{ key: string; value: number }> }>(() => apiRequest("/analytics/overview"), []);
  const stockByWarehouse = useApi<{ items: Array<{ warehouse_name: string; warehouse_code: string; total_available: number }> }>(() => apiRequest("/analytics/stock-by-warehouse"), []);
  const monthlyOrders = useApi<{ items: Array<{ month_bucket: string; gross_amount: number }> }>(() => apiRequest("/analytics/monthly-orders"), []);
  const topMoving = useApi<{ items: Array<{ product_name: string; product_sku: string; total_moved: number }> }>(() => apiRequest("/analytics/top-moving-products?limit=8"), []);
  const supplierRestocks = useApi<{ items: Array<{ supplier_name: string; purchase_order_count: number; total_units_ordered: number; total_spend: number }> }>(() => apiRequest("/analytics/supplier-restocks"), []);

  const loading = overview.loading || stockByWarehouse.loading || monthlyOrders.loading || topMoving.loading || supplierRestocks.loading;
  const error = overview.error || stockByWarehouse.error || monthlyOrders.error || topMoving.error || supplierRestocks.error;

  if (loading) return <Skeleton className="h-[680px] rounded-xl" />;
  if (error) return <ErrorState title="Analytics unavailable" message={error} />;

  const metricMap = new Map(overview.data?.items.map((item) => [item.key, item.value]) ?? []);

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Insights" title="Analytics" description="Operational analytics across stock posture, movement velocity, and supplier performance." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Open sales orders" value={formatNumber(metricMap.get("open_sales_orders") ?? 0)} helper="Orders waiting for shipment or processing" />
        <MetricCard label="Open purchase orders" value={formatNumber(metricMap.get("open_purchase_orders") ?? 0)} helper="Inbound restocks still in flight" />
        <MetricCard label="Tracked units" value={formatNumber(metricMap.get("total_units") ?? 0)} helper="Aggregate on-hand stock across all warehouses" />
        <MetricCard label="Pending alerts" value={formatNumber(metricMap.get("pending_alerts") ?? 0)} helper="Operational issues requiring review" />
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <ChartCard
          title="Available stock by warehouse"
          description="Inventory availability by location."
          data={(stockByWarehouse.data?.items ?? []).map((item) => ({ warehouse: item.warehouse_code, units: item.total_available }))}
          xKey="warehouse"
          yKey="units"
          type="bar"
        />
        <ChartCard
          title="Monthly order volume"
          description="Gross order value by month bucket."
          data={(monthlyOrders.data?.items ?? []).map((item) => ({ month: formatMonth(item.month_bucket), gross: item.gross_amount }))}
          xKey="month"
          yKey="gross"
          type="line"
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><h3 className="text-base font-semibold text-foreground">Top moving products</h3></CardHeader>
          <CardContent>
            {(topMoving.data?.items.length ?? 0) ? (
              <div className="space-y-3">
                {topMoving.data?.items.map((item) => (
                  <div key={item.product_sku} className="flex items-center justify-between rounded-lg border border-slate-100 px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.product_name}</p>
                      <p className="mt-1 text-xs text-muted">{item.product_sku}</p>
                    </div>
                    <p className="text-sm font-semibold text-foreground">{formatNumber(item.total_moved)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No movement data" description="Movement analytics will appear once inventory operations are recorded." />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><h3 className="text-base font-semibold text-foreground">Supplier restock summary</h3></CardHeader>
          <CardContent className="p-0">
            {(supplierRestocks.data?.items.length ?? 0) ? (
              <div className="overflow-x-auto">
                <Table>
                  <TableHead>
                    <tr>
                      <Th>Supplier</Th>
                      <Th>POs</Th>
                      <Th>Units</Th>
                      <Th>Spend</Th>
                    </tr>
                  </TableHead>
                  <TableBody>
                    {supplierRestocks.data?.items.map((item) => (
                      <tr key={item.supplier_name}>
                        <Td className="font-medium text-foreground">{item.supplier_name}</Td>
                        <Td>{formatNumber(item.purchase_order_count)}</Td>
                        <Td>{formatNumber(item.total_units_ordered)}</Td>
                        <Td>{formatCurrency(item.total_spend)}</Td>
                      </tr>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="p-5">
                <EmptyState title="No supplier restock data" description="Completed and active purchase order metrics will appear here once restocks are processed." />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

