import Link from "next/link";
import { Leaf } from "lucide-react";

const COLUMNS = [
  {
    heading: "Product",
    links: [
      { href: "/features",           label: "Features"        },
      { href: "/pricing",            label: "Pricing"         },
      { href: "/integrations",       label: "Integrations"    },
      { href: "/changelog",          label: "Changelog"       },
      { href: "/demo",               label: "Book a demo"     },
    ],
  },
  {
    heading: "Resources",
    links: [
      { href: "/resources/guides",   label: "Guides"          },
      { href: "/resources/tools/carbon-estimator", label: "Carbon estimator" },
      { href: "/standards",          label: "Standards"       },
      { href: "/api-docs",           label: "API docs"        },
      { href: "/blog",               label: "Blog"            },
    ],
  },
  {
    heading: "Company",
    links: [
      { href: "/about",              label: "About"           },
      { href: "/contact",            label: "Contact"         },
      { href: "/security",           label: "Security"        },
    ],
  },
  {
    heading: "Legal",
    links: [
      { href: "/legal/privacy",      label: "Privacy policy"  },
      { href: "/legal/terms",        label: "Terms of service"},
      { href: "/legal/dpa",          label: "DPA"             },
    ],
  },
];

export function Footer() {
  return (
    <footer className="bg-surface-900 text-surface-400">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 pt-14 pb-8">

        {/* Top row */}
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-5 mb-12">

          {/* Brand column */}
          <div className="col-span-2 sm:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
                <Leaf className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-white text-[15px]">SusDevOS</span>
            </Link>
            <p className="text-sm leading-relaxed">
              GHG reporting and ecosystem tracking built on GHG Protocol, SBTi,
              CDP and TNFD.
            </p>
            {/* Social */}
            <div className="flex gap-3 mt-4">
              <a
                href="https://linkedin.com/company/susdevos"
                target="_blank"
                rel="noopener noreferrer"
                className="text-surface-500 hover:text-white transition-colors text-sm"
                aria-label="LinkedIn"
              >
                LinkedIn
              </a>
              <a
                href="https://github.com/susdevos"
                target="_blank"
                rel="noopener noreferrer"
                className="text-surface-500 hover:text-white transition-colors text-sm"
                aria-label="GitHub"
              >
                GitHub
              </a>
            </div>
          </div>

          {/* Link columns */}
          {COLUMNS.map(({ heading, links }) => (
            <div key={heading}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-surface-300 mb-3">
                {heading}
              </h3>
              <ul className="space-y-2">
                {links.map(({ href, label }) => (
                  <li key={href}>
                    <Link
                      href={href}
                      className="text-sm hover:text-white transition-colors"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-surface-800 pt-6 flex flex-col sm:flex-row justify-between gap-3 text-xs text-surface-600">
          <p>© {new Date().getFullYear()} SusDevOS Ltd. All rights reserved.</p>
          <p>
            GHG Protocol, SBTi, CDP, TNFD and IPCC are trademarks of their respective owners.
            SusDevOS is not affiliated with or endorsed by these organisations.
          </p>
        </div>
      </div>
    </footer>
  );
}
