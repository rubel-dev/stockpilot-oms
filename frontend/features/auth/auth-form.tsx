"use client";

import type React from "react";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2 } from "lucide-react";

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
    title: "Sign in to your operations workspace",
    description:
      "Access inventory, warehouse activity, supplier records, and order workflows from one operational dashboard.",
    submitLabel: "Sign in to StockPilot",
    footerLabel: "Need a new workspace?",
    footerLinkLabel: "Create an account",
    sideTitle: "Built for day-to-day operations",
    sideDescription:
      "Pick up where your team left off with live stock visibility, order tracking, and warehouse activity in one place.",
    highlights: [
      "Review stock positions across every warehouse.",
      "Track purchase and sales orders without leaving the workspace.",
      "Stay on top of alerts, movements, and team activity."
    ]
  },
  register: {
    eyebrow: "StockPilot OMS",
    title: "Create your workspace",
    description:
      "Set up a StockPilot workspace for your team and start managing products, warehouses, suppliers, and operational stock flows.",
    submitLabel: "Create workspace and continue",
    footerLabel: "Already have a workspace account?",
    footerLinkLabel: "Sign in",
    sideTitle: "What your workspace includes",
    sideDescription:
      "Your owner account is created with the workspace so you can start configuring inventory operations right away.",
    highlights: [
      "A dedicated workspace for your products, warehouses, and suppliers.",
      "An owner account with access to dashboard, orders, analytics, and alerts.",
      "A clean starting point for inventory balances, movements, and team workflows."
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
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(46,108,246,0.10),_transparent_40%),linear-gradient(180deg,_#f8faff_0%,_#f5f7fb_100%)] px-4 py-10">
      <Card className="w-full max-w-5xl overflow-hidden border-white/70 bg-white/90 shadow-xl shadow-slate-200/70 backdrop-blur">
        <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
          <CardContent className="border-b border-slate-100 p-8 lg:border-b-0 lg:border-r">
            <div className="mb-8 space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-600">{content.eyebrow}</p>
              <h1 className="text-2xl font-semibold text-foreground sm:text-3xl">{content.title}</h1>
              <p className="max-w-xl text-sm leading-6 text-muted">{content.description}</p>
            </div>

            <form className="space-y-4" onSubmit={submit}>
              {mode === "register" ? (
                <>
                  <FormField label="Workspace name" hint="This becomes the main company workspace for inventory operations.">
                    <Input
                      value={form.workspace_name}
                      onChange={(event) => setForm((current) => ({ ...current, workspace_name: event.target.value }))}
                      placeholder="Northstar Supply Co"
                      required
                    />
                  </FormField>
                  <FormField label="Owner name" hint="The first account will be created as the workspace owner.">
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
              <FormField label="Password" hint={mode === "register" ? "Use at least 8 characters for your owner account." : undefined}>
                <Input
                  type="password"
                  value={form.password}
                  onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                  placeholder="Enter your password"
                  required
                />
              </FormField>
              {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{error}</p> : null}
              <Button className="w-full gap-2" disabled={loading} type="submit">
                {loading ? "Working..." : content.submitLabel}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>

            <p className="mt-6 text-sm text-muted">
              {content.footerLabel}{" "}
              <Link className="font-medium text-brand-600 hover:text-brand-700" href={mode === "login" ? "/register" : "/login"}>
                {content.footerLinkLabel}
              </Link>
            </p>
          </CardContent>

          <div className="bg-slate-950 px-8 py-10 text-slate-100">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-300">Operations Overview</p>
              <h2 className="text-xl font-semibold">{content.sideTitle}</h2>
              <p className="text-sm leading-6 text-slate-300">{content.sideDescription}</p>
            </div>

            <div className="mt-8 space-y-4">
              {content.highlights.map((highlight) => (
                <div key={highlight} className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-4">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 text-brand-300" />
                  <p className="text-sm leading-6 text-slate-200">{highlight}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
