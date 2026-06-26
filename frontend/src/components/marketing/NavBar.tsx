"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X, ArrowRight, Leaf } from "lucide-react";

const NAV_LINKS = [
  { href: "/features",     label: "Features"     },
  { href: "/pricing",      label: "Pricing"      },
  { href: "/standards",    label: "Standards"    },
  { href: "/integrations", label: "Integrations" },
  { href: "/blog",         label: "Blog"         },
];

export function NavBar() {
  const [open, setOpen] = useState(false);

  return (
    <div className="sticky top-0 z-50">
      {/* Announcement bar */}
      <div className="hidden sm:flex items-center justify-center gap-3 bg-surface-900 py-2 text-xs text-surface-400">
        <span className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-400 animate-pulse" />
          CDP 2025 Climate Change questionnaire export is now live
        </span>
        <Link
          href="/changelog"
          className="flex items-center gap-1 font-medium text-brand-400 hover:text-brand-300 transition-colors"
        >
          See what&apos;s new <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Main nav */}
      <header className="border-b border-surface-100 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">

          {/* Logo */}
          <Link href="/" className="group flex shrink-0 items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 shadow-sm shadow-brand-600/30 transition-colors group-hover:bg-brand-700">
              <Leaf className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold tracking-tight text-surface-900">SusDevOS</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-0.5 md:flex">
            {NAV_LINKS.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="rounded-md px-3 py-2 text-sm text-surface-500 transition-colors hover:bg-surface-50 hover:text-surface-900"
              >
                {label}
              </Link>
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden items-center gap-2 md:flex">
            <Link
              href="/login"
              className="px-3 py-2 text-sm text-surface-600 transition-colors hover:text-surface-900"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm shadow-brand-600/25 transition-colors hover:bg-brand-700"
            >
              Start free
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="rounded-md p-2 text-surface-600 hover:text-surface-900 md:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile menu */}
        {open && (
          <div className="flex flex-col gap-1 border-t border-surface-100 bg-white px-4 pb-5 pt-3 md:hidden">
            {NAV_LINKS.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="rounded-md px-3 py-2 text-sm text-surface-700 hover:bg-surface-50 hover:text-surface-900"
                onClick={() => setOpen(false)}
              >
                {label}
              </Link>
            ))}
            <div className="mt-2 flex flex-col gap-2 border-t border-surface-100 pt-3">
              <Link href="/login" className="px-3 py-2 text-sm text-surface-700">
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-brand-600 px-4 py-2.5 text-center text-sm font-medium text-white transition-colors hover:bg-brand-700"
              >
                Start free — no credit card
              </Link>
            </div>
          </div>
        )}
      </header>
    </div>
  );
}
