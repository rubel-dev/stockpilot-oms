"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Filter, Search } from "lucide-react";

import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { apiRequest } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type ProductRow = {
  id: string;
  name: string;
  sku: string;
  category_name?: string | null;
  total_on_hand: number;
  total_reserved: number;
  total_available: number;
  warehouse_count: number;
  status: string;
  updated_at: string;
};

type ProductResponse = {
  items: ProductRow[];
  page: number;
  page_size: number;
  total: number;
};

export function ProductsScreen() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    params.set("page_size", "50");
    return params.toString();
  }, [search, status]);

  const { data, error, loading, refresh } = useApi<ProductResponse>(() => apiRequest(`/products?${query}`), [query]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Catalog"
        title="Products"
        description="Track sellable items, reorder posture, and stock visibility across the warehouse network."
        action={{ label: "New product", href: "/products/new" }}
      />

      <Card>
        <CardContent className="grid gap-3 p-4 lg:grid-cols-[1.4fr,220px,auto]">
          <div className="relative">
            <Search className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
            <Input className="pl-9" placeholder="Search by product name, SKU, or description" value={search} onChange={(event) => setSearch(event.target.value)} />
          </div>
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </Select>
          <Button variant="secondary" className="gap-2" onClick={() => refresh()}>
            <Filter className="h-4 w-4" />
            Refresh
          </Button>
        </CardContent>
      </Card>

      {loading ? (
        <Skeleton className="h-[420px] rounded-xl" />
      ) : error ? (
        <ErrorState title="Could not load products" message={error} onRetry={refresh} />
      ) : !(data?.items.length ?? 0) ? (
        <EmptyState title="No products found" description="Add your first SKU to start tracking inventory and order activity." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Product</Th>
                    <Th>Category</Th>
                    <Th>Stock</Th>
                    <Th>Reserved</Th>
                    <Th>Available</Th>
                    <Th>Warehouses</Th>
                    <Th>Status</Th>
                    <Th>Updated</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data?.items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/60">
                      <Td>
                        <Link className="block" href={`/products/${item.id}`}>
                          <div className="font-medium text-foreground">{item.name}</div>
                          <div className="mt-1 text-xs text-muted">{item.sku}</div>
                        </Link>
                      </Td>
                      <Td>{item.category_name ?? "Unassigned"}</Td>
                      <Td>{formatNumber(item.total_on_hand)}</Td>
                      <Td>{formatNumber(item.total_reserved)}</Td>
                      <Td className="font-medium text-foreground">{formatNumber(item.total_available)}</Td>
                      <Td>{formatNumber(item.warehouse_count)}</Td>
                      <Td><Badge tone={item.status}>{item.status}</Badge></Td>
                      <Td>{new Date(item.updated_at).toLocaleDateString()}</Td>
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
