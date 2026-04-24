"use client";

import Link from "next/link";
import { Package } from "lucide-react";
import { usePathname } from "next/navigation";

import { primaryNavItems } from "@/components/layout/nav-config";
import { cn } from "@/lib/utils";

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-72 border-r border-slate-200 bg-white xl:flex xl:flex-col">
      <div className="border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-brand-500 p-2 text-white shadow-soft">
            <Package className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">StockPilot OMS</p>
            <p className="text-xs text-muted">Operations control center</p>
          </div>
        </div>
      </div>
      <nav className="space-y-1 px-4 py-5">
        {primaryNavItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                active ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-50 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
