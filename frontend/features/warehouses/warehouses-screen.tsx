"use client";

import type React from "react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { FormField } from "@/components/forms/form-field";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { apiRequest } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type Warehouse = {
  id: string;
  name: string;
  code: string;
  city?: string | null;
  country?: string | null;
  status: string;
  total_skus: number;
  total_units: number;
  low_stock_items: number;
};

type WarehousesResponse = { items: Warehouse[] };

export function WarehousesScreen() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form, setForm] = useState({ name: "", code: "", city: "", country: "" });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "50" });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    return params.toString();
  }, [search, status]);

  const { data, loading, error, refresh } = useApi<WarehousesResponse>(() => apiRequest(`/warehouses?${query}`), [query]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await apiRequest("/warehouses", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          city: form.city || null,
          country: form.country || null
        })
      });
      setDrawerOpen(false);
      setForm({ name: "", code: "", city: "", country: "" });
      await refresh();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not create warehouse.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Locations"
        title="Warehouses"
        description="Monitor storage sites, SKU density, and stock posture by fulfillment location."
        action={{ label: "New warehouse", onClick: () => setDrawerOpen(true) }}
      />

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-2">
          <Input placeholder="Search by warehouse name or code" value={search} onChange={(event) => setSearch(event.target.value)} />
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </CardContent>
      </Card>

      {loading ? (
        <Skeleton className="h-[420px] rounded-xl" />
      ) : error ? (
        <ErrorState title="Could not load warehouses" message={error} onRetry={refresh} />
      ) : !(data?.items.length ?? 0) ? (
        <EmptyState title="No warehouses yet" description="Create warehouse locations to start separating stock balances and transfer flows." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Warehouse</Th>
                    <Th>Location</Th>
                    <Th>SKUs</Th>
                    <Th>Units</Th>
                    <Th>Low stock</Th>
                    <Th>Status</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data?.items.map((item) => (
                    <tr key={item.id}>
                      <Td>
                        <Link href={`/warehouses/${item.id}`}>
                          <div className="font-medium text-foreground">{item.name}</div>
                          <div className="mt-1 text-xs text-muted">{item.code}</div>
                        </Link>
                      </Td>
                      <Td>{[item.city, item.country].filter(Boolean).join(", ") || "--"}</Td>
                      <Td>{formatNumber(item.total_skus)}</Td>
                      <Td>{formatNumber(item.total_units)}</Td>
                      <Td>{formatNumber(item.low_stock_items)}</Td>
                      <Td><Badge tone={item.status}>{item.status}</Badge></Td>
                    </tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} title="Create warehouse" description="Add a warehouse location for stock separation and fulfillment operations.">
        <form className="space-y-4" onSubmit={submit}>
          <FormField label="Warehouse name"><Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required /></FormField>
          <FormField label="Warehouse code"><Input value={form.code} onChange={(event) => setForm((current) => ({ ...current, code: event.target.value }))} required /></FormField>
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="City"><Input value={form.city} onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))} /></FormField>
            <FormField label="Country"><Input value={form.country} onChange={(event) => setForm((current) => ({ ...current, country: event.target.value }))} /></FormField>
          </div>
          {formError ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{formError}</p> : null}
          <div className="flex justify-end gap-3">
            <Button variant="secondary" type="button" onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button disabled={submitting} type="submit">{submitting ? "Creating..." : "Create warehouse"}</Button>
          </div>
        </form>
      </Drawer>
    </div>
  );
}
