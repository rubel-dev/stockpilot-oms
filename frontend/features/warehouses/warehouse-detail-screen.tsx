"use client";

import { useApi } from "@/lib/use-api";
import { apiRequest } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/data-display/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/format";

type WarehouseDetail = {
  id: string;
  name: string;
  code: string;
  city?: string | null;
  country?: string | null;
  status: string;
  total_skus: number;
  total_units: number;
  total_reserved: number;
  low_stock_items: number;
};

export function WarehouseDetailScreen({ id }: { id: string }) {
  const { data, loading, error } = useApi<WarehouseDetail>(() => apiRequest(`/warehouses/${id}`), [id]);

  if (loading) return <Skeleton className="h-[420px] rounded-xl" />;
  if (error || !data) return <ErrorState title="Warehouse unavailable" message={error ?? "Warehouse not found."} />;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Locations"
        title={data.name}
        description={`Operational view for ${data.code}${data.city ? ` in ${data.city}` : ""}.`}
      />
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="SKU count" value={formatNumber(data.total_skus)} />
        <Metric label="Units on hand" value={formatNumber(data.total_units)} />
        <Metric label="Reserved units" value={formatNumber(data.total_reserved)} />
        <Metric label="Low-stock items" value={formatNumber(data.low_stock_items)} />
      </div>
      <Card>
        <CardHeader>
          <h3 className="text-base font-semibold text-foreground">Warehouse profile</h3>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <ProfileField label="Code" value={data.code} />
          <ProfileField label="Location" value={[data.city, data.country].filter(Boolean).join(", ") || "—"} />
          <div className="space-y-2">
            <p className="text-sm text-muted">Status</p>
            <Badge tone={data.status}>{data.status}</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="space-y-1 p-5">
        <p className="text-sm text-muted">{label}</p>
        <p className="text-2xl font-semibold text-foreground">{value}</p>
      </CardContent>
    </Card>
  );
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/50 px-4 py-3">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}

