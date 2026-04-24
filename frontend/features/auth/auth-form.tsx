"use client";

import type React from "react";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

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

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
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
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(46,108,246,0.10),_transparent_40%),linear-gradient(180deg,_#f8faff_0%,_#f5f7fb_100%)] px-4 py-10">
      <Card className="w-full max-w-md overflow-hidden">
        <CardContent className="p-8">
          <div className="mb-8 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-600">StockPilot OMS</p>
            <h1 className="text-2xl font-semibold text-foreground">
              {mode === "login" ? "Welcome back" : "Create your workspace"}
            </h1>
            <p className="text-sm text-muted">
              {mode === "login"
                ? "Sign in to manage inventory, orders, suppliers, and warehouse operations."
                : "Spin up a new operations workspace with an owner account and start configuring products and stock."}
            </p>
          </div>

          <form className="space-y-4" onSubmit={submit}>
            {mode === "register" ? (
              <>
                <FormField label="Workspace name">
                  <Input
                    value={form.workspace_name}
                    onChange={(event) => setForm((current) => ({ ...current, workspace_name: event.target.value }))}
                    placeholder="Northstar Supply Co"
                    required
                  />
                </FormField>
                <FormField label="Full name">
                  <Input
                    value={form.name}
                    onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                    placeholder="Rubel Hossain"
                    required
                  />
                </FormField>
              </>
            ) : null}
            <FormField label="Email">
              <Input
                type="email"
                value={form.email}
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                placeholder="you@company.com"
                required
              />
            </FormField>
            <FormField label="Password" hint={mode === "register" ? "Use 8 or more characters" : undefined}>
              <Input
                type="password"
                value={form.password}
                onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                placeholder="********"
                required
              />
            </FormField>
            {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-danger">{error}</p> : null}
            <Button className="w-full gap-2" disabled={loading} type="submit">
              {loading ? "Working..." : mode === "login" ? "Sign in" : "Create workspace"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted">
            {mode === "login" ? "Need a workspace?" : "Already have an account?"}{" "}
            <Link className="font-medium text-brand-600 hover:text-brand-700" href={mode === "login" ? "/register" : "/login"}>
              {mode === "login" ? "Register" : "Sign in"}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
