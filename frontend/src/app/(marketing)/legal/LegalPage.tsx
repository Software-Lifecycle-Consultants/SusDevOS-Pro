import Link from "next/link";

interface Props {
  title:       string;
  lastUpdated: string;
  children:    React.ReactNode;
}

export function LegalPage({ title, lastUpdated, children }: Props) {
  return (
    <div className="bg-white">
      {/* Header */}
      <section className="border-b border-surface-200 bg-surface-50 py-12">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-surface-400">
            Legal
          </p>
          <h1 className="mb-2 text-3xl font-bold text-surface-900">{title}</h1>
          <p className="text-sm text-surface-400">Last updated: {lastUpdated}</p>
        </div>
      </section>

      {/* Content */}
      <section className="py-12 sm:py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          {/* Legal nav */}
          <div className="mb-10 flex flex-wrap gap-2 rounded-xl border border-surface-200 bg-surface-50 p-4">
            <span className="text-xs font-medium text-surface-500 self-center mr-2">Also see:</span>
            {[
              { href: "/legal/privacy", label: "Privacy Policy" },
              { href: "/legal/terms",   label: "Terms of Service" },
              { href: "/legal/dpa",     label: "Data Processing Agreement" },
              { href: "/security",      label: "Security" },
            ].map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="rounded-full border border-surface-200 bg-white px-3 py-1 text-xs text-surface-600 transition-colors hover:border-brand-300 hover:text-brand-700"
              >
                {label}
              </Link>
            ))}
          </div>

          {/* Prose */}
          <div className="
            space-y-6 text-[17px] leading-8 text-surface-700
            [&>h2]:mt-10 [&>h2]:mb-3 [&>h2]:text-xl [&>h2]:font-bold [&>h2]:text-surface-900
            [&>h3]:mt-7 [&>h3]:mb-2 [&>h3]:text-base [&>h3]:font-semibold [&>h3]:text-surface-900
            [&>p]:text-[16px] [&>p]:leading-7
            [&>ul]:ml-5 [&>ul]:list-disc [&>ul]:space-y-1.5 [&>ul]:text-[16px] [&>ul]:leading-7
            [&>ol]:ml-5 [&>ol]:list-decimal [&>ol]:space-y-1.5 [&>ol]:text-[16px] [&>ol]:leading-7
            [&>table]:w-full [&>table]:border-collapse [&>table]:text-sm
            [&>table>thead>tr>th]:border [&>table>thead>tr>th]:border-surface-200 [&>table>thead>tr>th]:bg-surface-50 [&>table>thead>tr>th]:px-3 [&>table>thead>tr>th]:py-2 [&>table>thead>tr>th]:text-left [&>table>thead>tr>th]:font-semibold
            [&>table>tbody>tr>td]:border [&>table>tbody>tr>td]:border-surface-200 [&>table>tbody>tr>td]:px-3 [&>table>tbody>tr>td]:py-2
            [&>a]:text-brand-600 [&>a:hover]:text-brand-800 [&>a]:underline [&>a]:underline-offset-2
          ">
            {children}
          </div>
        </div>
      </section>
    </div>
  );
}
