"use client";

import type React from "react";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Boxes, CheckCircle2, ShieldCheck, Warehouse } from "lucide-react";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiRequest } from "@/lib/api";
import { saveSession } from "@/lib/auth";

type AuthFormProps = {
  mode: "login" | "register";
};

type AuthResponse = {
  access_token: string;
  user: {
    id: string;
    workspace_id: string;
    name: string;
    email: string;
    role: string;
  };
};

const authContent = {
  login: {
    eyebrow: "StockPilot OMS",
    title: "Sign in",
    description: "Inventory, orders, suppliers, and warehouse operations in one workspace.",
    submitLabel: "Continue to dashboard",
    footerLabel: "Need a new workspace?",
    footerLinkLabel: "Create an account",
    sideTitle: "Operations at a glance",
    sideDescription: "A cleaner way to manage stock movement, order flow, and warehouse execution.",
    highlights: [
      "Live stock visibility",
      "Order and supplier control",
      "Alerts, activity, and analytics"
    ]
  },
  register: {
    eyebrow: "StockPilot OMS",
    title: "Create your workspace",
    description: "Launch your operations workspace and start managing products, stock, suppliers, and orders.",
    submitLabel: "Create workspace",
    footerLabel: "Already have a workspace account?",
    footerLinkLabel: "Sign in",
    sideTitle: "Ready for day one",
    sideDescription: "Your workspace starts with an owner account and a clean base for inventory operations.",
    highlights: [
      "Workspace-scoped product and stock data",
      "Owner access to the full operations suite",
      "Clean setup for warehouses and fulfillment flow"
    ]
  }
} as const;

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const content = authContent[mode];
  const [form, setForm] = useState({
    workspace_name: "",
    name: "",
    email: "",
    password: ""
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload =
        mode === "register"
          ? form
          : {
              email: form.email,
              password: form.password
            };

      const response = await apiRequest<AuthResponse>(`/auth/${mode}`, {
        auth: false,
        method: "POST",
        body: JSON.stringify(payload)
      });

      saveSession({
        accessToken: response.access_token,
        user: response.user
      });
      router.replace("/dashboard");
      router.refresh();
      window.location.assign("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f4f7fb] px-4 py-8 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(46,108,246,0.15),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(15,23,42,0.12),_transparent_34%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(255,255,255,0))]" />

      <Card className="relative w-full max-w-6xl overflow-hidden border-white/80 bg-white/80 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <div className="grid min-h-[720px] lg:grid-cols-[minmax(0,560px)_1fr]">
          <CardContent className="flex items-center border-b border-slate-100 p-6 sm:p-10 lg:border-b-0 lg:border-r lg:p-12">
            <div className="mx-auto w-full max-w-md">
              <div className="mb-10 flex items-center gap-3">
                <div className="rounded-2xl bg-brand-500 p-3 text-white shadow-lg shadow-brand-500/25">
                  <Boxes className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{content.eyebrow}</p>
                  <p className="text-xs text-slate-500">Multi-warehouse operations platform</p>
                </div>
              </div>

              <div className="mb-8 space-y-3">
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">{content.title}</h1>
                <p className="max-w-md text-sm leading-6 text-slate-500">{content.description}</p>
              </div>

              <div className="mb-8 grid grid-cols-3 gap-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4">
                  <Warehouse className="h-4 w-4 text-brand-600" />
                  <p className="mt-3 text-lg font-semibold text-slate-900">3+</p>
                  <p className="text-xs text-slate-500">Warehouse-ready</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  <p className="mt-3 text-lg font-semibold text-slate-900">JWT</p>
                  <p className="text-xs text-slate-500">Secure access</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4">
                  <CheckCircle2 className="h-4 w-4 text-slate-700" />
                  <p className="mt-3 text-lg font-semibold text-slate-900">SQL</p>
                  <p className="text-xs text-slate-500">Raw Postgres</p>
                </div>
              </div>

              <form className="space-y-4" onSubmit={submit}>
                {mode === "register" ? (
                  <>
                    <FormField label="Workspace name" hint="Company or operations team">
                      <Input
                        value={form.workspace_name}
                        onChange={(event) => setForm((current) => ({ ...current, workspace_name: event.target.value }))}
                        placeholder="Northstar Supply Co"
                        required
                      />
                    </FormField>
                    <FormField label="Owner name" hint="Primary account holder">
                      <Input
                        value={form.name}
                        onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                        placeholder="Rubel Hossain"
                        required
                      />
                    </FormField>
                  </>
                ) : null}
                <FormField label="Work email">
                  <Input
                    type="email"
                    value={form.email}
                    onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                    placeholder="you@company.com"
                    required
                  />
                </FormField>
                <FormField label="Password" hint={mode === "register" ? "Minimum 8 characters" : undefined}>
                  <Input
                    type="password"
                    value={form.password}
                    onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                    placeholder="Enter your password"
                    required
                  />
                </FormField>
                {error ? <p className="rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-danger">{error}</p> : null}
                <Button className="h-12 w-full gap-2 rounded-xl text-sm font-semibold shadow-lg shadow-brand-500/20" disabled={loading} type="submit">
                  {loading ? "Working..." : content.submitLabel}
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </form>

              <p className="mt-6 text-sm text-slate-500">
                {content.footerLabel}{" "}
                <Link className="font-semibold text-brand-600 hover:text-brand-700" href={mode === "login" ? "/register" : "/login"}>
                  {content.footerLinkLabel}
                </Link>
              </p>
            </div>
          </CardContent>

          <div className="relative hidden overflow-hidden bg-slate-950 lg:flex lg:flex-col lg:justify-between">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(46,108,246,0.35),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(148,163,184,0.18),_transparent_32%)]" />
            <div className="relative flex h-full flex-col justify-between p-12 text-slate-100">
              <div>
                <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-200">
                  B2B Operations Workspace
                </div>
                <div className="mt-8 max-w-md space-y-4">
                  <h2 className="text-3xl font-semibold tracking-tight text-white">{content.sideTitle}</h2>
                  <p className="text-sm leading-7 text-slate-300">{content.sideDescription}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4">
                  {content.highlights.map((highlight, index) => (
                    <div
                      key={highlight}
                      className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 backdrop-blur-sm"
                    >
                      <div className="flex items-center gap-3">
                        <div className="rounded-xl bg-white/10 p-2 text-brand-300">
                          {index === 0 ? <Warehouse className="h-4 w-4" /> : index === 1 ? <Boxes className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                        </div>
                        <p className="text-sm font-medium text-slate-100">{highlight}</p>
                      </div>
                      <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-4 pt-6">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Modules</p>
                    <p className="mt-3 text-2xl font-semibold text-white">10</p>
                    <p className="mt-1 text-sm text-slate-400">Inventory to analytics</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Workflow</p>
                    <p className="mt-3 text-2xl font-semibold text-white">Live</p>
                    <p className="mt-1 text-sm text-slate-400">Stock, orders, movement</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
