import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Calendar } from "lucide-react";

export const metadata: Metadata = {
  title: "Blog — SusDevOS",
  description:
    "Practical guides on GHG reporting, Scope 3, carbon credit validation, restoration MRV, TNFD biodiversity disclosure, and sustainable development — from the SusDevOS team.",
  alternates: {
    types: { "application/rss+xml": "/rss.xml" },
  },
};

interface PostSummary {
  BlogId:      number;
  Title:       string;
  Slug:        string;
  PostBody:    string;
  PublishedAt: string | null;
  SeoTitle:    string | null;
  SeoDescription: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getPosts(): Promise<PostSummary[]> {
  try {
    const res = await fetch(`${API_BASE}/api/public/blog/`, {
      next: { revalidate: 300 }, // ISR — revalidate every 5 minutes
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

function readingTime(body: string): number {
  return Math.max(1, Math.ceil(body.trim().split(/\s+/).length / 200));
}

function excerpt(post: PostSummary): string {
  if (post.SeoDescription) return post.SeoDescription;
  return post.PostBody.replace(/<[^>]+>/g, "").slice(0, 160).trim() + "…";
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", {
    day:   "numeric",
    month: "long",
    year:  "numeric",
  });
}

// ─────────────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-20 sm:py-24"
      style={{
        background: [
          "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(22,163,74,0.12) 0%, transparent 70%)",
          "#0f172a",
        ].join(", "),
      }}
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-brand-400">
          From the team
        </p>
        <h1 className="mb-4 text-4xl font-bold text-white sm:text-5xl">
          SusDevOS Blog
        </h1>
        <p className="mx-auto max-w-xl text-lg text-surface-400">
          Practical guides on GHG reporting, carbon credit validation, restoration MRV, TNFD biodiversity disclosure,
          and what the standards actually require — without the jargon.
        </p>
        <div className="mt-6 flex justify-center">
          <a
            href="/rss.xml"
            className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-surface-400 transition-colors hover:border-white/20 hover:text-white"
          >
            <svg className="h-3 w-3 text-orange-400" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19.01 7.38 20 6.18 20 4.98 20 4 19.01 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1z"/>
            </svg>
            RSS feed
          </a>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

export default async function BlogListPage() {
  const posts = await getPosts();

  return (
    <>
      <Hero />

      <section className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          {posts.length === 0 ? (
            <div className="py-20 text-center">
              <p className="text-surface-400 text-sm">No posts yet — check back soon.</p>
            </div>
          ) : (
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {posts.map((post) => (
                <Link
                  key={post.BlogId}
                  href={`/blog/${post.Slug}`}
                  className="group flex flex-col rounded-2xl border border-surface-200 bg-white p-7 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
                >
                  {/* Meta */}
                  <div className="mb-4 flex items-center gap-3 text-xs text-surface-400">
                    {post.PublishedAt && (
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(post.PublishedAt)}
                      </span>
                    )}
                    <span>{readingTime(post.PostBody)} min read</span>
                  </div>

                  {/* Title */}
                  <h2 className="mb-3 text-lg font-bold leading-snug text-surface-900 group-hover:text-brand-700 transition-colors">
                    {post.SeoTitle ?? post.Title}
                  </h2>

                  {/* Excerpt */}
                  <p className="mb-5 flex-1 text-sm leading-relaxed text-surface-500">
                    {excerpt(post)}
                  </p>

                  {/* CTA */}
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 group-hover:gap-2.5 transition-all">
                    Read article <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Newsletter / CTA */}
      <section className="border-t border-surface-100 bg-surface-50 py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-xl text-center">
            <h3 className="mb-2 text-xl font-bold text-surface-900">
              Stay up to date
            </h3>
            <p className="mb-6 text-sm text-surface-500">
              New articles on GHG reporting, Verra/Gold Standard, TNFD and sustainable development —
              straight to your inbox.
            </p>
            <form className="flex gap-2">
              <input
                type="email"
                placeholder="you@company.com"
                className="flex-1 rounded-lg border border-surface-200 bg-white px-4 py-2.5 text-sm text-surface-900 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <button
                type="submit"
                className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
              >
                Subscribe
              </button>
            </form>
            <p className="mt-3 text-xs text-surface-400">No spam. Unsubscribe any time.</p>
          </div>
        </div>
      </section>
    </>
  );
}
