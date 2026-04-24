"use client";

import type React from "react";
import { useMemo, useState } from "react";

import { FormField } from "@/components/forms/form-field";
import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
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

type Balance = {
  product_id: string;
  product_name: string;
  product_sku: string;
  warehouse_id: string;
  warehouse_name: string;
  warehouse_code: string;
  reorder_point: number;
  on_hand_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
};

type BalanceResponse = { items: Balance[] };
type ProductResponse = { items: Array<{ id: string; name: string; sku: string }> };
type WarehouseResponse = { items: Array<{ id: string; name: string; code: string }> };

export function InventoryScreen() {
  const [search, setSearch] = useState("");
  const [drawerMode, setDrawerMode] = useState<"stock-in" | "stock-out" | "transfer" | "adjustment" | null>(null);
  const [form, setForm] = useState({
    product_id: "",
    warehouse_id: "",
    destination_warehouse_id: "",
    quantity: "0",
    counted_quantity: "0",
    reason: "",
    notes: ""
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "100" });
    if (search) params.set("search", search);
    return params.toString();
  }, [search]);

  const balances = useApi<BalanceResponse>(() => apiRequest(`/inventory?${query}`), [query]);
  const products = useApi<ProductResponse>(() => apiRequest("/products?page_size=100"), []);
  const warehouses = useApi<WarehouseResponse>(() => apiRequest("/warehouses?page_size=100"), []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!drawerMode) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const pathMap = {
        "stock-in": "/inventory/movements/stock-in",
        "stock-out": "/inventory/movements/stock-out",
        transfer: "/inventory/movements/transfer",
        adjustment: "/inventory/movements/adjustment"
      } as const;

      const body =
        drawerMode === "transfer"
          ? {
              product_id: form.product_id,
              source_warehouse_id: form.warehouse_id,
              destination_warehouse_id: form.destination_warehouse_id,
              quantity: Number(form.quantity),
              reason: form.reason,
              notes: form.notes || null
            }
          : drawerMode === "adjustment"
            ? {
                product_id: form.product_id,
                warehouse_id: form.warehouse_id,
                counted_quantity: Number(form.counted_quantity),
                reason: form.reason,
                notes: form.notes || null
              }
            : {
                product_id: form.product_id,
                warehouse_id: form.warehouse_id,
                quantity: Number(form.quantity),
                reason: form.reason,
                notes: form.notes || null,
                reference_type: "manual"
              };

      await apiRequest(pathMap[drawerMode], { method: "POST", body: JSON.stringify(body) });
      setDrawerMode(null);
      setForm({
        product_id: "",
        warehouse_id: "",
        destination_warehouse_id: "",
        quantity: "0",
        counted_quantity: "0",
        reason: "",
        notes: ""
      });
      await balances.refresh();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Inventory operation failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Inventory"
        title="Inventory balances"
        description="Monitor on-hand, reserved, and available stock with quick operational actions."
      />

      <Card>
        <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center lg:justify-between">
          <Input className="max-w-xl" placeholder="Search by product, SKU, or warehouse" value={search} onChange={(event) => setSearch(event.target.value)} />
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => setDrawerMode("stock-in")}>Stock in</Button>
            <Button variant="secondary" onClick={() => setDrawerMode("stock-out")}>Stock out</Button>
            <Button variant="secondary" onClick={() => setDrawerMode("transfer")}>Transfer</Button>
            <Button onClick={() => setDrawerMode("adjustment")}>Adjustment</Button>
          </div>
        </CardContent>
      </Card>

      {balances.loading ? (
        <Skeleton className="h-[480px] rounded-xl" />
      ) : balances.error ? (
        <ErrorState title="Could not load inventory balances" message={balances.error} onRetry={balances.refresh} />
      ) : !(balances.data?.items.length ?? 0) ? (
        <EmptyState title="No inventory balances yet" description="Balances will appear after products receive stock in at least one warehouse." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Product</Th>
                    <Th>Warehouse</Th>
                    <Th>On hand</Th>
                    <Th>Reserved</Th>
                    <Th>Available</Th>
                    <Th>Reorder point</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {balances.data?.items.map((item) => (
                    <tr key={`${item.product_id}-${item.warehouse_id}`}>
                      <Td>
                        <div className="font-medium text-foreground">{item.product_name}</div>
                        <div className="mt-1 text-xs text-muted">{item.product_sku}</div>
                      </Td>
                      <Td>
                        <div className="font-medium text-foreground">{item.warehouse_name}</div>
                        <div className="mt-1 text-xs text-muted">{item.warehouse_code}</div>
                      </Td>
                      <Td>{formatNumber(item.on_hand_quantity)}</Td>
                      <Td>{formatNumber(item.reserved_quantity)}</Td>
                      <Td className="font-medium text-foreground">{formatNumber(item.available_quantity)}</Td>
                      <Td>{formatNumber(item.reorder_point)}</Td>
                    </tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      <Drawer
        open={Boolean(drawerMode)}
        onOpenChange={(open) => !open && setDrawerMode(null)}
        title={drawerMode ? drawerMode.replace("-", " ") : "Movement"}
        description="Record operational stock changes directly against warehouse balances."
      >
        <form className="space-y-4" onSubmit={submit}>
          <FormField label="Product">
            <Select value={form.product_id} onChange={(event) => setForm((current) => ({ ...current, product_id: event.target.value }))} required>
              <option value="">Select product</option>
              {products.data?.items.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.sku})</option>)}
            </Select>
          </FormField>
          <FormField label={drawerMode === "transfer" ? "Source warehouse" : "Warehouse"}>
            <Select value={form.warehouse_id} onChange={(event) => setForm((current) => ({ ...current, warehouse_id: event.target.value }))} required>
              <option value="">Select warehouse</option>
              {warehouses.data?.items.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.code})</option>)}
            </Select>
          </FormField>
          {drawerMode === "transfer" ? (
            <FormField label="Destination warehouse">
              <Select value={form.destination_warehouse_id} onChange={(event) => setForm((current) => ({ ...current, destination_warehouse_id: event.target.value }))} required>
                <option value="">Select destination</option>
                {warehouses.data?.items.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.code})</option>)}
              </Select>
            </FormField>
          ) : null}
          {drawerMode === "adjustment" ? (
            <FormField label="Counted quantity">
              <Input type="number" min="0" value={form.counted_quantity} onChange={(event) => setForm((current) => ({ ...current, counted_quantity: event.target.value }))} />
            </FormField>
          ) : (
            <FormField label="Quantity">
              <Input type="number" min="1" value={form.quantity} onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))} />
            </FormField>
          )}
          <FormField label="Reason">
            <Input value={form.reason} onChange={(event) => setForm((current) => ({ ...current, reason: event.target.value }))} required />
          </FormField>
          <FormField label="Notes">
            <Input value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} />
          </FormField>
          {formError ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{formError}</p> : null}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setDrawerMode(null)}>Cancel</Button>
            <Button type="submit" disabled={submitting}>{submitting ? "Saving..." : "Record movement"}</Button>
          </div>
        </form>
      </Drawer>
    </div>
  );
}
