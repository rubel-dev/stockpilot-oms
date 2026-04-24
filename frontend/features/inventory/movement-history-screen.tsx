"use client";

import { useMemo, useState } from "react";

import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { apiRequest } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type Movement = {
  id: string;
  product_name: string;
  product_sku: string;
  warehouse_name: string;
  movement_type: string;
  quantity: number;
  quantity_before: number;
  quantity_after: number;
  created_by_name?: string | null;
  created_at: string;
};

export function MovementHistoryScreen() {
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "100" });
    if (search) params.set("search", search);
    if (type) params.set("movement_type", type);
    return params.toString();
  }, [search, type]);
  const { data, loading, error, refresh } = useApi<{ items: Movement[] }>(() => apiRequest(`/inventory/movements?${query}`), [query]);

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Inventory" title="Movement history" description="Trace stock changes with before-and-after quantities and operational references." />
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr,240px]">
          <Input placeholder="Search movement reason, notes, or product" value={search} onChange={(event) => setSearch(event.target.value)} />
          <Select value={type} onChange={(event) => setType(event.target.value)}>
            <option value="">All movement types</option>
            <option value="stock_in">Stock in</option>
            <option value="stock_out">Stock out</option>
            <option value="transfer_out">Transfer out</option>
            <option value="transfer_in">Transfer in</option>
            <option value="adjustment">Adjustment</option>
            <option value="reservation">Reservation</option>
            <option value="reservation_release">Reservation release</option>
            <option value="order_deduction">Order deduction</option>
          </Select>
        </CardContent>
      </Card>
      {loading ? (
        <Skeleton className="h-[480px] rounded-xl" />
      ) : error ? (
        <ErrorState title="Could not load movement history" message={error} onRetry={refresh} />
      ) : !(data?.items.length ?? 0) ? (
        <EmptyState title="No movement events" description="As stock operations happen, they will appear here with timestamps and quantity deltas." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Product</Th>
                    <Th>Warehouse</Th>
                    <Th>Type</Th>
                    <Th>Quantity</Th>
                    <Th>Before</Th>
                    <Th>After</Th>
                    <Th>User</Th>
                    <Th>Timestamp</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data?.items.map((item) => (
                    <tr key={item.id}>
                      <Td>
                        <div className="font-medium text-foreground">{item.product_name}</div>
                        <div className="mt-1 text-xs text-muted">{item.product_sku}</div>
                      </Td>
                      <Td>{item.warehouse_name}</Td>
                      <Td><Badge tone={item.movement_type}>{item.movement_type.replaceAll("_", " ")}</Badge></Td>
                      <Td>{formatNumber(item.quantity)}</Td>
                      <Td>{formatNumber(item.quantity_before)}</Td>
                      <Td>{formatNumber(item.quantity_after)}</Td>
                      <Td>{item.created_by_name ?? "System"}</Td>
                      <Td>{new Date(item.created_at).toLocaleString()}</Td>
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

