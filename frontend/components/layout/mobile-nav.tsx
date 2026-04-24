"use client";

import Link from "next/link";
import { Menu, Package } from "lucide-react";
import { usePathname } from "next/navigation";

import { primaryNavItems } from "@/components/layout/nav-config";
import { Button } from "@/components/ui/button";
import { Drawer } from "@/components/ui/drawer";
import { cn } from "@/lib/utils";

export function MobileNav({
  open,
  onOpenChange
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const pathname = usePathname();

  return (
    <>
      <Button
        variant="secondary"
        className="md:hidden"
        onClick={() => onOpenChange(true)}
        aria-label="Open navigation"
      >
        <Menu className="h-4 w-4" />
      </Button>
      <Drawer
        open={open}
        onOpenChange={onOpenChange}
        title="Navigation"
        description="Move between operations, analytics, and audit surfaces."
      >
        <div className="space-y-5">
          <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
            <div className="rounded-lg bg-brand-500 p-2 text-white shadow-soft">
              <Package className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">StockPilot OMS</p>
              <p className="text-xs text-muted">Operations control center</p>
            </div>
          </div>

          <nav className="space-y-1">
            {primaryNavItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => onOpenChange(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition",
                    active ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-50 hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </Drawer>
    </>
  );
}
