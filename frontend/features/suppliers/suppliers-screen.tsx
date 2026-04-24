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
import { useApi } from "@/lib/use-api";

type Supplier = {
  id: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  status: string;
  active_product_count: number;
  last_restock_at?: string | null;
};

export function SuppliersScreen() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form, setForm] = useState({ name: "", contact_name: "", email: "", phone: "", address: "", notes: "" });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "100" });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    return params.toString();
  }, [search, status]);

  const { data, loading, error, refresh } = useApi<{ items: Supplier[] }>(() => apiRequest(`/suppliers?${query}`), [query]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await apiRequest("/suppliers", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          contact_name: form.contact_name || null,
          email: form.email || null,
          phone: form.phone || null,
          address: form.address || null,
          notes: form.notes || null
        })
      });
      setDrawerOpen(false);
      setForm({ name: "", contact_name: "", email: "", phone: "", address: "", notes: "" });
      await refresh();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not create supplier.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Vendors"
        title="Suppliers"
        description="Manage vendor relationships, contact records, and product sourcing coverage."
        action={{ label: "New supplier", onClick: () => setDrawerOpen(true) }}
      />
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr,220px]">
          <Input placeholder="Search suppliers, contacts, or email" value={search} onChange={(event) => setSearch(event.target.value)} />
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </CardContent>
      </Card>
      {loading ? (
        <Skeleton className="h-[460px] rounded-xl" />
      ) : error ? (
        <ErrorState title="Could not load suppliers" message={error} onRetry={refresh} />
      ) : !(data?.items.length ?? 0) ? (
        <EmptyState title="No suppliers yet" description="Create supplier records to support purchase orders and reorder recommendations." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Supplier</Th>
                    <Th>Contact</Th>
                    <Th>Linked products</Th>
                    <Th>Last restock</Th>
                    <Th>Status</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data?.items.map((item) => (
                    <tr key={item.id}>
                      <Td>
                        <Link href={`/suppliers/${item.id}`}>
                          <div className="font-medium text-foreground">{item.name}</div>
                          <div className="mt-1 text-xs text-muted">{item.email ?? "No email"}</div>
                        </Link>
                      </Td>
                      <Td>{item.contact_name ?? item.phone ?? "--"}</Td>
                      <Td>{item.active_product_count}</Td>
                      <Td>{item.last_restock_at ? new Date(item.last_restock_at).toLocaleDateString() : "--"}</Td>
                      <Td><Badge tone={item.status}>{item.status}</Badge></Td>
                    </tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} title="Create supplier" description="Capture supplier details for sourcing, replenishment, and vendor communication.">
        <form className="space-y-4" onSubmit={submit}>
          <FormField label="Supplier name"><Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required /></FormField>
          <FormField label="Contact name"><Input value={form.contact_name} onChange={(event) => setForm((current) => ({ ...current, contact_name: event.target.value }))} /></FormField>
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="Email"><Input type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} /></FormField>
            <FormField label="Phone"><Input value={form.phone} onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))} /></FormField>
          </div>
          <FormField label="Address"><Input value={form.address} onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))} /></FormField>
          <FormField label="Notes"><Input value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} /></FormField>
          {formError ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{formError}</p> : null}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button disabled={submitting} type="submit">{submitting ? "Creating..." : "Create supplier"}</Button>
          </div>
        </form>
      </Drawer>
    </div>
  );
}
