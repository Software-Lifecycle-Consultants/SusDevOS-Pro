"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Bell } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore, displayName } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";

interface NavItem {
  href:  string;
  label: string;
  icon:  string;
}

const NAV: NavItem[] = [
  { href: "/dashboard",    label: "Dashboard",    icon: "📊" },
  { href: "/emissions",    label: "Emissions",    icon: "🏭" },
  { href: "/inventories",  label: "Inventories",  icon: "📋" },
  { href: "/targets",      label: "Targets",      icon: "🎯" },
  { href: "/projects",     label: "Projects",     icon: "📁" },
  { href: "/land-parcels", label: "Land Parcels", icon: "🗺️" },
  { href: "/ecosystem",    label: "Ecosystem",    icon: "🌿" },
  { href: "/restorations", label: "Restorations", icon: "🌳" },
  { href: "/reports",      label: "Reports",      icon: "📄" },
  { href: "/settings",     label: "Settings",     icon: "⚙️" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router   = useRouter();
  const pathname = usePathname();
  const { user, accessToken, activeEntityId, clearAuth } = useAuthStore();

  useEffect(() => {
    if (!accessToken) router.replace("/login");
  }, [accessToken, router]);

  // Unread notification count — polled every 60s
  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};
  const { data: notifData } = useQuery<{ results: { IsRead: boolean }[] }>({
    queryKey: ["notifications-count", activeEntityId],
    queryFn: () =>
      axiosInstance.get("/api/notifications/?unread=true&page_size=50", { headers })
        .then((r) => r.data),
    enabled: !!accessToken && !!activeEntityId,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
  const unreadCount = notifData?.results?.length ?? 0;

  if (!accessToken) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-surface-50">
      {/* ── Sidebar ── */}
      <aside className="flex w-[var(--sidebar-width)] shrink-0 flex-col border-r border-surface-200 bg-white">
        <div className="flex h-14 items-center border-b border-surface-100 px-4">
          <Link href="/dashboard" className="text-base font-bold text-brand-700">SusDevOS</Link>
        </div>

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

        <div className="border-t border-surface-100 p-3">
          <div className="mb-0.5 truncate px-1 text-xs font-medium text-surface-700">
            {displayName(user) || "—"}
          </div>
          <div className="truncate px-1 text-xs text-surface-400">{user?.email}</div>
          <button
            onClick={() => { clearAuth(); router.replace("/login"); }}
            className="btn-ghost btn-sm mt-2 w-full justify-start"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-surface-200 bg-white px-6">
          <h1 className="text-sm font-semibold text-surface-600 capitalize">
            {pathname.split("/").filter(Boolean)[0]?.replace(/-/g, " ") ?? "Dashboard"}
          </h1>

          {/* Notifications bell */}
          <Link
            href="/notifications"
            className="relative p-2 rounded-md text-surface-500 hover:text-surface-800 hover:bg-surface-100 transition-colors"
            aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white leading-none">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </Link>
        </header>

        <div className="flex-1 overflow-y-auto p-6 animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
