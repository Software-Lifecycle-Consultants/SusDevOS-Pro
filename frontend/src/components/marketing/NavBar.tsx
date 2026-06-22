"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X, Leaf } from "lucide-react";

const NAV_LINKS = [
  { href: "/features",    label: "Features"   },
  { href: "/pricing",     label: "Pricing"    },
  { href: "/standards",   label: "Standards"  },
  { href: "/integrations",label: "Integrations"},
  { href: "/blog",        label: "Blog"       },
];

export function NavBar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-surface-100">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 flex h-16 items-center justify-between">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
            <Leaf className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-surface-900 text-[15px]">SusDevOS</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-surface-500">
          {NAV_LINKS.map(({ href, label }) => (
            <Link key={href} href={href} className="hover:text-surface-900 transition-colors">
              {label}
            </Link>
          ))}
        </nav>

        {/* Desktop CTAs */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-surface-600 hover:text-surface-900 transition-colors px-3 py-1.5"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="text-sm bg-brand-600 text-white px-4 py-2 rounded-md hover:bg-brand-700 transition-colors font-medium"
          >
            Start free
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 text-surface-600 hover:text-surface-900"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-surface-100 bg-white px-4 pt-3 pb-5 flex flex-col gap-3 text-sm">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-surface-700 hover:text-surface-900 py-1"
              onClick={() => setOpen(false)}
            >
              {label}
            </Link>
          ))}
          <div className="border-t border-surface-100 pt-3 flex flex-col gap-2">
            <Link href="/login" className="text-surface-700 py-1">Sign in</Link>
            <Link
              href="/register"
              className="bg-brand-600 text-white px-4 py-2 rounded-md text-center font-medium"
            >
              Start free — no credit card
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
