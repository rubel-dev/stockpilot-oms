"use client";

import { useMemo, useState } from "react";

import { EmptyState } from "@/components/data-display/empty-state";
import { ErrorState } from "@/components/data-display/error-state";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, Td, Th, TableHead } from "@/components/ui/table";
import { apiRequest } from "@/lib/api";
import { useApi } from "@/lib/use-api";

type Log = {
  id: string;
  actor_name?: string | null;
  action: string;
  entity_type: string;
  summary: string;
  created_at: string;
};

export function ActivityScreen() {
  const [search, setSearch] = useState("");
  const [entityType, setEntityType] = useState("");
  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "100" });
    if (search) params.set("search", search);
    if (entityType) params.set("entity_type", entityType);
    return params.toString();
  }, [search, entityType]);
  const { data, loading, error, refresh } = useApi<{ items: Log[] }>(() => apiRequest(`/activity?${query}`), [query]);

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Audit" title="Activity" description="Searchable event feed for product, warehouse, inventory, order, and alert operations." />
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr,240px]">
          <Input placeholder="Search summaries, action names, or entity types" value={search} onChange={(event) => setSearch(event.target.value)} />
          <Select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
            <option value="">All entity types</option>
            <option value="product">Product</option>
            <option value="warehouse">Warehouse</option>
            <option value="order">Order</option>
            <option value="supplier">Supplier</option>
            <option value="alert">Alert</option>
          </Select>
        </CardContent>
      </Card>
      {loading ? (
        <Skeleton className="h-[460px] rounded-xl" />
      ) : error ? (
        <ErrorState title="Could not load activity feed" message={error} onRetry={refresh} />
      ) : !(data?.items.length ?? 0) ? (
        <EmptyState title="No audit events yet" description="Operational activity will appear here as users create, move, confirm, ship, and resolve records." />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <Th>Summary</Th>
                    <Th>Actor</Th>
                    <Th>Action</Th>
                    <Th>Entity</Th>
                    <Th>Timestamp</Th>
                  </tr>
                </TableHead>
                <TableBody>
                  {data?.items.map((item) => (
                    <tr key={item.id}>
                      <Td className="max-w-[480px] text-foreground">{item.summary}</Td>
                      <Td>{item.actor_name ?? "System"}</Td>
                      <Td>{item.action}</Td>
                      <Td>{item.entity_type}</Td>
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

