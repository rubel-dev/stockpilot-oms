"use client";

import type React from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiRequest } from "@/lib/api";

export function ProductCreateScreen() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    sku: "",
    description: "",
    unit: "each",
    reorder_point: "0",
    reorder_quantity: "0"
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await apiRequest<{ id: string }>("/products", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          sku: form.sku || null,
          description: form.description || null,
          unit: form.unit,
          reorder_point: Number(form.reorder_point),
          reorder_quantity: Number(form.reorder_quantity)
        })
      });
      router.push(`/products/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create product.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Catalog" title="New product" description="Define a product record with SKU posture and reorder controls for future stock operations." />
      <Card>
        <CardContent className="p-6">
          <form className="grid gap-6" onSubmit={submit}>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Product name">
                <Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required />
              </FormField>
              <FormField label="SKU" hint="Leave blank to auto-generate">
                <Input value={form.sku} onChange={(event) => setForm((current) => ({ ...current, sku: event.target.value }))} />
              </FormField>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <FormField label="Unit">
                <Input value={form.unit} onChange={(event) => setForm((current) => ({ ...current, unit: event.target.value }))} />
              </FormField>
              <FormField label="Reorder point">
                <Input type="number" min="0" value={form.reorder_point} onChange={(event) => setForm((current) => ({ ...current, reorder_point: event.target.value }))} />
              </FormField>
              <FormField label="Reorder quantity">
                <Input type="number" min="0" value={form.reorder_quantity} onChange={(event) => setForm((current) => ({ ...current, reorder_quantity: event.target.value }))} />
              </FormField>
            </div>
            <FormField label="Description">
              <Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} />
            </FormField>
            {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{error}</p> : null}
            <div className="flex justify-end gap-3">
              <a href="/products"><Button variant="secondary" type="button">Cancel</Button></a>
              <Button disabled={saving} type="submit">{saving ? "Creating..." : "Create product"}</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
