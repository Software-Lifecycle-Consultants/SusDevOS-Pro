"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore, displayName } from "@/store/auth";

interface NavItem {
  href:  string;
  label: string;
  icon:  string;  // simple emoji icon — swap for Lucide later
}

const NAV: NavItem[] = [
  { href: "/dashboard",   label: "Dashboard",   icon: "📊" },
  { href: "/emissions",   label: "Emissions",   icon: "🏭" },
  { href: "/projects",    label: "Projects",    icon: "📁" },
  { href: "/ecosystem",   label: "Ecosystem",   icon: "🌿" },
  { href: "/targets",     label: "Targets",     icon: "🎯" },
  { href: "/reports",     label: "Reports",     icon: "📄" },
  { href: "/supply-chain",label: "Supply Chain",icon: "🔗" },
  { href: "/settings",    label: "Settings",    icon: "⚙️" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router    = useRouter();
  const pathname  = usePathname();
  const { user, accessToken, clearAuth } = useAuthStore();

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!accessToken) router.replace("/login");
  }, [accessToken, router]);

  if (!accessToken) return null;

  function handleSignOut() {
    clearAuth();
    router.replace("/login");
  }

  return (
    <div className="flex h-screen overflow-hidden bg-surface-50">
      {/* ── Sidebar ── */}
      <aside className="flex w-[var(--sidebar-width)] shrink-0 flex-col border-r border-surface-200 bg-white">
        {/* Brand */}
        <div className="flex h-14 items-center border-b border-surface-100 px-4">
          <span className="text-base font-bold text-brand-700">SusDevOS</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-2 py-4">
          <ul className="space-y-0.5">
            {NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`nav-item ${active ? "nav-item-active" : ""}`}
                  >
                    <span aria-hidden>{item.icon}</span>
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User footer */}
        <div className="border-t border-surface-100 p-3">
          <div className="mb-1 truncate px-1 text-xs font-medium text-surface-700">
            {displayName(user) || "—"}
          </div>
          <div className="truncate px-1 text-xs text-surface-400">{user?.email}</div>
          <button onClick={handleSignOut} className="btn-ghost btn-sm mt-2 w-full justify-start">
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center border-b border-surface-200 bg-white px-6">
          <h1 className="text-sm font-semibold text-surface-600 capitalize">
            {pathname.split("/").filter(Boolean)[0]?.replace(/-/g, " ") ?? "Dashboard"}
          </h1>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-y-auto p-6 animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
