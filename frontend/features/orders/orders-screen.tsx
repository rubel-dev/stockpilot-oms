"use client";

import Link from "next/link";
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
import { formatCurrency } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type Order = {
  id: string;
  order_number: string;
  order_type: string;
  status: string;
  warehouse_name: string;
  supplier_name?: string | null;
  customer_name?: string | null;
  item_count: number;
  subtotal_amount: number;
  created_at: string;
};

export function OrdersScreen() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [orderType, setOrderType] = useState("");

  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "100" });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    if (orderType) params.set("order_type", orderType);
    return params.toString();
  }, [search, status, orderType]);

  const { data, loading, error, refresh } = useApi<{ items: Order[] }>(() => apiRequest(`/orders?${query}`), [query]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Execution"
        title="Orders"
        description="Coordinate outbound sales and inbound purchase orders with lifecycle visibility."
        action={{ label: "New order", href: "/orders/new" }}
      />
      <Card>
        <CardContent className="grid gap-3 p-4 lg:grid-cols-[1fr,220px,220px]">
          <Input placeholder="Search order number, customer, or supplier" value={search} onChange={(event) => setSearch(event.target.value)} />
          <Select value={orderType} onChange={(event) => setOrderType(event.target.value)}>
            <option value="">All order types</option>
            <option value="sales">Sales</option>
            <option value="purchase">Purchase</option>
          </Select>
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="confirmed">Confirmed</option>
            <option value="processing">Processing</option>
            <option value="shipped">Shipped</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </Select>
        </CardContent>
      </Card>

      {loading ? (
        <Skeleton className="h-[460px] rounded-xl" />
      ) : error ? (
        <ErrorState title="Could not load orders" message={error} onRetry={refresh} />
      ) : !(data?.items.length ?? 0) ? (
        <EmptyState title="No orders yet" description="Create draft sales or purchase orders to start reserving stock and receiving inventory." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Order</Th>
                    <Th>Counterparty</Th>
                    <Th>Warehouse</Th>
                    <Th>Items</Th>
                    <Th>Total</Th>
                    <Th>Status</Th>
                    <Th>Created</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data?.items.map((item) => (
                    <tr key={item.id}>
                      <Td>
                        <Link href={`/orders/${item.id}`}>
                          <div className="font-medium text-foreground">{item.order_number}</div>
                          <div className="mt-1 text-xs text-muted">{item.order_type}</div>
                        </Link>
                      </Td>
                      <Td>{item.order_type === "sales" ? item.customer_name ?? "--" : item.supplier_name ?? "--"}</Td>
                      <Td>{item.warehouse_name}</Td>
                      <Td>{item.item_count}</Td>
                      <Td>{formatCurrency(item.subtotal_amount)}</Td>
                      <Td><Badge tone={item.status}>{item.status}</Badge></Td>
                      <Td>{new Date(item.created_at).toLocaleDateString()}</Td>
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
