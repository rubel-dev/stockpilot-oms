"use client";

import type React from "react";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { apiRequest } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type Product = { id: string; name: string; sku: string };
type Supplier = { id: string; name: string };
type Warehouse = { id: string; name: string; code: string };

export function OrderCreateScreen() {
  const router = useRouter();
  const [orderType, setOrderType] = useState<"sales" | "purchase">("sales");
  const [warehouseId, setWarehouseId] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState([{ product_id: "", quantity: "1", unit_price: "0", unit_cost: "0" }]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const products = useApi<{ items: Product[] }>(() => apiRequest("/products?page_size=100"), []);
  const suppliers = useApi<{ items: Supplier[] }>(() => apiRequest("/suppliers?page_size=100"), []);
  const warehouses = useApi<{ items: Warehouse[] }>(() => apiRequest("/warehouses?page_size=100"), []);

  const total = useMemo(
    () =>
      items.reduce((sum, item) => {
        const price = orderType === "sales" ? Number(item.unit_price) : Number(item.unit_cost);
        return sum + price * Number(item.quantity);
      }, 0),
    [items, orderType]
  );

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        order_type: orderType,
        warehouse_id: warehouseId,
        supplier_id: orderType === "purchase" ? supplierId : null,
        customer_name: orderType === "sales" ? customerName : null,
        notes: notes || null,
        items: items.map((item) => ({
          product_id: item.product_id,
          quantity: Number(item.quantity),
          unit_price: orderType === "sales" ? Number(item.unit_price) : undefined,
          unit_cost: orderType === "purchase" ? Number(item.unit_cost) : undefined
        }))
      };
      const created = await apiRequest<{ id: string }>("/orders", { method: "POST", body: JSON.stringify(payload) });
      router.push(`/orders/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create order.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Execution" title="New order" description="Create a draft sales or purchase order with warehouse assignment and itemized pricing." />
      <Card>
        <CardContent className="p-6">
          <form className="space-y-6" onSubmit={submit}>
            <div className="grid gap-4 md:grid-cols-3">
              <FormField label="Order type">
                <Select value={orderType} onChange={(event) => setOrderType(event.target.value as "sales" | "purchase")}>
                  <option value="sales">Sales</option>
                  <option value="purchase">Purchase</option>
                </Select>
              </FormField>
              <FormField label="Warehouse">
                <Select value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)} required>
                  <option value="">Select warehouse</option>
                  {warehouses.data?.items.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.code})</option>)}
                </Select>
              </FormField>
              {orderType === "sales" ? (
                <FormField label="Customer">
                  <Input value={customerName} onChange={(event) => setCustomerName(event.target.value)} required />
                </FormField>
              ) : (
                <FormField label="Supplier">
                  <Select value={supplierId} onChange={(event) => setSupplierId(event.target.value)} required>
                    <option value="">Select supplier</option>
                    {suppliers.data?.items.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </Select>
                </FormField>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-foreground">Line items</h3>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setItems((current) => [...current, { product_id: "", quantity: "1", unit_price: "0", unit_cost: "0" }])}
                >
                  Add line
                </Button>
              </div>
              <div className="space-y-3">
                {items.map((item, index) => (
                  <div key={index} className="grid gap-3 rounded-lg border border-slate-100 p-4 md:grid-cols-[1.8fr,0.8fr,0.8fr,auto]">
                    <Select
                      value={item.product_id}
                      onChange={(event) =>
                        setItems((current) => current.map((row, rowIndex) => (rowIndex === index ? { ...row, product_id: event.target.value } : row)))
                      }
                    >
                      <option value="">Select product</option>
                      {products.data?.items.map((product) => <option key={product.id} value={product.id}>{product.name} ({product.sku})</option>)}
                    </Select>
                    <Input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(event) =>
                        setItems((current) => current.map((row, rowIndex) => (rowIndex === index ? { ...row, quantity: event.target.value } : row)))
                      }
                    />
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={orderType === "sales" ? item.unit_price : item.unit_cost}
                      onChange={(event) =>
                        setItems((current) =>
                          current.map((row, rowIndex) =>
                            rowIndex === index
                              ? { ...row, [orderType === "sales" ? "unit_price" : "unit_cost"]: event.target.value }
                              : row
                          )
                        )
                      }
                    />
                    <Button type="button" variant="ghost" onClick={() => setItems((current) => current.filter((_, rowIndex) => rowIndex !== index))}>
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            <FormField label="Notes">
              <Input value={notes} onChange={(event) => setNotes(event.target.value)} />
            </FormField>

            <div className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/50 px-4 py-4">
              <div>
                <p className="text-sm text-muted">Draft total</p>
                <p className="mt-1 text-2xl font-semibold text-foreground">{formatCurrency(total)}</p>
              </div>
              <div className="flex gap-3">
                <a href="/orders"><Button type="button" variant="secondary">Cancel</Button></a>
                <Button disabled={submitting} type="submit">{submitting ? "Creating..." : "Create draft order"}</Button>
              </div>
            </div>
            {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{error}</p> : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
