"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/settings/entity",    label: "Organisation" },
  { href: "/settings/users",     label: "Users"        },
  { href: "/settings/api-keys",  label: "API Keys"     },
  { href: "/settings/billing",   label: "Billing"      },
  { href: "/settings/audit-log", label: "Audit Log"    },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your organisation, users and account.</p>
      </div>

      <div className="flex gap-6">
        {/* Tab sidebar */}
        <nav className="w-44 shrink-0">
          <ul className="space-y-0.5">
            {TABS.map(({ href, label }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <li key={href}>
                  <Link
                    href={href}
                    className={[
                      "block rounded-md px-3 py-2 text-sm transition-colors",
                      active
                        ? "bg-brand-50 font-medium text-brand-700"
                        : "text-surface-600 hover:bg-surface-100 hover:text-surface-900",
                    ].join(" ")}
                  >
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Tab content */}
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </div>
  );
}
