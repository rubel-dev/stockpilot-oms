"use client";

import { Bell, LogOut, Search } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { MobileNav } from "@/components/layout/mobile-nav";
import { clearSession, loadSession } from "@/lib/auth";

export function TopNav() {
  const router = useRouter();
  const session = loadSession();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-5 py-4 lg:px-8">
        <div className="flex min-w-0 items-center gap-4">
          <MobileNav open={mobileNavOpen} onOpenChange={setMobileNavOpen} />
          <div className="hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500 md:flex">
            <Search className="h-4 w-4" />
            <span>Search products, orders, suppliers</span>
          </div>
          <div className="rounded-full bg-slate-100 p-2 text-slate-600">
            <Bell className="h-4 w-4" />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-right sm:block">
            <p className="text-sm font-semibold text-foreground">{session?.user.name ?? "Workspace User"}</p>
            <p className="text-xs text-muted">{session?.user.role ?? "member"}</p>
          </div>
          <button
            className="rounded-lg border border-slate-200 p-2 text-slate-500 hover:bg-slate-50"
            onClick={() => {
              clearSession();
              router.push("/login");
            }}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
