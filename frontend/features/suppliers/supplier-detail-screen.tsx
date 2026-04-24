"use client";

import type React from "react";
import { useApi } from "@/lib/use-api";
import { apiRequest, apiDelete } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { FormField } from "@/components/forms/form-field";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useState } from "react";

type SupplierDetail = {
  id: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  status: string;
  notes?: string | null;
  linked_products: Array<{
    id: string;
    product_id: string;
    product_name: string;
    product_sku: string;
    supplier_sku?: string | null;
    minimum_order_quantity: number;
    unit_cost?: number | null;
    is_preferred: boolean;
  }>;
};

export function SupplierDetailScreen({ id }: { id: string }) {
  const detail = useApi<SupplierDetail>(() => apiRequest(`/suppliers/${id}`), [id]);
  const products = useApi<{ items: Array<{ id: string; name: string; sku: string }> }>(() => apiRequest("/products?page_size=100"), []);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form, setForm] = useState({ product_id: "", supplier_sku: "", minimum_order_quantity: "0", unit_cost: "0" });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (detail.loading) return <Skeleton className="h-[520px] rounded-xl" />;
  if (detail.error || !detail.data) return <ErrorState title="Supplier unavailable" message={detail.error ?? "Supplier not found."} />;

  const linkProduct = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await apiRequest(`/suppliers/${id}/products`, {
        method: "POST",
        body: JSON.stringify({
          product_id: form.product_id,
          supplier_sku: form.supplier_sku || null,
          minimum_order_quantity: Number(form.minimum_order_quantity),
          unit_cost: Number(form.unit_cost),
          is_preferred: true
        })
      });
      setDrawerOpen(false);
      await detail.refresh();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not link product.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Vendors" title={detail.data.name} description={detail.data.notes ?? "Supplier profile, sourcing coverage, and purchase support details."} action={{ label: "Link product", onClick: () => setDrawerOpen(true) }} />
      <div className="grid gap-6 xl:grid-cols-[0.9fr,1.1fr]">
        <Card>
          <CardHeader><h3 className="text-base font-semibold text-foreground">Supplier profile</h3></CardHeader>
          <CardContent className="space-y-4">
            <Field label="Contact" value={detail.data.contact_name ?? "—"} />
            <Field label="Email" value={detail.data.email ?? "—"} />
            <Field label="Phone" value={detail.data.phone ?? "—"} />
            <Field label="Address" value={detail.data.address ?? "—"} />
            <div className="space-y-2">
              <p className="text-sm text-muted">Status</p>
              <Badge tone={detail.data.status}>{detail.data.status}</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><h3 className="text-base font-semibold text-foreground">Linked products</h3></CardHeader>
          <CardContent className="space-y-3">
            {detail.data.linked_products.length ? (
              detail.data.linked_products.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{item.product_name}</p>
                    <p className="mt-1 text-xs text-muted">{item.product_sku} · MOQ {item.minimum_order_quantity}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {item.is_preferred ? <Badge tone="active">preferred</Badge> : null}
                    <Button
                      variant="ghost"
                      onClick={async () => {
                        await apiDelete(`/suppliers/${id}/products/${item.product_id}`);
                        await detail.refresh();
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState title="No linked products" description="Link catalog items to this supplier to support purchase order validation and replenishment workflows." />
            )}
          </CardContent>
        </Card>
      </div>
      <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} title="Link product" description="Associate a catalog item with this supplier for sourcing and purchase orders.">
        <form className="space-y-4" onSubmit={linkProduct}>
          <FormField label="Product">
            <Select value={form.product_id} onChange={(event) => setForm((current) => ({ ...current, product_id: event.target.value }))} required>
              <option value="">Select product</option>
              {products.data?.items.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.sku})</option>)}
            </Select>
          </FormField>
          <FormField label="Supplier SKU"><Input value={form.supplier_sku} onChange={(event) => setForm((current) => ({ ...current, supplier_sku: event.target.value }))} /></FormField>
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="Minimum order quantity"><Input type="number" min="0" value={form.minimum_order_quantity} onChange={(event) => setForm((current) => ({ ...current, minimum_order_quantity: event.target.value }))} /></FormField>
            <FormField label="Unit cost"><Input type="number" min="0" step="0.01" value={form.unit_cost} onChange={(event) => setForm((current) => ({ ...current, unit_cost: event.target.value }))} /></FormField>
          </div>
          {formError ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{formError}</p> : null}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button disabled={submitting} type="submit">{submitting ? "Linking..." : "Link product"}</Button>
          </div>
        </form>
      </Drawer>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/50 px-4 py-3">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}
