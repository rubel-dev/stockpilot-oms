"use client";

import { useState } from "react";

import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { apiRequest } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type OrderDetail = {
  id: string;
  order_number: string;
  order_type: string;
  status: string;
  warehouse_name: string;
  supplier_name?: string | null;
  customer_name?: string | null;
  subtotal_amount: number;
  notes?: string | null;
  items: Array<{
    id: string;
    product_name: string;
    product_sku: string;
    quantity: number;
    unit_price?: number | null;
    unit_cost?: number | null;
    line_total: number;
  }>;
};

export function OrderDetailScreen({ id }: { id: string }) {
  const { data, loading, error, refresh } = useApi<OrderDetail>(() => apiRequest(`/orders/${id}`), [id]);
  const [busy, setBusy] = useState(false);

  if (loading) return <Skeleton className="h-[540px] rounded-xl" />;
  if (error || !data) return <ErrorState title="Order unavailable" message={error ?? "Order not found."} />;

  const transitions = [
    data.status === "draft" && { label: "Confirm", path: "confirm" },
    data.status === "confirmed" && { label: "Move to processing", path: "process" },
    data.status === "processing" && data.order_type === "sales" && { label: "Ship order", path: "ship" },
    ["confirmed", "processing"].includes(data.status) && data.order_type === "purchase" && { label: "Complete purchase", path: "complete" },
    data.status === "shipped" && data.order_type === "sales" && { label: "Complete order", path: "complete" },
    ["draft", "confirmed", "processing"].includes(data.status) && { label: "Cancel order", path: "cancel", danger: true }
  ].filter(Boolean) as Array<{ label: string; path: string; danger?: boolean }>;

  const runAction = async (path: string) => {
    setBusy(true);
    try {
      await apiRequest(`/orders/${id}/${path}`, { method: "POST" });
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Execution"
        title={data.order_number}
        description={`${data.order_type === "sales" ? data.customer_name : data.supplier_name} - ${data.warehouse_name}`}
      />
      <div className="grid gap-6 xl:grid-cols-[0.9fr,1.1fr]">
        <Card>
          <CardHeader><h3 className="text-base font-semibold text-foreground">Order status</h3></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted">Current status</p>
              <Badge tone={data.status}>{data.status}</Badge>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted">Order type</p>
              <Badge tone={data.order_type}>{data.order_type}</Badge>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted">Subtotal</p>
              <p className="text-2xl font-semibold text-foreground">{formatCurrency(data.subtotal_amount)}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {transitions.map((action) => (
                <Button key={action.path} disabled={busy} variant={action.danger ? "danger" : "secondary"} onClick={() => runAction(action.path)}>
                  {action.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><h3 className="text-base font-semibold text-foreground">Order items</h3></CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Product</Th>
                    <Th>Quantity</Th>
                    <Th>{data.order_type === "sales" ? "Unit price" : "Unit cost"}</Th>
                    <Th>Line total</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data.items.map((item) => (
                    <tr key={item.id}>
                      <Td>
                        <div className="font-medium text-foreground">{item.product_name}</div>
                        <div className="mt-1 text-xs text-muted">{item.product_sku}</div>
                      </Td>
                      <Td>{item.quantity}</Td>
                      <Td>{formatCurrency(data.order_type === "sales" ? item.unit_price ?? 0 : item.unit_cost ?? 0)}</Td>
                      <Td>{formatCurrency(item.line_total)}</Td>
                    </tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
