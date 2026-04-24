"use client";

import { useApi } from "@/lib/use-api";
import { apiRequest } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/format";
import { formatLabel } from "@/lib/utils";

type ProductDetail = {
  id: string;
  name: string;
  sku: string;
  description?: string | null;
  unit: string;
  reorder_point: number;
  reorder_quantity: number;
  status: string;
  total_on_hand: number;
  total_reserved: number;
  total_available: number;
  warehouse_count: number;
  category_name?: string | null;
};

type MovementResponse = {
  items: Array<{
    id: string;
    movement_type: string;
    quantity: number;
    warehouse_name: string;
    created_at: string;
  }>;
};

export function ProductDetailScreen({ id }: { id: string }) {
  const detail = useApi<ProductDetail>(() => apiRequest(`/products/${id}`), [id]);
  const movements = useApi<MovementResponse>(() => apiRequest(`/inventory/movements?product_id=${id}&page_size=6`), [id]);

  if (detail.loading) return <Skeleton className="h-[520px] rounded-xl" />;
  if (detail.error || !detail.data) return <ErrorState title="Product unavailable" message={detail.error ?? "Product not found."} />;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Catalog"
        title={detail.data.name}
        description={detail.data.description ?? "Operational product record with warehouse-wide stock posture."}
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold text-foreground">Product summary</h3>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <Info label="SKU" value={detail.data.sku} />
            <Info label="Category" value={detail.data.category_name ?? "Unassigned"} />
            <Info label="Unit" value={detail.data.unit} />
            <div className="space-y-2">
              <p className="text-sm text-muted">Status</p>
              <Badge tone={detail.data.status}>{detail.data.status}</Badge>
            </div>
            <Info label="Reorder point" value={formatNumber(detail.data.reorder_point)} />
            <Info label="Reorder quantity" value={formatNumber(detail.data.reorder_quantity)} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold text-foreground">Stock posture</h3>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Info label="On hand" value={formatNumber(detail.data.total_on_hand)} />
            <Info label="Reserved" value={formatNumber(detail.data.total_reserved)} />
            <Info label="Available" value={formatNumber(detail.data.total_available)} />
            <Info label="Warehouses" value={formatNumber(detail.data.warehouse_count)} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="text-base font-semibold text-foreground">Recent movements</h3>
          <p className="mt-1 text-sm text-muted">Latest stock changes that touched this product.</p>
        </CardHeader>
        <CardContent>
          {movements.loading ? (
            <Skeleton className="h-48 rounded-xl" />
          ) : movements.error ? (
            <ErrorState title="Could not load movements" message={movements.error} />
          ) : !(movements.data?.items.length ?? 0) ? (
            <EmptyState title="No movement history" description="Movement events will appear once stock is received, adjusted, transferred, or shipped." />
          ) : (
            <div className="space-y-3">
              {movements.data?.items.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{item.warehouse_name}</p>
                    <p className="mt-1 text-xs text-muted">{new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge tone={item.movement_type}>{formatLabel(item.movement_type)}</Badge>
                    <span className="text-sm font-semibold text-foreground">{formatNumber(item.quantity)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/50 px-4 py-3">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}
